#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Usage:
tubd -c <chat_name> -p <phone_num> -f <filter> [-o <file>]
"""

import os
import sys
from telegram_users_dump.telegram_dumper import TelegramDumper
from telegram_users_dump.chat_dump_settings import ChatDumpSettings



def main():
    # print("run.main(): 13: " + __doc__)
    settings = ChatDumpSettings(__doc__)

    print("chat: " + settings.chat_name)
    print("phone: " + settings.phone_num)
    print("out: " + settings.out_file)
    print("filter: " + settings.filter)

    sys.exit(TelegramDumper(os.path.basename(__file__), settings).run())