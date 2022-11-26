import io
import os

from click.testing import CliRunner
from babel.messages import pofile
import pytest

from sphinx_intl import catalog
from sphinx_intl import commands

runner = CliRunner()

def test_update_command_keep_project_field1(po_changed_pot_files):
    temp_dir, po_ja_filename, pot_filename = po_changed_pot_files

    cmd_result = runner.invoke(
        commands.update, ["-d", "locale", "-p", "_build/locale", "-l", "ja"]
    )
    assert cmd_result.exit_code == 0
    cat_po = pofile.read_po(open(po_ja_filename, "rb"))
    cat_pot = pofile.read_po(open(pot_filename, "rb"))
    assert cat_po.project != cat_pot.project
    assert cat_po.version != cat_pot.version


def test_update_command_keep_project_field2(po_unchanged_pot_files):
    temp_dir, po_ja_filename, pot_filename = po_unchanged_pot_files

    cmd_result = runner.invoke(
        commands.update, ["-d", "locale", "-p", "_build/locale", "-l", "ja"]
    )
    assert cmd_result.exit_code == 0
    cat_po = pofile.read_po(open(po_ja_filename, "rb"))
    cat_pot = pofile.read_po(open(pot_filename, "rb"))
    assert cat_po.project != cat_pot.project
    assert cat_po.version != cat_pot.version


def test_update_command_update_project_field1(po_changed_pot_files):
    temp_dir, po_ja_filename, pot_filename = po_changed_pot_files

    cmd_result = runner.invoke(
        commands.update,
        ["-d", "locale", "-p", "_build/locale", "-l", "ja", "-up"]
    )
    assert cmd_result.exit_code == 0
    cat_po = pofile.read_po(open(po_ja_filename, "rb"))
    cat_pot = pofile.read_po(open(pot_filename, "rb"))
    assert cat_po.project == cat_pot.project
    assert cat_po.version == cat_pot.version

def test_update_command_update_project_field2(po_unchanged_pot_files):
    temp_dir, po_ja_filename, pot_filename = po_unchanged_pot_files

    cmd_result = runner.invoke(
        commands.update,
        ["-d", "locale", "-p", "_build/locale", "-l", "ja", "-up"]
    )
    assert cmd_result.exit_code == 0
    cat_po = pofile.read_po(open(po_ja_filename, "rb"))
    cat_pot = pofile.read_po(open(pot_filename, "rb"))
    assert cat_po.project == cat_pot.project
    assert cat_po.version == cat_pot.version


def _write_po_files(base_dir, po_basename, po_bytes, pot_bytes):
    po_ja_filename = os.path.join(
        base_dir, "locale", "ja", "LC_MESSAGES", f"{po_basename}.po"
    )
    pot_filename = os.path.join(
        base_dir, "_build", "locale", f"{po_basename}.pot"
    )
    for dir_ in [po_ja_filename, pot_filename]:
        if not os.path.exists(os.path.dirname(dir_)):
            os.makedirs(os.path.dirname(dir_))

    with open(po_ja_filename, "bw") as f:
        f.write(po_bytes)
    with open(pot_filename, "bw") as f:
        f.write(pot_bytes)

    return po_ja_filename, pot_filename


@pytest.fixture(scope="function")
def po_changed_pot_files(temp):
    # assert temp == os.getcwd()
    po_basename = "test_file"
    po_ja_filename, pot_filename = _write_po_files(
        temp,
        po_basename,
        project_id1_po.encode("utf-8"),
        project_id2_pot.encode("utf-8"),
    )

    yield temp, po_ja_filename, pot_filename

    for fname in [po_ja_filename, pot_filename]:
        if os.path.exists(po_ja_filename):
            os.remove(fname)

@pytest.fixture(scope="function")
def po_unchanged_pot_files(temp):
    # assert temp == os.getcwd()
    po_basename = "test_file"
    po_ja_filename, pot_filename = _write_po_files(
        temp,
        po_basename,
        project_id1_po.encode("utf-8"),
        project_id2_messaes_unchanged_pot.encode("utf-8"),
    )

    yield temp, po_ja_filename, pot_filename

    for fname in [po_ja_filename, pot_filename]:
        if os.path.exists(po_ja_filename):
            os.remove(fname)

@pytest.fixture(scope="function")
def id1_po_bytesio():
    bytes_io = io.BytesIO()
    bytes_io.write(project_id1_po.encode("utf-8"))
    bytes_io.seek(0)
    return bytes_io


@pytest.fixture(scope="function")
def id2_pot_bytesio():
    bytes_io = io.BytesIO()
    bytes_io.write(project_id2_pot.encode("utf-8"))
    bytes_io.seek(0)
    return bytes_io


project_id1_po = r"""
# Japanese translations for PROJECT.
# Copyright (C) 2022 ORGANIZATION
# This file is distributed under the same license as the PROJECT project.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2022.
#
msgid ""
msgstr ""
"Project-Id-Version: ID1 1.0\n"
"Report-Msgid-Bugs-To: EMAIL@ADDRESS\n"
"POT-Creation-Date: 2022-11-23 19:00+0900\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language: ja\n"
"Language-Team: ja <LL@li.org>\n"
"Plural-Forms: nplurals=1; plural=0;\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel 2.11.0\n"

#: file1:1 file1:2 file2:3
msgid ""
"first entry.\n"
"The quick brown fox jumps over lazy dog."
msgstr ""
"最初のエントリー。\n"
"素早い茶色の狐はのろまな犬を飛び越える。"

#: file1:4 file1:5 file2:6
msgid ""
"last entry.\n"
"The quick brown fox jumped over the lazy dogs. 1234567890."
msgstr ""
"最後のエントリー。\n"
"素早い茶色の狐はのろまな犬どもを飛び越えた。１２３４５６７８９０。"
"""

project_id2_pot = r"""
# Japanese translations for PROJECT.
# Copyright (C) 2022 ORGANIZATION
# This file is distributed under the same license as the PROJECT project.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2022.
#
msgid ""
msgstr ""
"Project-Id-Version: ID2 2.0\n"
"Report-Msgid-Bugs-To: EMAIL@ADDRESS\n"
"POT-Creation-Date: 2022-11-23 20:00+0900\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language: ja\n"
"Language-Team: ja <LL@li.org>\n"
"Plural-Forms: nplurals=1; plural=0;\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel 2.11.0\n"

#: file1:1 file1:2 file2:3
msgid ""
"# FIRST ENTRY\n"
"The quick brown fox jumps over lazy dog."
msgstr ""

#: file1:4 file1:5 file2:6
msgid ""
"# LAST ENTRY\n"
"The quick brown fox jumped over the lazy dogs. 1234567890."
msgstr ""
"""

project_id2_messaes_unchanged_pot = r"""
# Japanese translations for PROJECT.
# Copyright (C) 2022 ORGANIZATION
# This file is distributed under the same license as the PROJECT project.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2022.
#
msgid ""
msgstr ""
"Project-Id-Version: ID2 2.0\n"
"Report-Msgid-Bugs-To: EMAIL@ADDRESS\n"
"POT-Creation-Date: 2022-11-23 20:00+0900\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language: ja\n"
"Language-Team: ja <LL@li.org>\n"
"Plural-Forms: nplurals=1; plural=0;\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: Babel 2.11.0\n"

#: file1:1 file1:2 file2:3
msgid ""
"first entry.\n"
"The quick brown fox jumps over lazy dog."
msgstr ""

#: file1:4 file1:5 file2:6
msgid ""
"last entry.\n"
"The quick brown fox jumped over the lazy dogs. 1234567890."
msgstr ""
"""
