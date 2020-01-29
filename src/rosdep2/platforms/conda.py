# Copyright 2019 Open Source Robotics Foundation, Inc.
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
from rospkg.os_detect import OS_WINDOWS, OsDetect
from ..installers import PackageManagerInstaller
CONDA_INSTALLER = 'conda'


def register_installers(context):
    context.set_installer(CONDA_INSTALLER, CondaInstaller())


def register_platforms(context):
    context.add_os_installer_key('conda', CONDA_INSTALLER)
    context.set_default_os_installer_key('conda', lambda self: CONDA_INSTALLER)
    context.set_os_version_type('conda', OsDetect.get_codename)


def conda_detect(pkgs, exec_fn=None):
    """
    Given a list of package, return the list of installed packages.
    NOTE: These are stubs currently and will be filled after semantics are fully defined.

    :param pkgs: list of package names, optionally followed by a fixed version (`foo=3.0`)
    :param exec_fn: function to execute Popen and read stdout (for testing)
    :return: list elements in *pkgs* that were found installed on the system
    """
    raise NotImplementedError("conda_detect is not implemented yet")


class CondaInstaller(PackageManagerInstaller):
    """
    An implementation of the Installer for use on oe systems.
    NOTE: These are stubs currently and will be filled after semantics are fully defined.
    """

    def __init__(self):
        super(CondaInstaller, self).__init__(conda_detect)

    def get_version_strings(self):
        output = subprocess.check_output(['conda', '--version'])
        version = output.splitlines()[0].split(' ')[1]
        return [('conda {}').format(version)]

    def get_install_command(self, resolved, interactive=True, reinstall=False, quiet=False):
        raise NotImplementedError('get_install_command is not implemented yet')
