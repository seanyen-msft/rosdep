#!/usr/bin/env python

# Author Stuart Schaefere/stuart@theschaefers.com

import subprocess
import json
import sys
import traceback

from rospkg.os_detect import OS_WINDOWS, OsDetect

from ..core import InstallFailed, RosdepInternalError, InvalidData
from .pip import PIP_INSTALLER
from .source import SOURCE_INSTALLER
from ..installers import PackageManagerInstaller
from ..shell_utils import read_stdout

NUGET_INSTALLER = 'nuget'
CHOCO_INSTALLER = 'chocolatey'


def register_installers(context):
    context.set_installer(CHOCO_INSTALLER, ChocolateyInstaller())


def register_platforms(context):
    context.add_os_installer_key(OS_WINDOWS, CHOCO_INSTALLER)
    context.add_os_installer_key(OS_WINDOWS, PIP_INSTALLER)
    context.add_os_installer_key(OS_WINDOWS, SOURCE_INSTALLER)
    context.set_default_os_installer_key(OS_WINDOWS, lambda self: CHOCO_INSTALLER)
    context.set_os_version_type(OS_WINDOWS, OsDetect.get_codename)


def is_choco_installed():
    if "not-found" not in get_choco_version():
        return True
    else:
        return False


def get_choco_version():
    try:
        p = subprocess.Popen(
            ['powershell', 'choco'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        # If choco is not installed, we get a PS general failure
        if "not recognized" not in stdout:
            version = stdout.replace('Chocolatey v', '').strip()
            return version
        else:
            return 'Chocolatey not-found'
    except OSError:
        return 'Chocolatey not-found'


def choco_detect(pkgs, exec_fn=None):
    """
    Given a list of package, return the list of installed packages.

    :param exec_fn: function to execute Popen and read stdout (for testing)
    """
    ret_list = []
    if not is_choco_installed():
        return ret_list
    if exec_fn is None:
        exec_fn = read_stdout
    pkg_list = exec_fn(['powershell', 'choco', 'list', '--localonly']).split('\r\n')
    pkg_list.pop()
    pkg_list.pop()

    ret_list = []
    for pkg in pkg_list:
        pkg_row = pkg.split(' ')
        if pkg_row[0] in pkgs:
            ret_list.append(pkg_row[0])
    return ret_list


class ChocolateyInstaller(PackageManagerInstaller):

    def __init__(self):
        super(ChocolateyInstaller, self).__init__(choco_detect, supports_depends=True)

    def get_version_strings(self):
        version_strings = [
            get_choco_version()
        ]
        return version_strings

    def get_install_command(self, resolved, interactive=True, reinstall=False, quiet=False):
        if not is_choco_installed():
            raise InstallFailed((CHOCO_INSTALLER, "Chocolatey is not installed"))
        # convenience function that calls outs to our detect function
        packages = self.get_packages_to_install(resolved, reinstall=reinstall)
        if not packages:
            return []
        else:
            return [['powershell', 'choco', 'install', p] for p in packages]
