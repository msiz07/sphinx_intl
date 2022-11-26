import io
import re

import pytest

from babel.messages import pofile
from sphinx_intl import catalog


def test_read_pot_bytesio(line_wrap_pot_bytesio):
    cat = catalog._read_po_stream(line_wrap_pot_bytesio, "utf-8")

    included_msgid = "".join([
        line.replace('"', "") for line in line_wrap_pofile_msgid.split("\n")
    ])
    # included_msgid = (
    #     "If you want your children to be intelligent, read them fairy "
    #     "tales. If you want them to be more intelligent, read them more "
    #     "fairy tales."
    # )
    assert included_msgid in [msg.id for msg in cat]


def test_read_po_ja_bytesio(line_wrap_po_ja_bytesio):
    cat = catalog._read_po_stream(line_wrap_po_ja_bytesio, "utf-8")

    included_msgid = "".join([
        line.replace('"', "") for line in line_wrap_pofile_msgid.split("\n")
    ])
    # included_msgid = (
    #     "If you want your children to be intelligent, read them fairy "
    #     "tales. If you want them to be more intelligent, read them more "
    #     "fairy tales."
    # )
    assert included_msgid in [msg.id for msg in cat]

    msg = cat.get(included_msgid)
    assert msg.string == pofile.denormalize(line_wrap_pofile_msgtr), (
        "##### msg.string #####:\n"
        f"{msg.string}\n\n"
        "##### line_wrap_pofile_msgstr #####:\n"
        f"{pofile.denormalize(line_wrap_pofile_msgtr)}"
    )
    assert isinstance(msg, catalog.SphinxIntlMessage), (
        f"type(msg): {type(msg)}"
    )


def test_update_catalog(
    line_wrap_updated_pot_bytesio, line_wrap_po_ja_bytesio
):
    cat_updated_pot = pofile.read_po(line_wrap_updated_pot_bytesio)
    cat_po_ja = pofile.read_po(line_wrap_po_ja_bytesio)

    cat_po_ja.update(cat_updated_pot)

    expected_msgid = "".join([
        line.replace('"', "").replace(".", "!")
        for line in line_wrap_pofile_msgid.split("\n")
    ])
    expected_previous_msgid = "".join([
        line.replace('"', "") for line in line_wrap_pofile_msgid.split("\n")
    ])
    print(f"expected_msgid: {expected_msgid}")
    print(f"expected_previous_msgid: {expected_previous_msgid}")
    msgid_list = [msg.id for msg in cat_po_ja]
    prev_msgid_list = [
        msg.previous_id[0] for msg in cat_po_ja if len(msg.previous_id) > 0
    ]
    assert expected_msgid in msgid_list
    assert expected_msgid not in prev_msgid_list
    assert expected_previous_msgid not in msgid_list
    assert expected_previous_msgid in prev_msgid_list


def test_read_write_pofile_without_change(line_wrap_po_ja_bytesio):
    orig_pofile_bytes = line_wrap_po_ja_bytesio.getvalue()

    cat = catalog._read_po_stream(line_wrap_po_ja_bytesio, "utf-8")

    tmp_bytesio = io.BytesIO()
    catalog._write_po_stream(tmp_bytesio, cat)
    written_pofile_bytes = tmp_bytesio.getvalue()

    assert (
        orig_pofile_bytes.decode("utf-8") ==
        written_pofile_bytes.decode("utf-8")
    ), (
        "\n***** orig_pofile *****:\n"
        f"{orig_pofile_bytes.decode('utf-8')}"
        "\n--------------------------------------------------\n"
        "\n***** written_pofile *****:\n"
        f"{written_pofile_bytes.decode('utf-8')}"
        "\n--------------------------------------------------\n"
    )


