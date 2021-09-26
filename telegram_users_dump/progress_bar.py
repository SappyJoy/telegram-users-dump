#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

class ProgressBar:

    def __init__(self, title, size):
        self.pattern = "{}: {:<1d}/{:<1d} Found: {:<3d} [{}{}]"
        self.title = title
        self.size = size


    def startProgress(self):
        # digits_count = len(str(size))
        out_str = self.pattern.format(self.title, 0, self.size, 0, "", "-"*40)
        sys.stdout.write(out_str + chr(8)*len(out_str))
        sys.stdout.flush()

    def progress(self, x, found):
        filled = int((x / self.size * 4000) // 100)
        out_str = self.pattern.format(self.title, x, self.size, found, "#"*filled, "-"*(40-filled))
        sys.stdout.write(out_str + chr(8)*len(out_str))
        sys.stdout.flush()

    def endProgress(self, found):
        out_str = self.pattern.format(self.title, self.size, self.size, found, "#"*40, "")
        sys.stdout.write(out_str + "\n")
        sys.stdout.flush()