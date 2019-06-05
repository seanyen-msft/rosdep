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
import platform

from rospkg.os_detect import OsDetect, uname_get_machine

from ..core import InstallFailed, RosdepInternalError, InvalidData
from ..installers import PackageManagerInstaller
from ..shell_utils import read_stdout

VCPKG_INSTALLER = 'vcpkg'


def register_installers(context):
    context.set_installer(VCPKG_INSTALLER, VcpkgInstaller())


def auto_detected_triplet():
    machine_name = platform.machine().lower()
    os_name = OsDetect().get_name().lower()
    if machine_name in ['amd64', 'x86_64']:
        return 'x64-%s' % os_name
    elif machine_name in ['i386', 'i686']:
        return 'x86-%s' % os_name
    else:
        raise RosdepInternalError


def is_vcpkg_installed():
    if "not-found" not in get_vcpkg_version():
        return True
    else:
        return False


def get_vcpkg_version():
    try:
        p = subprocess.Popen(
            ['vcpkg', 'version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode == 0:
            version = stdout.decode('utf8').strip()
            if "Vcpkg package management program version" in version:
                version = version.replace('Vcpkg package management program version', '').strip()
                return version
        else:
            return 'vcpkg not-found'
    except OSError:
        return 'vcpkg not-found'


def vcpkg_detect(pkgs, exec_fn=None):
    """
    Given a list of package, return the list of installed packages.

    :param exec_fn: function to execute Popen and read stdout (for testing)
    """
    ret_list = []
    if not is_vcpkg_installed():
        return ret_list
    if exec_fn is None:
        exec_fn = read_stdout
    pkg_list = exec_fn(['vcpkg', 'list']).splitlines()

    ret_list = []
    for pkg in pkg_list:
        try:
            pkg_row = pkg.split(' ')
            pkg_tuple = pkg_row[0].split(':')
            if pkg_tuple[1] == auto_detected_triplet():
                if pkg_tuple[0] in pkgs:
                    ret_list.append(pkg_tuple[0])
        except IndexError:
            pass
    return ret_list


class VcpkgInstaller(PackageManagerInstaller):

    def __init__(self):
        super(VcpkgInstaller, self).__init__(vcpkg_detect, supports_depends=True)

    def get_version_strings(self):
        version_strings = [
            get_vcpkg_version()
        ]
        return version_strings

    def get_install_command(self, resolved, interactive=True, reinstall=False, quiet=False):
        if not is_vcpkg_installed():
            raise InstallFailed((VCPKG_INSTALLER, "Vcpkg is not installed"))
        # convenience function that calls outs to our detect function
        packages = self.get_packages_to_install(resolved, reinstall=reinstall)
        if not packages:
            return []

        return [['vcpkg', 'install', p, '--triplet', auto_detected_triplet()] for p in packages]
