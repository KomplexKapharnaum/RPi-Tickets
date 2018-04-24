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


class Cutter(threading.Thread):
    DEBUG = False

    R = 5
    L = 7
    Pos = 3
    STOP = 0

    ON = GPIO.HIGH
    OFF = GPIO.LOW

    HALF_TIME = 0.19
    TIMEOUT = 1.5 # sec

    def __init__(self, half_time=None, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(Cutter.Pos, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(Cutter.L, GPIO.OUT)
        GPIO.setup(Cutter.R, GPIO.OUT)
        self._queue = queue.Queue()
        self.half_time = Cutter.HALF_TIME if half_time is None else half_time
        self._state = None
        self.stop()
        self.start()

    def kill(self):
        print("kill cutter..")
        self._queue.put(None)

    def join(self, *args, **kwargs):
        if self._state != 'stop':
            time.sleep(Cutter.TIMEOUT)
        self.kill()
        threading.Thread.join(self,*args,**kwargs)

    def _stop(self):
        GPIO.output(Cutter.L, Cutter.OFF)
        GPIO.output(Cutter.R, Cutter.OFF)
        print("STOP : ok")
        self._state = 'stop'

    def _test(self):
        print("ALL OFF")
        GPIO.output(Cutter.L, Cutter.OFF)
        GPIO.output(Cutter.R, Cutter.OFF)
        time.sleep(0.5)
        print("Left")
        GPIO.output(Cutter.R, Cutter.OFF)
        GPIO.output(Cutter.L, Cutter.ON)
        time.sleep(1)
        print("Right")
        GPIO.output(Cutter.R, Cutter.ON)
        GPIO.output(Cutter.L, Cutter.OFF)
        time.sleep(1)
        print("ALL OFF")
        GPIO.output(Cutter.L, Cutter.OFF)
        GPIO.output(Cutter.R, Cutter.OFF)

    def _turn(self, pin):
        self._state = 'turn'
        if pin == Cutter.L:
            GPIO.output(Cutter.R, Cutter.OFF)
        elif pin == Cutter.R:
            GPIO.output(Cutter.L, Cutter.OFF)
        else:
            print("Unknown pin : {}".format(pin))
        GPIO.output(pin, Cutter.ON)

    def wait_pos(self, target_pos=REPOS):
        start = time.time()
        debug("start wait pos..")
        while time.time() - start < Cutter.TIMEOUT:
            pos = GPIO.input(Cutter.Pos)
            debug("pos : {}".format(pos))
            if target_pos == pos:
                debug("--break")
                break
            t = GPIO.wait_for_edge(Cutter.Pos, GPIO.BOTH,
                                   timeout=int(Cutter.TIMEOUT*500))
            if t is None:
                self.stop()
                break

    def stop(self):
        self._queue.put(Cutter.STOP)

    def turn(self, pin):
        self._queue.put(pin)

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
                time.sleep(self.half_time*1.5)
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

    def run(self):
        while True:
            if self._state == 'stop':
                ev = self._queue.get(block=True)
            else:
                try:
                    ev = self._queue.get(timeout=Cutter.TIMEOUT)
                except queue.Empty:
                    print("Emergency stop")
                    self._stop()
                    continue
            debug("ev : {}".format(ev))
            if ev == Cutter.STOP:
                self._stop()
            elif ev in (Cutter.R, Cutter.L):
                debug("add ev turn : {}".format(ev))
                self._turn(ev)
            else:
                break
        debug("end_of_cutter")
        self._stop()


