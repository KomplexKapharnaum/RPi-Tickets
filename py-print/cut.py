#!/usr/bin/env python3

import time
from RPi import GPIO

DEBUG = False

def debug(txt):
    if DEBUG:
        print(txt)

CUT_FULL = 0
CUT_HALF = 1
REPOS = 1

class Cutter:
    DEBUG = False

    R = 5
    L = 7
    Pos = 3

    ON = GPIO.HIGH
    OFF = GPIO.LOW

    HALF_TIME = 0.19

    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(Cutter.Pos, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(Cutter.L, GPIO.OUT)
        GPIO.setup(Cutter.R, GPIO.OUT)
        self.stop()

    def stop(self):
        GPIO.output(Cutter.L, Cutter.OFF)
        GPIO.output(Cutter.R, Cutter.OFF)

    def turn(self, pin):
        if pin == Cutter.L:
            GPIO.output(Cutter.R, Cutter.OFF)
        elif pin == Cutter.R:
            GPIO.output(Cutter.L, Cutter.OFF)
        else:
            print("Unknown pin : {}".format(pin))
        GPIO.output(pin, Cutter.ON)

    def wait_pos(self, target_pos=REPOS):
        while True:
            pos = GPIO.input(Cutter.Pos)
            debug("pos : {}".format(pos))
            if target_pos == pos:
                debug("--break")
                break
            GPIO.wait_for_edge(Cutter.Pos, GPIO.BOTH, timeout=1)

    def cut(self, mode=CUT_FULL):
        if mode not in (CUT_FULL, CUT_HALF):
            mode = CUT_FULL

        debug("Mise en position")
        self.turn(Cutter.R)
        self.wait_pos()
        if mode == CUT_FULL:
            debug("Cut")
            self.turn(Cutter.R)
            time.sleep(Cutter.HALF_TIME)
        elif mode == CUT_HALF:
            debug("Start cut")
            self.turn(Cutter.R)
            time.sleep(Cutter.HALF_TIME)
            debug("Go back")
            self.turn(Cutter.L)
        self.wait_pos()
        self.stop()
        debug("End")









