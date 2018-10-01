#!/usr/bin/env python3

import time
import threading
import queue
from RPi import GPIO

DEBUG = True

def debug(txt):
    if DEBUG:
        print(txt)

CUT_FULL = 0
CUT_HALF = 1
REPOS = 1


class _CutterHardware(threading.Thread):
    DEBUG = False

    R = 5
    L = 7
    Pos = 3
    STOP = 0

    ON = GPIO.HIGH
    OFF = GPIO.LOW

    HALF_TIME = 0.19
    TIMEOUT = 1 # sec

    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(*args,**kwargs)
        self._queue = queue.Queue()
        self._stop = None
        self.stop()

    def kill(self):
        self._queue.put(None)

    def __del__(self):
        self.stop()
        self.kill()

    def stop(self):
        GPIO.output(Cutter.L, Cutter.OFF)
        GPIO.output(Cutter.R, Cutter.OFF)
        print("STOP : ok")
        self._state = 'stop'

    def turn(self, pin):
        if pin == Cutter.L:
            GPIO.output(Cutter.R, Cutter.OFF)
        elif pin == Cutter.R:
            GPIO.output(Cutter.L, Cutter.OFF)
        else:
            print("Unknown pin : {}".format(pin))
        GPIO.output(pin, Cutter.ON)

    def run(self):
        while True:
            if self._state == 'stop':
                ev = self._queue.get(block=True)
            else:
                try:
                    ev = self._queue.get(timeout=_CutterHardware.TIMEOUT)
                except queue.Empty:
                    print("Emergency stop")
                    self.stop()
                    continue
            if ev == Cutter.STOP:
                self.stop()
            elif ev in (Cutter.R, Cutter.L):
                self.turn(ev)
            else:
                break
        self.stop()






class OldCutter:
    DEBUG = False

    R = 5
    L = 7
    Pos = 3
    STOP = 0

    ON = GPIO.HIGH
    OFF = GPIO.LOW

    TIMEOUT = 500
    HALF_TIME = 0.19

    def __init__(self, half_time=None):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(Cutter.Pos, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(Cutter.L, GPIO.OUT)
        GPIO.setup(Cutter.R, GPIO.OUT)
        self.stop()
        self.half_time = Cutter.HALF_TIME if half_time is None else half_time

    def __del__(self):
        self.stop()

    def stop(self):
        GPIO.output(Cutter.L, Cutter.OFF)
        GPIO.output(Cutter.R, Cutter.OFF)
        print("STOP : ok")

    def turn(self, pin):
        if pin == Cutter.L:
            GPIO.output(Cutter.R, Cutter.OFF)
        elif pin == Cutter.R:
            GPIO.output(Cutter.L, Cutter.OFF)
        else:
            print("Unknown pin : {}".format(pin))
        GPIO.output(pin, Cutter.ON)

    def wait_pos(self, target_pos=REPOS):
        start = time.time()
        while time.time() - start < Cutter.TIMEOUT / 600 :
            pos = GPIO.input(Cutter.Pos)
            debug("pos : {}".format(pos))
            if target_pos == pos:
                debug("--break")
                break
            t = GPIO.wait_for_edge(Cutter.Pos, GPIO.BOTH, timeout=Cutter.TIMEOUT)
            if t is None:
                self.stop()
                break

    def cut(self, mode=CUT_FULL):
        if mode not in (CUT_FULL, CUT_HALF):
            mode = CUT_FULL
        try:
            debug("Mise en position")
            self.turn(Cutter.R)
            self.wait_pos()
            if mode == CUT_FULL:
                debug("Cut")
                self.turn(Cutter.R)
                time.sleep(self.half_time)
            elif mode == CUT_HALF:
                debug("Start cut")
                self.turn(Cutter.R)
                time.sleep(self.half_time)
                debug("Go back")
                self.turn(Cutter.L)
            self.wait_pos()
            self.stop()
            debug("End")
        except Exception as e:
            self.stop()
            raise e