def test_keep_po_format_string(line_wrap_po_ja_bytesio):
    cat_po_ja = catalog._read_po_stream(line_wrap_po_ja_bytesio, "utf-8")

    included_msgid = "".join([
        line.replace('"', "") for line in line_wrap_pofile_msgid.split("\n")
    ])
    assert included_msgid in [msg.id for msg in cat_po_ja]

    msg = cat_po_ja.get(included_msgid)
    assert isinstance(msg, catalog.SphinxIntlMessage), (
        f"type(msg): {type(msg)}"
    )
    assert msg.get_po_format_translation() == (
        '""\n' + line_wrap_pofile_msgtr
    ).strip(), (
        "##### msg.po_format_translation() #####\n"
        f"{msg.get_po_format_translation()}\n"
        "##### line_wrap_pofile_msgstr #####\n"
        f'""\n{line_wrap_pofile_msgtr}'
    )


def test_write_updated_catalog(
    line_wrap_updated_pot_bytesio, line_wrap_po_ja_bytesio
):
    cat_updated_pot = catalog._read_po_stream(
        line_wrap_updated_pot_bytesio, "utf-8"
    )
    cat_po_ja = catalog._read_po_stream(line_wrap_po_ja_bytesio, "utf-8")

    catalog.update_with_fuzzy(cat_po_ja, cat_updated_pot)

    po_bout = io.BytesIO()
    catalog._write_po_stream(po_bout, cat_po_ja)
    updated_po = po_bout.getvalue().decode("utf-8")

    expected_msg_entry = (
        'msgid ""\n'
        '{0}\n'
        'msgstr ""\n'
        '{1}\n'
        '\n'
    ).format(
        line_wrap_pofile_msgid.replace(".", "!").strip(),
        line_wrap_pofile_msgtr.strip(),
    )

    assert (
        re.search(expected_msg_entry, updated_po, flags=re.MULTILINE)
    ), (
        "\n***** expected_msg_entry *****:\n"
        f"{expected_msg_entry}"
        "\n--------------------------------------------------\n"
        "\n***** updated_po *****:\n"
        f"{updated_po}"
        "\n--------------------------------------------------\n"
    )


@pytest.fixture(scope="function")
def line_wrap_pot_bytesio():
    bytes_io = io.BytesIO()
    bytes_io.write(
        line_wrap_pot.format(line_wrap_pofile_msgid, "").encode("utf-8")
    )
    bytes_io.seek(0)
    return bytes_io


@pytest.fixture(scope="function")
def line_wrap_updated_pot_bytesio():
    bytes_io = io.BytesIO()
    bytes_io.write(
        line_wrap_pot.format(
            line_wrap_pofile_msgid.replace(".", "!"), ""
        ).encode("utf-8")
    )
    bytes_io.seek(0)
    return bytes_io


@pytest.fixture(scope="function")
def line_wrap_po_ja_bytesio():
    bytes_io = io.BytesIO()
    bytes_io.write(
        line_wrap_pot.format(
            line_wrap_pofile_msgid.strip(), line_wrap_pofile_msgtr.strip()
        ).encode("utf-8")
    )
    bytes_io.seek(0)
    return bytes_io


line_wrap_pofile_msgid = """\
"If you want your children to be intelligent, read them fairy tales. If "
"you want them to be more intelligent, read them more fairy tales."
"""

line_wrap_pofile_msgtr = """\
"もしも自分の子供に賢くなってほしかったら、おとぎ話を読んであげましょう。"
"もしももっと賢くなってほしかったら、もっとおとぎ話を読んであげましょう。"
"""

line_wrap_pot = r"""# Japanese translations for PROJECT.
# Copyright (C) 2022 ORGANIZATION
# This file is distributed under the same license as the PROJECT project.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2022.
#
msgid ""
msgstr ""
"Project-Id-Version: PROJECT VERSION\n"
"Report-Msgid-Bugs-To: EMAIL@ADDRESS\n"
"POT-Creation-Date: 2022-11-03 21:39+0900\n"
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

#: line_wrap_message.txt:1 line_wrap_message.txt:5
msgid ""
{0}
msgstr ""
{1}

#: file1:4 file1:5 file2:6
msgid ""
"last entry.\n"
"The quick brown fox jumped over the lazy dogs. 1234567890."
msgstr ""
"最後のエントリー。\n"
"素早い茶色の狐はのろまな犬どもを飛び越えた。１２３４５６７８９０。"
"""
