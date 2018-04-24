#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from escpos.printer import Usb
from escpos.escpos import *
import time
from cutter import Cutter, CUT_HALF, CUT_FULL

class KXKMPrinter(Usb):

    def __init__(self, mode, *args, **kwargs):
        Usb.__init__(self, *args, **kwargs)
        self.cutter = Cutter()
        if mode == 'rpi':
            self.cut = self._cut_rpi
        else:
            self.cut = Usb.cut

    def _cut_rpi(self, mode='PART', feed=True):
        """ Cut paper.
        Without any arguments the paper will be cut completely. With 'mode=PART' a partial cut will
        be attempted. Note however, that not all models can do a partial cut. See the documentation of
        your printer for details.
        .. todo:: Check this function on TM-T88II.
        :param mode: set to 'PART' for a partial cut. default: 'FULL'
        :param feed: print and feed before cutting. default: true
        :raises ValueError: if mode not in ('FULL', 'PART')
        """

        if feed:
            self._raw(ESC + b"d" + six.int2byte(4))
            time.sleep(0.07)

        mode = mode.upper()
        if mode not in ('FULL', 'PART'):
            raise ValueError("Mode must be one of ('FULL', 'PART')")

        try:
            if mode == "PART":
                self.cutter.cut(CUT_HALF)
            elif mode == "FULL":
                self.cutter.cut(CUT_FULL)
        except Exception as e:
            self.cutter.stop()
            raise e

        if feed:
            self._raw(ESC + b"d" + six.int2byte(2))
            time.sleep(0.05)

