# -*- coding: utf-8 -*-
"""
    test_commands
    ~~~~~~~~~~~~~

    Test all commands that have no special checks.

    :copyright: Copyright 2013 by Takayuki SHIMIZUKAWA.
    :license: BSD, see LICENSE for details.
"""
from __future__ import with_statement

from click.testing import CliRunner

from sphinx_intl import commands

from utils import in_tmp

runner = CliRunner()


@in_tmp()
def test_update_pot_notfound(temp):
    r1 = runner.invoke(commands.update, ['-d', 'locale'])
    assert r1.exit_code != 0
    assert 'Please specify pot directory with -p option,' in r1.output


@in_tmp()
def test_update_no_language(temp):
    r1 = runner.invoke(commands.update, ['-d', 'locale', '-p', '_build/locale'])
    assert r1.exit_code != 0
    assert 'No languages are found. Please specify language with -l' in r1.output


@in_tmp()
def test_update_simple(temp):
    r1 = runner.invoke(commands.update, ['-d', 'locale', '-p', '_build/locale', '-l', 'ja'])
    assert r1.exit_code == 0


@in_tmp()
def test_update_difference_detect(temp):
    r1 = runner.invoke(commands.update, ['-d', 'locale', '-p', '_build/locale', '-l', 'ja'])
    assert r1.exit_code == 0
    assert r1.output.count('Create:') == 1
    assert r1.output.count('Update:') == 0
    assert r1.output.count('Not Changed:') == 0

    with open('_build/locale/README.pot', 'a') as f:
        f.write('\nmsgid "test1"\nmsgstr ""\n')

    r2 = runner.invoke(commands.update, ['-d', 'locale', '-p', '_build/locale'])
    assert r2.exit_code == 0
    assert r2.output.count('Create:') == 0
    assert r2.output.count('Update:') == 1
    assert r2.output.count('Not Changed:') == 0

    with open('_build/locale/README.pot', 'r') as f:
        d = f.read()
        d = d.replace('test1', 'test2')
    with open('_build/locale/README.pot', 'w') as f:
        f.write(d)

    r3 = runner.invoke(commands.update, ['-d', 'locale', '-p', '_build/locale'])
    assert r3.exit_code == 0
    assert r3.output.count('Create:') == 0
    assert r3.output.count('Update:') == 1
    assert r3.output.count('Not Changed:') == 0

    r4 = runner.invoke(commands.update, ['-d', 'locale', '-p', '_build/locale'])
    assert r4.exit_code == 0
    assert r4.output.count('Create:') == 0
    assert r4.output.count('Update:') == 0
    assert r4.output.count('Not Changed:') == 1


@in_tmp()
def test_stat(temp):
    r1 = runner.invoke(commands.update, ['-d', 'locale', '-p', '_build/locale', '-l', 'ja'])
    assert r1.exit_code == 0

    r2 = runner.invoke(commands.stat, ['-d', 'locale'])
    assert r2.exit_code == 0
    assert 'README.po: 0 translated, 0 fuzzy, 1 untranslated.' in r2.output


@in_tmp()
def test_stat_with_multiple_languages(temp):
    r1 = runner.invoke(commands.update, ['-d', 'locale', '-p', '_build/locale', '-l', 'ja,de,it'])
    assert r1.exit_code == 0

    # r2 = runner.invoke(commands.stat, ['-d', 'locale', '-l', 'ja,de', '-l', 'it'])
    r2 = runner.invoke(commands.stat, ['-d', 'locale', '-l', 'ja'])
    assert r2.exit_code == 0
    assert 'README.po: 0 translated, 0 fuzzy, 1 untranslated.' in r2.output


@in_tmp()
def test_build(temp):
    result = runner.invoke(commands.build, ['--locale-dir', 'locale'])
    assert result.exit_code == 0
