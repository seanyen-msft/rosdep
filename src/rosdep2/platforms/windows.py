# Copyright (c) Microsoft Corporation. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess
import json
import sys
import traceback

from rospkg.os_detect import OS_WINDOWS, OsDetect

from ..core import InstallFailed, RosdepInternalError, InvalidData
from .pip import PIP_INSTALLER
from .source import SOURCE_INSTALLER
from .vcpkg import VCPKG_INSTALLER
from ..installers import PackageManagerInstaller
from ..shell_utils import read_stdout

CHOCO_INSTALLER = 'chocolatey'


def register_installers(context):
    context.set_installer(CHOCO_INSTALLER, ChocolateyInstaller())


def register_platforms(context):
    context.add_os_installer_key(OS_WINDOWS, CHOCO_INSTALLER)
    context.add_os_installer_key(OS_WINDOWS, PIP_INSTALLER)
    context.add_os_installer_key(OS_WINDOWS, VCPKG_INSTALLER)
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
            ['choco', '--version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout, _ = p.communicate()
        if p.returncode == 0:
            version = stdout.decode('utf8').strip()
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
    pkg_list = exec_fn(['choco', 'list', '-lo', '-r']).splitlines()

    ret_list = []
    for pkg in pkg_list:
        pkg_row = pkg.split('|')
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

        # interactive switch doesn't matter
        if reinstall:
            # previous we explicitly uninstall and install packages, however
            # we noticed there are some problematic code path inside packages'
            # uninstall scripts.
            # so here we workaround that by only doing force upgrade, and we
            # should revisit this after we figure out the root cause of the
            # uninstall scripts.
            return [['choco', 'upgrade', '-f', '-y', p] for p in packages]
        else:
            return [['choco', 'upgrade', '-y', p] for p in packages]
