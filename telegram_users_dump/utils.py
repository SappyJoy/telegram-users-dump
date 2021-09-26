#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Various utility functions/classes """

def sprint(string, *args, **kwargs):
    """Safe Print (handle UnicodeEncodeErrors on some terminals)"""
    try:
        print(string, *args, **kwargs)
    except UnicodeEncodeError:
        string = string.encode('utf-8', errors='ignore') \
            .decode('ascii', errors='ignore')
        print(string, *args, **kwargs)


JOIN_CHAT_PREFIX_URL = 'https://t.me/joinchat/'

# Underlines if object is None
def uin(obj, medium_length=5):
    return str(obj) if obj else "_" * medium_length

# Empty string if object is None
def ein(obj):
    return str(obj) if obj else ""

def quoted_if_has_comma(obj):
    if not obj:
        return ""
    if str(obj).find(",") != -1:
        return '"' + str(obj) + '"'
    return str(obj)