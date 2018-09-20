#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from escpos.printer import Usb
from escpos.escpos import *
from .cut import Cutter, CUT_HALF, CUT_FULL

class KXKMPrinter(Usb):

    def __init__(self, *args, **kwargs):
        Usb.__init__(self, *args, **kwargs)
        self.cutter = Cutter()

    def cut(self, mode='FULL', feed=True):
        """ Cut paper.
        Without any arguments the paper will be cut completely. With 'mode=PART' a partial cut will
        be attempted. Note however, that not all models can do a partial cut. See the documentation of
        your printer for details.
        .. todo:: Check this function on TM-T88II.
        :param mode: set to 'PART' for a partial cut. default: 'FULL'
        :param feed: print and feed before cutting. default: true
        :raises ValueError: if mode not in ('FULL', 'PART')
        """

        if not feed:
            self._raw(GS + b'V' + six.int2byte(66) + b'\x00')
            return

        self.print_and_feed(6)

        mode = mode.upper()
        if mode not in ('FULL', 'PART'):
            raise ValueError("Mode must be one of ('FULL', 'PART')")

        if mode == "PART":
            self.cutter.cut(CUT_HALF)
        elif mode == "FULL":
            self.cutter.cut(CUT_FULL)

