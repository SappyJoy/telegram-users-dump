#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring

import re
from .common import common
from telegram_users_dump.utils import uin, ein

class text(object):
    """ text exporter plugin.
        By convention it has to be called exactly the same as its file name.
        (Apart from .py extention)
    """

    ext = ""

    def __init__(self):
        """ constructor """
        self.ESCAPE = re.compile(r'[\x00-\x1f\b\f\n\r\t]')
        self.ESCAPE_DICT = {
            '\\': '\\\\',
            # '"': '\\"',
            '\b': '\\b',
            '\f': '\\f',
            '\n': '\\n',
            '\r': '\\r',
            '\t': '\\t',
        }
        for i in range(0x20):
            self.ESCAPE_DICT.setdefault(chr(i), '\\u{0:04x}'.format(i))

    def format(self, fullUser, exporter_context):
        """ Formatter method. Takes fullUser and converts it to a *one-line* string.
            :param msg: Raw message object :class:`telethon.tl.types.Message` and derivatives.
                        https://core.telegram.org/type/Message

            :returns: *one-line* string containing one message data.
        """
        # pylint: disable=unused-argument
        id, first_name, last_name, username, phone, about = common.extract_user_data(fullUser)
        # Format a message log record
        user_dump_str = '[id={:10d}, {:10s} ({:18s}), phone={:11s}] {}'.format(
            id, uin(username, 10), uin(first_name, 7) + " " + uin(last_name, 10), uin(phone, 11), ein(self._py_encode_basestring(about)))

        return user_dump_str

    def begin_final_file(self, resulting_file, exporter_context):
        """ Hook executes at the beginning of writing a resulting file.
            (After BOM is written in case of --addbom)
        """
        pass



    # This code is inspired by Python's json encoder's code
    def _py_encode_basestring(self, s):
        """Return a JSON representation of a Python string"""
        if not s:
            return s
        def replace(match):
            return self.ESCAPE_DICT[match.group(0)]
        return self.ESCAPE.sub(replace, s)
