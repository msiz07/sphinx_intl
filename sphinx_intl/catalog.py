# -*- coding: utf-8 -*-

import os
import io
import re
from copy import copy

from babel.messages import pofile, mofile, Message
from babel.messages.catalog import Catalog


class PoFileParseError(Exception):
    pass


class SphinxIntlMessage(Message):
    _po_format_translation: str = '""'

    def get_po_format_translation(self) -> str:
        return self._po_format_translation

    def set_po_format_translation(self, po_format_translation) -> None:
        self._po_format_translation = po_format_translation

    @classmethod
    def copy_from_babel_message(cls, message: Message):
        message_attrs = (
            message.id, message.string, message.locations, message.flags,
            message.auto_comments, message.user_comments, message.previous_id,
            message.lineno, message.context
        )
        return SphinxIntlMessage(*map(copy, message_attrs))


class SphinxIntlPoFileParser(pofile.PoFileParser):

    def _add_message(self):
        if len(self.messages) > 1:
            self._invalid_pofile(
                u"", self.offset,
                "message entry has more than 1 translation. "
                "sphinx_intl seems to assume message without plurals only."
            )
        msgid = self.messages[0].denormalize()
        # translated_string = self.translations[0][1].denormalize()
        po_format_translated_string = "\n".join(
            self.translations[0][1]._strs
        )
        is_obsolete = self.obsolete

        super()._add_message()

        orig_message = self.catalog[msgid]
        if not msgid:  # header entry has empty msgid
            return
        if is_obsolete:  # do not care line wrap for obsolete entries
            return
        if not orig_message:  # failed to add babel message to catalog?
            raise PoFileParseError(
                f"{msgid}: failed to add babel message to catalog?\n"
                f"orig_message: {orig_message}"
            )
        sphinx_intl_message = (
            SphinxIntlMessage.copy_from_babel_message(orig_message)
        )
        sphinx_intl_message.set_po_format_translation(
            po_format_translated_string
        )
        # babel catalog does not replace message instance by
        # catalog.__setitem__() when the message already exists.
        self.catalog.delete(msgid)
        self.catalog[msgid] = sphinx_intl_message


class SphinxIntlPoFileWriter:

    def __init__(self, catalog: Catalog, line_width: int = 76):
        self.catalog = catalog
        self.line_width = 76
        self._in_msgid = False
        self._in_msgstr = False
        self._cur_msgid = ""
        self._cur_msgid_po_lines = b""
        self._cur_msgstr = ""
        self._cur_msgstr_po_lines = b""

    def write_po(self, fileobj: io.BufferedIOBase) -> None:
        _babel_output_bytes = io.BytesIO()

        pofile.write_po(
            _babel_output_bytes,
            self.catalog,
            self.line_width,
            include_previous=True,
        )
        _babel_output_bytes.seek(0)
        _updated_output_bytes = self._update_to_line_wrapped_translations(
            _babel_output_bytes
        )
        _updated_output_bytes.seek(0)
        fileobj.write(_updated_output_bytes.read())

    def _update_to_line_wrapped_translations(
        self,
        babel_bytesio: io.BufferedIOBase,
    ) -> io.BufferedIOBase:
        """\
        Replace msgstr in ``babel_bytesio`` data with line wrapped one
        originally written in PO file.

        It is assumed that ``babel_bytesio`` data is generated by Babel
        write_po function.

        Babel write_po often changes (normalizes) msgstr automatically,
        leading to break original line wrapping. This side effects sometimes
        causes inconveniences, espacially for CJK charset translations.

        This function parses ``babel_bytesio`` and replace msgstr data if
        possible.

        :param babel_bytesio: byte stream for PO file data to update.
        :return: io.BufferedIOBase
        """
        ret_bytesio = io.BytesIO()
        for line in babel_bytesio.readlines():
            if (not self._in_msgid) and (not self._in_msgstr):
                if line.startswith(b"msgid"):
                    self._start_msgid(line)
                    continue
                if line.startswith(b"msgstr"):
                    self._start_msgstr(line)
                    continue
            elif self._in_msgid:  # self._in_msgid is True
                if line.startswith(b'"'):
                    self._process_msgid(line)
                    continue
                elif re.search(b"^(msgstr|msgctxt|#)", line):
                    self._end_msgid(ret_bytesio)
                    if line.startswith(b"msgstr"):
                        self._start_msgstr(line)
                        continue
                else:
                    raise PoFileParseError("error in parsing msgid")
            else:  # self._in_msgstr is True
                if re.search(br'(^"|^\s*$)', line):
                    self._process_msgstr(line)
                    continue
                elif re.search(b"^(msgctxt|#)", line):
                    self._end_msgstr(ret_bytesio)
                elif line.startswith(b"msgid"):
                    self._end_msgstr(ret_bytesio)
                    self._start_msgid(line)
                    continue
                else:
                    raise PoFileParseError("error in parsing msgstr")
            ret_bytesio.write(line)
        else:  # will be executed after for loop iterator is exhausted
            # in case an message entry is placed just before EOF
            if self._in_msgid:
                self._end_msgid(ret_bytesio)
            elif self._in_msgstr:
                self._end_msgstr(ret_bytesio, is_last=True)

        ret_bytesio.seek(0)
        return ret_bytesio

    def _start_msgid(self, line):
        self._in_msgid = True
        self._in_msgstr = False
        self._cur_msgid_po_lines = line

    def _process_msgid(self, line):
        self._cur_msgid_po_lines += line
        pass

    def _end_msgid(self, out_bytesio: io.BufferedIOBase):
        out_bytesio.write(self._cur_msgid_po_lines)
        cur_msgid = self._cur_msgid_po_lines.decode(self.catalog.charset)
        cur_msgid = re.sub(r"^msgid\s+", "", cur_msgid)
        self._cur_msgid = pofile.denormalize(cur_msgid)
        self._in_msgid = False

    def _start_msgstr(self, line):
        self._in_msgid = False
        self._in_msgstr = True
        self._cur_msgstr_po_lines = line

    def _process_msgstr(self, line):
        self._cur_msgstr_po_lines += line
        pass

    def _end_msgstr(
        self, out_bytesio: io.BufferedIOBase, is_last: bool = False
    ):
        cur_msgstr = re.sub(rb"^msgstr\s+", b"", self._cur_msgstr_po_lines)
        self._cur_msgstr = pofile.denormalize(
            cur_msgstr.decode(self.catalog.charset)
        )
        self._in_msgstr = False

        po_format_msgstr = self._cur_msgstr_po_lines
        cur_msg = self.catalog.get(self._cur_msgid)
        if isinstance(cur_msg, SphinxIntlMessage):
            # use original po format msgstr to write
            trailing_lines = re.search(
                rb"""(?mx)      # set flags for multiline, verbose
                    (^\s*$)+    # trailing lines
                    \Z          # end of string
                """,
                po_format_msgstr
            ).group(0)
            po_format_msgstr = (
                "msgstr " + cur_msg.get_po_format_translation()
            ).strip().encode(self.catalog.charset)
            out_bytesio.write(po_format_msgstr)
            out_bytesio.write(trailing_lines)
            if not is_last:
                out_bytesio.write(b"\n")
        else:
            out_bytesio.write(self._cur_msgstr_po_lines)


