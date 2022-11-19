# -*- coding: utf-8 -*-

import os
import io
from copy import copy

from babel.messages import pofile, mofile, Message
from babel.messages.catalog import Catalog


class PoFileParseError(Exception):
    pass


class SphinxIntlMessage(Message):
    _po_format_translation: str = '""'

    def get_po_format_translation(self) -> str:
        return self._po_format_translation

    def set_po_format_translation(self, normalized_translation) -> None:
        self._po_format_translation = normalized_translation

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
        # import pdb; pdb.set_trace()
        # babel catalog do not replace message instance by catalog.__setitem__
        self.catalog.delete(msgid)
        self.catalog[msgid] = sphinx_intl_message


def _read_po_stream(fileobj: io.TextIOBase, charset: str) -> Catalog:

    # To decode lines by babel, read po file as binary mode and specify charset for
    # read_po function.
    # with io.open(filename, 'rb') as f:  # FIXME: encoding VS charset
    #     return pofile.read_po(f, charset=charset)
    catalog = Catalog(charset=charset)
    parser = SphinxIntlPoFileParser(
        catalog, ignore_obsolete=False, abort_invalid=False,
    )
    parser.parse(fileobj)
    return catalog


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
        pofile.write_po(f, catalog, line_width)


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
    catalog.update(catalog_source)
