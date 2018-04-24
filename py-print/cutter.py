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

class FSMCutter(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(Cutter.Pos, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(Cutter.L, GPIO.OUT)
        GPIO.setup(Cutter.R, GPIO.OUT)
        self.queue = queue.Queue(maxsize=1)
        self.lock = threading.Lock()
        self._state = None
        self._stop()
        self.start()

    def kill(self):
        print("kill cutter..")
        self._stop()
        debug("Q+: None")
        self.queue.put(None)

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

    def _turn(self, pin):
        self._state = self._last_sens = pin
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
                self._stop()
                timeout = False
                break
        if timeout:
            debug("WAIT POS TIMEOUT ! should be in wrong position")
            self._stop()

    def run(self):
        while True:
            if self._state == 'stop':
                ev = self.queue.get(block=True)
            else:
                try:
                    ev = self.queue.get(timeout=Cutter.TIMEOUT)
                except queue.Empty:
                    print("Emergency stop")
                    self._stop()
                    continue
            if ev == Cutter.STOP:
                debug("Q- : stop")
                self._stop()
            elif ev in (Cutter.R, Cutter.L):
                debug("Q- : turn {}".format(ev))
                self._turn(ev)
            elif ev == Cutter.WAIT_POS:
                debug("Q- : wait pos")
                #debug("add ev turn : {}".format(ev))
                self._wait_pos()
            else:
                debug("Q- : ? {}".format(ev))
                break
        debug("end_of_cutter")
        self._stop()


class Cutter():
    DEBUG = False

    R = 5
    L = 7
    Pos = 3
    STOP = 0
    WAIT_POS = 1

    REPOS = 1
    ON = GPIO.HIGH
    OFF = GPIO.LOW

    HALF_TIME = 0.16
    FULL_TIME = 0.25
    TIMEOUT = 1 # sec

    def __init__(self, half_time=None, full_time=None, *args, **kwargs):
        self._fsmcutter = FSMCutter()
        self.half_time = Cutter.HALF_TIME if half_time is None else half_time
        self.full_time = Cutter.FULL_TIME if full_time is None else full_time
#        self._cut_full()
        self._fsmcutter.queue.put(Cutter.STOP)

    def _cut_full(self, start=None):
        self._fsmcutter.queue.put(Cutter.R)
        time.sleep(0.15)
        if start is None:
            start = time.time()
        debug("start wait pos..")
        timeout = True
        while time.time() - start < Cutter.TIMEOUT:
            pos = GPIO.input(Cutter.Pos)
            #print(str(pos))
            if Cutter.REPOS == pos:
                debug("--break")
                self._fsmcutter.queue.put(Cutter.STOP)
                timeout = False
                break
        time.sleep(0.05)
        if not timeout and GPIO.input(Cutter.Pos) != Cutter.REPOS:
            print("===== Double !")
            self._cut_full(start)

        if timeout:
            debug("WAIT POS TIMEOUT ! should be in wrong position")
            self._fsmcutter.queue.put(Cutter.STOP)
        # self._fsmcutter.queue.put(Cutter.WAIT_POS)

    def cut_full(self):
        with self._fsmcutter.lock:
            self._cut_full()

    def _cut_half(self, start=None):
        if start is None:
            self._fsmcutter.queue.put(Cutter.R)
            time.sleep(self.half_time)
        self._fsmcutter.queue.put(Cutter.L)
        if start is None:
            time.sleep(0.15)
            start = time.time()
        debug("start wait pos..")
        timeout = True
        while time.time() - start < Cutter.TIMEOUT:
            pos = GPIO.input(Cutter.Pos)
            print(str(pos))
            if Cutter.REPOS == pos:
                debug("--break")
                self._fsmcutter.queue.put(Cutter.STOP)
                timeout = False
                break
        time.sleep(0.05)
        if GPIO.input(Cutter.Pos) != Cutter.REPOS:
            print("===== Double !")
            self._cut_half(start)

        if timeout:
            debug("WAIT POS TIMEOUT ! should be in wrong position")
            self._fsmcutter.queue.put(Cutter.STOP)
        # self._fsmcutter.queue.put(Cutter.WAIT_POS)

    def cut_half(self):
        with self._fsmcutter.lock:
            self._cut_half()


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

    def __old_repos(self,sens='auto'):
        debug("start repos..")
        self.stop()
        if sens == 'L':
            self.turn(Cutter.L)
        elif sens == 'R':
            self.turn(Cutter.R)
        else:
            if self._last_sens == Cutter.R:
                self.turn(Cutter.L)
            else:
                self.turn(Cutter.R)
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
        self._fsmcutter.queue.put(Cutter.STOP)
        #self._queue.join()

    def _repos(self):
        self._cut_half(time.time())

    def repos(self):
        with self._fsmcutter.lock:
            self._repos()

    def quit(self):
        self._fsmcutter.queue.put(None)

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
            #self.repos()
            if mode == CUT_FULL:
                self.cut_full()
            elif mode == CUT_HALF:
                self.cut_half()
            debug("End Cut")
        except Exception as e:
            self.stop()
            raise e
