#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from telegram_users_dump.utils import JOIN_CHAT_PREFIX_URL


class ChatDumpSettings:
    """ Parses CLI arguments. """

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-few-public-methods
    def __init__(self, usage):

        # From telegram-cli
        self.api_id = 8875274
        self.api_hash = '559798f4a470d3da86862e3c8c290f85'

        # Parse parameters
        parser = CustomArgumentParser(formatter_class=CustomFormatter, usage=usage)

        parser.add_argument('-c', '--chat', required=True, type=str)
        parser.add_argument('-p', '--phone', required=True, type=str)
        parser.add_argument('-f', '--filter', default=".*", required=False, type=str)
        parser.add_argument('-i', '--ignore_case', required=False, action='store_true')
        parser.add_argument('-o', '--out', default='', required=False, type=str)
        parser.add_argument('-e', '--exp', default='', type=str)

        args = parser.parse_args()

        # Trim extra spaces in string param values
        if args.chat:
            args.chat = args.chat.strip()
        if args.phone:
            args.phone = args.phone.strip()
        
        # Validate phone number
        try:
            if int(args.phone) <= 0:
                raise ValueError
        except ValueError:
            parser.error('Phone number is invalid.')

        # Validate exporter name / set default
        exp_file = 'csv' if not args.exp else args.exp
        if not exp_file:
            parser.error('Exporter name is invalid.')

        # Default output file if not specified by user
        OUTPUT_FILE_TEMPLATE = 'telegram_{}.log'
        if args.out != '':
            out_file = args.out
        elif args.chat.startswith(JOIN_CHAT_PREFIX_URL):
            out_file = OUTPUT_FILE_TEMPLATE.format(args.chat.rsplit('/', 1)[-1])
        else:
            out_file = OUTPUT_FILE_TEMPLATE.format(args.chat)

        self.chat_name = args.chat
        self.phone_num = args.phone
        self.out_file = out_file
        self.filter = args.filter
        self.ignore_case = args.ignore_case
        self.exporter = exp_file


class CustomFormatter(argparse.HelpFormatter):
    """ Custom formatter for setting argparse formatter_class.
        It only outputs raw 'usage' text and omits other sections
        (e.g. positional, optional params and epilog).
    """

    def __init__(self, prog=''):
        argparse.HelpFormatter.__init__(
            self, prog, max_help_position=100, width=150)

    def add_usage(self, usage, actions, groups, prefix=None):
        if usage is not argparse.SUPPRESS:
            args = usage, actions, groups, ''
            self._add_item(self._format_usage, args)

    def _format_usage(self, usage, actions, groups, prefix):
        # if usage is specified, use that
        if usage is not None:
            usage = usage % dict(prog=self._prog)

        return "\n\r%s\n\r" % usage


class CustomArgumentParser(argparse.ArgumentParser):
    """ Custom ArgumentParser.
        Outputs raw 'usage' text and omits other sections.
    """

    def format_help(self):
        formatter = self._get_formatter()

        # usage
        formatter.add_usage(self.usage, self._actions,
                            self._mutually_exclusive_groups)

        return formatter.format_help()
