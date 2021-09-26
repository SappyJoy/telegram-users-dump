#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Usage:
telegram_users_dump -c <chat_name> -p <phone_num> [-f <filter>] [-o <file>]

Where:
    -c,  --chat         Unique name of a channel/chat. E.g. @python.
    -p,  --phone        Phone number. E.g. +380503211234.
    -f,  --filter       Filter using regular expression
    -i,  --ignore_case  Ignore case while filtering
    -o,  --out          Output file name or full path. (Default: telegram_<chatName>.log)
    -e,  --exp          Exporter name. text | jsonl | csv (Default: 'text')
    -h,  --help         Show this help message and exit.
"""

import os
import sys
import importlib
from telegram_users_dump.telegram_dumper import TelegramDumper
from telegram_users_dump.chat_dump_settings import ChatDumpSettings
from telegram_users_dump.utils import sprint



def main():
    settings = ChatDumpSettings(__doc__)
    exporter = _load_exporter(settings.exporter)
    settings.out_file += exporter.ext
    sys.exit(TelegramDumper(os.path.basename(__file__), settings, exporter).run())

def _load_exporter(exporter_name):
    """ Loads exporter from file <exporter_name>.py in ./exporters subfolder.
        :param exporter_name:      name of exporter. E.g. 'text' or 'json'

        :return: Exporter instance
    """
    # By convention exporters are located in .\exporters subfolder
    # COMMENT: Don't check file existance. It won't play well with pyinstaller bins
    exporter_file_name = exporter_name + ".py"
    exporter_rel_name = "telegram_users_dump.exporters." + exporter_name
    # Load exporter from file
    sprint("Try to load exporter '%s'...  " % (exporter_file_name), end='')
    try:
        exporter_module = importlib.import_module(exporter_rel_name)
        sprint("OK!")
    except ModuleNotFoundError:
        sprint("\nERROR: Failed to load exporter './exporters/%s'." % exporter_file_name)
        exit(1)

    try:
        exporterClass = getattr(exporter_module, exporter_name)
    except AttributeError:
        sprint("ERROR: Failed to load class '%s' out of './exporters/%s'." \
               % (exporter_name, exporter_file_name))
        exit(1)

    return exporterClass()