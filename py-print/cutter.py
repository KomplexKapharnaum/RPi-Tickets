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


class Cutter(threading.Thread):
    DEBUG = False

    R = 5
    L = 7
    Pos = 3
    STOP = 0
    WAIT_POS = 1

    REPOS = 1
    ON = GPIO.HIGH
    OFF = GPIO.LOW

    HALF_TIME = 0.22
    TIMEOUT = 1.2 # sec

    def __init__(self, half_time=None, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(Cutter.Pos, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(Cutter.L, GPIO.OUT)
        GPIO.setup(Cutter.R, GPIO.OUT)
        self._queue = queue.Queue(maxsize=1)
        self.half_time = Cutter.HALF_TIME if half_time is None else half_time
        self._state = None
        self._stop()
        self.start()
        self.stop()

    def kill(self):
        print("kill cutter..")
        self._stop()
        debug("Q+: None")
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
        print("Repos")
        self._repos()
        print("ALL OFF")
        GPIO.output(Cutter.L, Cutter.OFF)
        GPIO.output(Cutter.R, Cutter.OFF)

    def _repos(self):
        GPIO.output(Cutter.L, Cutter.OFF)
        GPIO.output(Cutter.R, Cutter.OFF)
        time.sleep(0.1)
        GPIO.output(Cutter.L, Cutter.ON)
        time.sleep(0.1)
        self.wait_pos()
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

    def _wait_pos(self):
        start = time.time()
        debug("start wait pos..")
        timeout = True
        while time.time() - start < Cutter.TIMEOUT:
            pos = GPIO.input(Cutter.Pos)
            if Cutter.REPOS == pos:
                debug("--break")
                timeout = False
                break
        if timeout:
            debug("WAIT POS TIMEOUT ! should be in wrong position")
            time.sleep(0.5)
        time.sleep(0.01)
        self._stop()

    def repos(self):
        debug("start repos..")
        self.stop()
        self.turn(Cutter.L)
        self.wait_pos()


    def _old_wait_pos(self, target_pos=REPOS):
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
            else:
                debug("pos t = {}".format(t))

    def stop(self):
        debug("Q+: stop")
        self._queue.put(Cutter.STOP)
        #self._queue.join()

    def turn(self, pin):
        debug("Q+: turn {}".format(pin))
        self._queue.put(pin)
        #self._queue.join()

    def wait_pos(self):
        debug("Q+: wait pos")
        self._queue.put(Cutter.WAIT_POS)

    def cut(self, mode=CUT_FULL):
        if mode not in (CUT_FULL, CUT_HALF):
            mode = CUT_FULL
        try:
            debug("Mise en position")
            self.repos()
            if mode == CUT_FULL:
                debug("Cut Full")
                self.turn(Cutter.R)
                time.sleep(self.half_time)
                self.wait_pos()
                self.repos()
            elif mode == CUT_HALF:
                debug("Cut Partial")
                self.turn(Cutter.R)
                time.sleep(self.half_time)
                debug("Go back")
                self.turn(Cutter.L)
                self.repos()
            debug("End Cut")
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
                    self._wait_pos()
                    continue
            if ev == Cutter.STOP:
                debug("Q- : stop")
                self._stop()
                self._queue.task_done()
            elif ev in (Cutter.R, Cutter.L):
                debug("Q- : turn {}".format(ev))
                #debug("add ev turn : {}".format(ev))
                self._turn(ev)
                self._queue.task_done()
            elif ev == Cutter.WAIT_POS:
                debug("Q- : wait pos")
                #debug("add ev turn : {}".format(ev))
                self._wait_pos()
                self._queue.task_done()
            else:
                debug("Q- : ? {}".format(ev))
                self._queue.task_done()
                break
        debug("end_of_cutter")
        self._stop()


