#!/usr/bin/env python3

import argparse
import telnetlib as t

from flask import Flask, request, render_template, redirect, g
from functools import wraps
from time import sleep

pioneer = ("83.133.178.82", 23)

setupCommands = {
    "tisch": ("04FN",),
    "sofa": ("15FN",),
}

lautsprecherOptions = {
    "alle": "3",
    "nord": "1",
    "keiner": "0",
    "sued": "2",
}

app = Flask(__name__)

def sessionWrapper(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            g.s = getSession()
        except Exception as e:
            msg = "Connection to the receiver could not be established. Please check that the device is powered. (%s)" % e
            return render_template("error.html", msg=msg), 500
        return f(*args, **kwargs)
    return decorated_function

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("error.html", msg=e), 500

def sendCommand(command, session):
    session.write(command.encode('ascii') + b"\r")

def getSession(target = pioneer, timeout = 5):
    return t.Telnet(target[0],target[1],timeout=timeout)

def powerOn(session):
    sendCommand("PO", session)

def powerOff(session):
    sendCommand("PF", session)

def getPowerStatus(session):
    session.read_eager()
    sendCommand("?P", session)
    return "PWR0" in session.read_some().decode('ascii')

def setUp(session):
    on = getPowerStatus(session)

    if not on:
        powerOn(session)
        sleep(0.1)
        sendCommand(lautsprecherOptions["alle"]+"SPK",session)

def renderedIndex():
    lautsprecher = list(lautsprecherOptions.keys())
    lautsprechWidth = (80-len(lautsprecher)*2)/len(lautsprecher)

    return render_template("index.html", lautsprecher=lautsprecher, lautsprechWidth = lautsprechWidth)

@app.route("/")
def index():
    return renderedIndex()

@app.route("/receiver/setups/<setting>")
@sessionWrapper
def setups(setting):
    setUp(g.s)

    if setting in setupCommands.keys():
        for command in setupCommands[setting]:
            sendCommand(command, g.s)
    return redirect("/")

@app.route("/receiver/power/<state>")
@sessionWrapper
def power(state):
    if state == "on":
        setUp(g.s)
    elif state == "off":
        powerOff(g.s)
    return redirect("/")

@app.route("/receiver/lautsprecher")
@sessionWrapper
def lautsprecher():
    setUp(g.s)

    choice = request.args.get('welche')
    if choice in lautsprecherOptions.keys():
        sendCommand(lautsprecherOptions[choice]+"SPK",g.s)
    return redirect("/")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Hauptraum AV Setup Control Server')
    parser.add_argument('--port', '-p', type=int, default=5002)
    args = parser.parse_args()

    app.run(host='0.0.0.0', port=args.port)
