# -*- coding: utf-8 -*-
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

import os
import traceback

from mock import call
from mock import Mock
from mock import patch


def get_test_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'vcpkg'))


def test_auto_detected_triplet():
    from rosdep2.platforms.vcpkg import auto_detected_triplet
    triplet = auto_detected_triplet()
    # make sure it is in commonly seen triplets.
    assert triplet in ['x64-windows', 'x64-linux', 'x64-osx', 'x86-windows', 'x86-linux', 'x86-osx'], triplet


def test_vcpkg_installed():
    # don't know the correct answer, but make sure this does not throw
    from rosdep2.platforms.vcpkg import is_vcpkg_installed
    assert is_vcpkg_installed() in [True, False]


def vcpkg_command(command):
    if command[1] == 'list':
        with open(os.path.join(get_test_dir(), 'vcpkg-list-output'), 'r') as f:
            return f.read()
    return ''


@patch('rosdep2.platforms.vcpkg.auto_detected_triplet')
@patch('rosdep2.platforms.vcpkg.is_vcpkg_installed')
def test_vcpkg_detect(mock_vcpkg_installed, mock_vcpkg_triplet):
    mock_vcpkg_installed.return_value = True
    mock_vcpkg_triplet.return_value = 'x64-windows'

    from rosdep2.platforms.vcpkg import vcpkg_detect

    m = Mock()
    m.return_value = ''
    val = vcpkg_detect([], exec_fn=m)
    assert val == [], val

    m = Mock()
    m.return_value = ''
    val = vcpkg_detect(['tinyxml'], exec_fn=m)
    assert val == [], val
    # make sure our test harness is based on the same implementation
    m.assert_called_with(['vcpkg', 'list'])

    m = Mock()
    m.side_effect = vcpkg_command
    val = vcpkg_detect(['sqlite3', 'zlib', 'python', 'bazaar'], exec_fn=m)
    expected = ['sqlite3', 'zlib']
    assert set(val) == set(expected), val
    assert val == expected, val
    assert len(val) == len(set(val)), val


def test_VcpkgInstaller():
    from rosdep2.platforms.vcpkg import VcpkgInstaller

    @patch('rosdep2.platforms.vcpkg.auto_detected_triplet')
    @patch('rosdep2.platforms.vcpkg.is_vcpkg_installed')
    @patch.object(VcpkgInstaller, 'get_packages_to_install')
    def test(mock_get_packages_to_install, mock_vcpkg_installed, mock_vcpkg_triplet):
        mock_vcpkg_installed.return_value = True
        mock_vcpkg_triplet.return_value = 'machine-os'

        installer = VcpkgInstaller()
        mock_get_packages_to_install.return_value = []
        assert [] == installer.get_install_command(['fake'])

        mock_get_packages_to_install.return_value = ['subversion', 'bazaar']
        expected = [['vcpkg', 'install', 'subversion', '--triplet', 'machine-os'],
                    ['vcpkg', 'install', 'bazaar', '--triplet', 'machine-os']]
        # Vcpkg can be interactive
        for interactive in [True, False]:
            val = installer.get_install_command(['whatever'], interactive=interactive)
            assert val == expected, val

        expected = [['vcpkg', 'install', 'subversion', '--triplet', 'machine-os'],
                    ['vcpkg', 'install', 'bazaar', '--triplet', 'machine-os']]
        val = installer.get_install_command(['whatever'], reinstall=True)
        assert val == expected, val
    try:
        test()
    except AssertionError:
        traceback.print_exc()
        raise
