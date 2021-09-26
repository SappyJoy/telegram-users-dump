#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring

import re
from .common import common
from telegram_users_dump.utils import ein, quoted_if_has_comma

class csv(object):
    """ csv (comma separated values) exporter plugin.
        By convention it has to be called exactly the same as its file name.
        (Apart from .py extention)
    """
    ext = ".csv"

    def __init__(self):
        """ constructor """
        self.ESCAPE = re.compile(r'[\x00-\x1f\\"\b\f\n\r\t]')
        self.ESCAPE_DICT = {
            '\\': '\\\\',
            '"': '""',
            '\b': '\\b',
            '\f': '\\f',
            '\n': '\\n',
            '\r': '\\r',
            '\t': '\\t',
        }
        for i in range(0x20):
            self.ESCAPE_DICT.setdefault(chr(i), '\\u{0:04x}'.format(i))

    def format(self, msg, exporter_context):
        """ Formatter method. Takes raw msg and converts it to a *one-line* string.
            :param msg: Raw message object :class:`telethon.tl.types.Message` and derivatives.
                        https://core.telegram.org/type/Message

            :returns: *one-line* string containing one message data.
        """
        # pylint: disable=unused-argument
        id, first_name, last_name, username, phone, about = common.extract_user_data(msg)
        # Format a message log record
        # msg_dump_str = '[{}-{:02d}-{:02d} {:02d}:{:02d}] ID={} {}{}: {}'.format(
        #     msg.date.year, msg.date.month, msg.date.day,
        #     msg.date.hour, msg.date.minute, msg.id, "RE_ID=%s " % re_id if re_id else "",
        #     name, self._py_encode_basestring(content))

        msg_dump_str = ",".join([str(id),
                                 quoted_if_has_comma(self._py_encode_basestring(username)[0]),
                                 quoted_if_has_comma(self._py_encode_basestring(first_name)[0]),
                                 quoted_if_has_comma(self._py_encode_basestring(last_name)[0]),
                                 ein(phone),
                                 quoted_if_has_comma(self._py_encode_basestring(about)[0])])
        return msg_dump_str

    def begin_final_file(self, resulting_file, exporter_context):
        """ Hook executes at the beginning of writing a resulting file.
            (After BOM is written in case of --addbom)
        """
        if not exporter_context.is_continue_mode:
            header_str = ",".join(["User Id", "Username", "First Name", "Last Name", "Phone", "Bio"])
            print(header_str, file=resulting_file)

    # This code is inspired by Python's json encoder's code
    def _py_encode_basestring(self, s):
        """Return a JSON representation of a Python string"""
        if not s:
            return s, False
        isAnyCharReplaced = False
        def replace(match):
            nonlocal isAnyCharReplaced
            isAnyCharReplaced = True
            return self.ESCAPE_DICT[match.group(0)]
        return str(self.ESCAPE.sub(replace, s)), isAnyCharReplaced
