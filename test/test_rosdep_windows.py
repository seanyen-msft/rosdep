# -*- coding: utf-8 -*-

# Author Stuart Schaefer/stuart@theschaefers.com

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
    elif command[1] == 'info':
        pkg = command[2]
        with open(os.path.join(get_test_dir(), 'choco-info-output'), 'r') as f:
            output = f.readlines()
        for line in output:
            res = line.split(':', 1)
            if res[0] == pkg:
                return res[1]
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
    m.assert_called_with(['choco', 'list'])
    assert m.call_args_list == [call(['choco, 'list'])], m.call_args_list

    m = Mock()
    m.side_effect = choco_command
    val = choco_detect((['apt', 'subversion', 'python', 'bazaar'], exec_fn=m)
    # make sure it preserves order
    expected = ['subversion', 'bazaar']
    assert set(val) == set(expected), val
    assert val == expected, val
    assert len(val) == len(set(val)), val


def test_ChocolateyInstaller():
    from rosdep2.platforms.windows import ChocolateyInstaller

    @patch('rosdep2.platforms.windows.is_choco_installed')
    @patch.object(ChocolateyInstaller, 'remove_duplicate_dependencies')
    @patch.object(ChocolateyInstaller, 'get_packages_to_install')
    def test(mock_get_packages_to_install, mock_remove_duplicate_dependencies, mock_choco_installed):
        mock_choco_installed.return_value = True

        installer = ChocolateyInstaller()
        mock_get_packages_to_install.return_value = []
        mock_remove_duplicate_dependencies.return_value = mock_get_packages_to_install.return_value
        assert [] == installer.get_install_command(make_resolutions(['fake']))

        mock_get_packages_to_install.return_value = make_resolutions(['subversion', 'bazaar'])
        mock_remove_duplicate_dependencies.return_value = mock_get_packages_to_install.return_value
        expected = [['powershell', 'choco', 'install', 'subversion'],
                    ['powershell', 'choco', 'install', 'bazaar']]
        # Chocolatey can be interactive
        for interactive in [True, False]:
            val = installer.get_install_command(['whatever'], interactive=interactive)
            assert val == expected, val

        expected = [['powershell', 'choco', 'uninstall', '--force', 'subversion'],
                    ['powershell', 'choco', 'install', 'subversion'],
                    ['powershell', 'choco', 'uninstall', '--force', 'bazaar'],
                    ['powershell', 'choco', 'install', 'bazaar']]
        val = installer.get_install_command(['whatever'], reinstall=True)
        assert val == expected, val

        mock_get_packages_to_install.return_value = make_resolutions_options(
            [('subversion', ['foo', 'bar'], ['baz']), ('bazaar', [], ['--with-quux'])])
        mock_remove_duplicate_dependencies.return_value = mock_get_packages_to_install.return_value
        expected = [['powershell', 'choco', 'install', 'subversion', 'foo', 'bar', 'baz'],
                    ['powershell', 'choco', 'install', 'bazaar', '--with-quux']]
        val = installer.get_install_command(['whatever'])
        assert val == expected, val

        try:
            mock_get_packages_to_install.return_value = eval("make_resolutions_options([('subversion', [u'f´´ßß', u'öäö'], []), (u'bazaar', [], [u'tüü'])])")
        except SyntaxError:
            # Python 3.2, u'...' is not allowed, but string literals are unicode
            mock_get_packages_to_install.return_value = make_resolutions_options(
                [('subversion', ['f´´ßß', 'öäö'], []), ('bazaar', [], ['tüü'])])
        mock_remove_duplicate_dependencies.return_value = mock_get_packages_to_install.return_value
        try:
            expected = eval("[['powershell', 'choco', 'install', 'subversion', u'f´´ßß', u'öäö'], ['brew', 'install', 'bazaar', u'tüü']]")
        except SyntaxError:
            # Python 3.2, u'...' is not allowed, but string literals are unicode
            expected = [['powershell', 'choco', 'install', 'subversion', 'f´´ßß', 'öäö'],
                        ['powershell', 'choco', 'install', 'bazaar', 'tüü']]
        val = installer.get_install_command(['whatever'])
        assert val == expected, val
    try:
        test()
    except AssertionError:
        traceback.print_exc()
        raise