def _read_po_stream(fileobj: io.TextIOBase, charset: str) -> Catalog:
    catalog = Catalog(charset=charset)
    parser = SphinxIntlPoFileParser(
        catalog, ignore_obsolete=False, abort_invalid=False,
    )
    parser.parse(fileobj)
    return catalog


def _write_po_stream(
    fileobj: io.BufferedIOBase, catalog: Catalog, line_width: int = 76
):
    writer = SphinxIntlPoFileWriter(catalog, line_width)
    writer.write_po(fileobj)


def load_po(filename: str) -> Catalog:
    """read po/pot file and return catalog object

    :param unicode filename: path to po/pot file
    :return: catalog object
    """
    with io.open(filename, 'rb') as f:
        cat = pofile.read_po(f)
    charset = cat.charset or 'utf-8'

    # FIXME: encoding VS charset
    with open(filename, 'r', encoding=charset) as f:
        return _read_po_stream(f, charset)


def dump_po(filename: str, catalog: Catalog, line_width: int = 76) -> None:
    """write po/pot file from catalog object

    :param unicode filename: path to po file
    :param catalog: catalog object
    :param line_width: maximum line wdith of po files
    :return: None
    """
    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    # Because babel automatically encode strings, file should be open as binary mode.
    with io.open(filename, 'wb') as f:
        # pofile.write_po(f, catalog, line_width)
        _write_po_stream(f, catalog, line_width)


def write_mo(filename: str, catalog: Catalog) -> None:
    """write mo file from catalog object

    :param unicode filename: path to mo file
    :param catalog: catalog object
    :return: None
    """
    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with io.open(filename, 'wb') as f:
        mofile.write_mo(f, catalog)


def translated_entries(catalog: Catalog) -> list[str]:
    return [m for m in catalog if m.id and m.string]


def fuzzy_entries(catalog: Catalog) -> list[str]:
    return [m for m in catalog if m.id and m.fuzzy]


def untranslated_entries(catalog: Catalog) -> list[str]:
    return [m for m in catalog if m.id and not m.string]


def update_with_fuzzy(catalog: Catalog, catalog_source: Catalog) -> None:
    """update catalog by template catalog with fuzzy flag.

    :param catalog: catalog object to be updated
    :param catalog_source: catalog object as a template to update 'catalog'
    :return: None
    """

    # to use PO format msgstr of messages later, save them if possible before
    # updating catalog
    po_msgstr = dict()
    for orig_msg in catalog:
        if isinstance(orig_msg, SphinxIntlMessage):
            po_msgstr[orig_msg.id] = orig_msg.get_po_format_translation()

    catalog.update(catalog_source)

    # For fuzzy entries, ``catalog.update()`` use babel message class which
    # does not keep PO format msgstr. Replace them with SphinxIntlMessage
    # to have PO format msgstr.
    msg_list: list[Message] = [msg for msg in catalog]
    for new_msg in msg_list:
        if isinstance(new_msg.id, str) and new_msg.id in po_msgstr:
            update_msg = SphinxIntlMessage.copy_from_babel_message(new_msg)
            update_msg.set_po_format_translation(po_msgstr[new_msg.id])
            catalog.delete(new_msg.id)
            catalog[new_msg.id] = update_msg
        if (
            new_msg.previous_id and
            isinstance(new_msg.previous_id[0], str) and
            new_msg.previous_id[0] in po_msgstr
        ):
            update_msg = SphinxIntlMessage.copy_from_babel_message(new_msg)
            update_msg.set_po_format_translation(
                po_msgstr[new_msg.previous_id[0]]
            )
            catalog.delete(new_msg.id)
            catalog[new_msg.id] = update_msg
