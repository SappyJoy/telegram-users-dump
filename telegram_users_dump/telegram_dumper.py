#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" This is a main Module that contains code
    that fetches messages from Telegram and do processing.
"""

import os
import sys
import logging
import re
from joblib import Parallel, delayed
from time import sleep
from collections import deque
from telethon.tl.types import ChannelParticipantsSearch
from telegram_users_dump.exceptions import DumpingError
from telegram_users_dump.utils import sprint
from getpass import getpass
import codecs
from telethon import TelegramClient, sync # pylint: disable=unused-import
from telethon.errors import (FloodWaitError,
                             SessionPasswordNeededError,
                             UsernameNotOccupiedError,
                             UsernameInvalidError)
from telethon import functions, types
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telegram_users_dump.utils import JOIN_CHAT_PREFIX_URL, ein
from telegram_users_dump.exporter_context import ExporterContext
from telegram_users_dump.progress_bar import ProgressBar


class TelegramDumper(TelegramClient):
    """ Authenticates and opens new session. Retrieves message history for a chat. """

    def __init__(self, session_user_id, settings, exporter):
        self.logger = logging.getLogger(__name__)
        self.logger.info('Initializing session...')
        super().__init__(session_user_id, settings.api_id, settings.api_hash, timeout=40, proxy=None)

        # Settings as specified by user or defaults or from metadata
        self.settings = settings
        
        # A list of paths to the temp files
        self.temp_files_list = deque()

        # Exporter object that converts msg -> string
        self.exporter = exporter

        # The context that will be passed to the exporter
        self.exporter_context = ExporterContext()

        # The number of messages written into a resulting file de-facto
        self.output_total_count = 0

    def run(self):
        """ Dumps all desired chat messages into a file """

        ret_code = 0
        try:
            self._init_connect()
            try:
                channel = self._getChannel()
            except ValueError as ex:
                ret_code = 1
                self.logger.error('%s', ex,
                                  exc_info=self.logger.level > logging.INFO)
                return
            # Fetch history in chunks and save it into a resulting file
            self._do_dump(channel)
            
        except DumpingError as ex:
            self.logger.error('%s', ex, exc_info=self.logger.level > logging.INFO)
            ret_code = 1
        except KeyboardInterrupt:
            sprint("Received a user's request to interrupt, stopping…")
            ret_code = 1
        except Exception as ex:
            self.logger.error('Uncaught exception ocurred. %s', ex, exc_info=self.logger.level > logging.INFO)
        finally:
            self.logger.debug('Make sure there are no temp files left undeleted.')
            # Clear temp files if any
            while self.temp_files_list:
                try:
                    os.remove(self.temp_files_list.pop().name)
                except Exception:  # pylint: disable=broad-except
                    pass

        sprint('{} users were successfully written in the resulting file. Done!'
               .format(self.output_total_count))
        return ret_code

    def _init_connect(self):
        """ Connect to the Telegram server and Authenticate. """
        sprint('Connecting to Telegram servers...')
        if not self.connect():
            # sprint('Initial connection failed.')
            pass

        # Then, ensure we're authorized and have access
        if not self.is_user_authorized():
            sprint('First run. Sending code request...')
            self.send_code_request(self.settings.phone_num)
            self_user = None
            while self_user is None:
                code = input('Enter the code you just received: ')
                try:
                    self_user = self.sign_in(self.settings.phone_num, code)
                # Two-step verification may be enabled
                except SessionPasswordNeededError:
                    pw = getpass("Two step verification is enabled. "
                                 "Please enter your password: ")
                    self_user = self.sign_in(password=pw)

    def _getChannel(self):
        """ Returns telethon.tl.types.Channel object resolved from chat_name
            at Telegram server
        """
        name = self.settings.chat_name

        # For private channуls try to resolve channel peer object from its invitation link
        # Note: it will only work if the login user has already joined the private channel.
        # Otherwise, get_entity will throw ValueError
        if name.startswith(JOIN_CHAT_PREFIX_URL):
            self.logger.debug('Trying to resolve as invite url.')
            try:
                peer = self.get_entity(name)
                if peer:
                    sprint('Invitation link "{}" resolved into channel id={}'.format(
                        name, peer.id))
                    return peer
            except ValueError as ex:
                self.logger.debug('Failed to resolve "%s" as an invitation link. %s',
                                  self.settings.chat_name,
                                  ex,
                                  exc_info=self.logger.level > logging.INFO)

        if name.startswith('@'):
            name = name[1:]
            self.logger.debug('Trying ResolveUsernameRequest().')
            try:
                peer = self(ResolveUsernameRequest(name))
                if peer.chats is not None and peer.chats:
                    sprint('Chat name "{}" resolved into channel id={}'.format(
                        name, peer.chats[0].id))
                    return peer.chats[0]
                if peer.users is not None and peer.users:
                    sprint('User name "{}" resolved into channel id={}'.format(
                        name, peer.users[0].id))
                    return peer.users[0]
            except (UsernameNotOccupiedError, UsernameInvalidError) as ex:
                self.logger.debug('Failed to resolve "%s" as @-chat-name. %s',
                                  self.settings.chat_name,
                                  ex,
                                  exc_info=self.logger.level > logging.INFO)

        # Search in dialogs first, this way we will find private groups and
        # channels.
        self.logger.debug('Fetch loggedin user`s dialogs')
        dialogs_count = self.get_dialogs(0).total
        self.logger.info('%s user`s dialogs found', dialogs_count)
        dialogs = self.get_dialogs(limit=None)
        self.logger.debug('%s dialogs fetched.', len(dialogs))
        for dialog in dialogs:
            if dialog.name == name:
                sprint('Dialog title "{}" resolved into channel id={}'.format(
                    name, dialog.entity.id))
                return dialog.entity
            if hasattr(dialog.entity, 'username') and dialog.entity.username == name:
                sprint('Dialog username "{}" resolved into channel id={}'.format(
                    name, dialog.entity.id))
                return dialog.entity
            if name.startswith('@') and dialog.entity.username == name[1:]:
                sprint('Dialog username "{}" resolved into channel id={}'.format(
                    name, dialog.entity.id))
                return dialog.entity
        self.logger.debug('Specified chat name was not found among dialogs.')

        raise ValueError('Failed to resolve dialogue/chat name "{}".'.format(name))

    def _do_dump(self, channel):
        """ Retrieves users and save them in-memory 'buffer'.
            Then writes them in resulting file.

             :param peer: Chat/Channel object that contains the message history of interest

             :return  Number of files that were saved into resulting file
        """
        self.msg_count_to_process = sys.maxsize

        self._check_preconditions()

        # Current buffer of messages, that will be batched into a temp file
        # or otherwise written directly into the resulting file if there are too few of them
        # to form a batch of size 1000.
        buffer = deque()
        filter_flags = re.IGNORECASE if self.settings.ignore_case else 0
        pattern = re.compile(self.settings.filter, filter_flags)

        # process users
        try:
            all_participants = self.get_participants(channel, filter=ChannelParticipantsSearch(''), aggressive=True)
            users_size = len(all_participants)
            sprint("Found users total: {}".format(users_size))

            users_count = 0
            found = 0
            bar = ProgressBar("Processed users", users_size)
            bar.startProgress()
            for user in all_participants:
                full = self(functions.users.GetFullUserRequest(user))
                if pattern.search(ein(full.about)):
                    user_dump_str = self.exporter.format(full, self.exporter_context)
                    buffer.append(user_dump_str)
                    found += 1
                users_count += 1
                bar.progress(users_count, found)
            bar.endProgress(found)
        except RuntimeError as ex:
            sprint('Fetching users from server failed. ' + str(ex))
            sprint('Warn: The resulting file will contain partial/incomplete data.')

        sprint('Writing results into an output file.')
        try:
            self._write_final_file(buffer)
        except OSError as ex:
            raise DumpingError("Dumping to a final file failed.") from ex

    def _check_preconditions(self):
        """ Check preconditions before processing data """
        out_file_path = self.settings.out_file
        if os.path.exists(out_file_path):
            sprint('Warning: The output file already exists.')
            if not self._is_user_confirmed('Are you sure you want to overwrite it? [y/n]'):
                raise DumpingError("Terminating on user's request...")
        # Check if output file can be created/overwritten
        try:
            with open(out_file_path, mode='w+'):
                pass
        except OSError as ex:
            raise DumpingError('Output file path "{}" is invalid. {}'.format(
                out_file_path, ex.strerror))
        sprint('Dumping {} users into "{}" file ...'
                .format('all' if self.msg_count_to_process == sys.maxsize
                        else self.msg_count_to_process, out_file_path))

    def _flush_buffer_into_filestream(self, buffer, file_stream):
        """ Flush buffer into a file stream """
        count = 0
        while buffer:
            count += 1
            cur_user = buffer.pop()
            print(cur_user, file=file_stream)
        return count

    def _write_final_file(self, buffer):
        # result_file_mode = 'a' if self.settings.last_message_id > -1 else 'w'
        with codecs.open(self.settings.out_file, 'w', 'utf-8') as resulting_file:
            # if self.settings.is_addbom:
            #     resulting_file.write(codecs.BOM_UTF8.decode())

            # self.exporter.begin_final_file(
            #     resulting_file, self.exporter_context)

            # flush what's left in the mem buffer into resulting file
            self.output_total_count += self._flush_buffer_into_filestream(
                buffer, resulting_file)

    def _is_user_confirmed(self, msg):
        """ Get confirmation from user """
        # if self.settings.is_quiet_mode:
        #     return True
        continueResponse = input(msg).lower().strip()
        return continueResponse == 'y'\
            or continueResponse == 'yes'