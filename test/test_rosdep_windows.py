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
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'windows'))


def test_choco_installed():
    # don't know the correct answer, but make sure this does not throw
    from rosdep2.platforms.windows import is_choco_installed
    assert is_choco_installed() in [True, False]


def choco_command(command):
    if command[1] == 'list':
        with open(os.path.join(get_test_dir(), 'choco-list-output'), 'r') as f:
            return f.read()
    return ''


def test_choco_detect():
    from rosdep2.platforms.windows import choco_detect

    m = Mock()
    m.return_value = ''
    val = choco_detect([], exec_fn=m)
    assert val == [], val

    m = Mock()
    m.return_value = ''
    val = choco_detect(['tinyxml'], exec_fn=m)
    assert val == [], val
    # make sure our test harness is based on the same implementation
    m.assert_called_with(['choco', 'list', '-lo', '-r'])
    assert m.call_args_list == [call(['choco', 'list', '-lo', '-r'])], m.call_args_list

    m = Mock()
    m.side_effect = choco_command
    val = choco_detect(['apt', 'subversion', 'python', 'bazaar'], exec_fn=m)
    # make sure it preserves order
    expected = ['subversion', 'bazaar']
    assert set(val) == set(expected), val
    assert val == expected, val
    assert len(val) == len(set(val)), val


def test_ChocolateyInstaller():
    from rosdep2.platforms.windows import ChocolateyInstaller

    @patch('rosdep2.platforms.windows.is_choco_installed')
    @patch.object(ChocolateyInstaller, 'get_packages_to_install')
    def test(mock_get_packages_to_install, mock_choco_installed):
        mock_choco_installed.return_value = True

        installer = ChocolateyInstaller()
        mock_get_packages_to_install.return_value = []
        assert [] == installer.get_install_command(['fake'])

        mock_get_packages_to_install.return_value = ['subversion', 'bazaar']
        expected = [['choco', 'upgrade', '-y', 'subversion'],
                    ['choco', 'upgrade', '-y', 'bazaar']]
        # Chocolatey can be interactive
        for interactive in [True, False]:
            val = installer.get_install_command(['whatever'], interactive=interactive)
            assert val == expected, val

        expected = [['choco', 'uninstall', '--force', '-y', 'subversion'],
                    ['choco', 'install', '-y', 'subversion'],
                    ['choco', 'uninstall', '--force', '-y', 'bazaar'],
                    ['choco', 'install', '-y', 'bazaar']]
        val = installer.get_install_command(['whatever'], reinstall=True)
        assert val == expected, val
    try:
        test()
    except AssertionError:
        traceback.print_exc()
        raise
