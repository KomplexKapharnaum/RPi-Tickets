from flask import Flask
from flask import render_template, redirect

import os
import json
import random
import subprocess

app = Flask(__name__)

MEDIAS = {
    "TICKET_A": "/mnt/usb/TICKET_A.jpg",
    "TICKET_B": "/mnt/usb/TICKET_B.jpg",
    "TICKET_C": "/mnt/usb/TICKET_C.jpg",
    "TICKET_D": "/mnt/usb/TICKET_D.jpg",
    "TICKET_W": "/mnt/usb/TICKET_W.jpg",
}

PROPORTIONS = {
    "TICKET_A": 5,
    "TICKET_B": 9,
    "TICKET_C": 12,
    "TICKET_D": 23
}

WINNER = "TICKET_W"


class Scenario:
    instance = None

    def __init__(self, path="/data/rida_pool.json"):
        self.path = path
        self.infile = False
        if os.path.isfile(path):
            with open(self.path, mode="r") as fp:
                try:
                    self.pool = json.load(fp)
                    self.infile = True
                except Exception as e:
                    print("Error in reading JSON file : {}".format(e))

        if self.infile is not True:
            self.pool = Scenario.generate_pool(with_winner=True)
            self.save_pool()
        self.infinit_pool = Scenario.generate_pool(with_winner=False)

    def _take_ticket(self):
        if len(self.pool) > 0:
            ticket = self.pool.pop(0)
            self.save_pool()
        else:
            ticket = random.choice(self.infinit_pool)
        return ticket

    def save_pool(self):
        with open(self.path, mode="w") as fp:
            try:
                json.dump(self.pool, fp)
                self.infile = True
            except Exception as e:
                print("Error in creating JSON file : {}".format(e))
                self.infile = False

    @classmethod
    def take_ticket(cls):
        scenario = cls._get()
        return scenario._take_ticket()

    @classmethod
    def get_state(cls):
        scenario = cls._get()
        return {
            "infile": scenario.infile,
            "winner_remain": WINNER in scenario.pool,
            "pool_len": len(scenario.pool)
        }

    @classmethod
    def reset(cls):
        scenario = cls._get()
        if os.path.isfile(scenario.path):
            try:
                os.remove(scenario.path)
            except Exception as e:
                print("Error in deleting scenario pool : {}".format(e))
        cls.instance = cls()

    @classmethod
    def _get(cls):
        if cls.instance is None:
            cls.instance = cls()
        return cls.instance

    @classmethod
    def generate_pool(cls, with_winner):
        print("INIT POOL")
        pool = list()

        for ticket, n in PROPORTIONS.items():
            pool += [ticket for i in range(n)]
        random.shuffle(pool)
        if with_winner:
            pool.insert(random.randint(0, 9), WINNER)
            print("INITIAL SCENARIO : {}".format(pool))
        return pool


@app.route('/')
def hello_world():
    return render_template("index.html", **Scenario.get_state())


@app.route('/printTicket')
def print_ticket():
    ticket = Scenario.take_ticket()
    media = MEDIAS[ticket]
    print("TICKET : {} FILE : {}".format(ticket, media))
    subprocess.check_call(['/root/RPi-Tickets/py-print/print', '-c',
                           '--old', media])
    print("SCENARIO : {}".format(Scenario._get().pool))
    return redirect('/')


@app.route('/reset')
def reset():
    Scenario.reset()
    return redirect('/')


if __name__ == '__main__':
    app.run()
