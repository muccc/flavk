#!/usr/bin/env python3

import telnetlib as t

from flask import Flask, request, render_template, redirect
from time import sleep

pioneer = ("83.133.178.82", 23)

setupCommands = {
    "tisch": ("04FN",),
    "sofa-klinke": ("01FN",),
    "sofa-hdmi": ("10FN",),
}

lautsprecherOptions = {
    "alle": "3",
    "nord": "1",
    "keiner": "0",
    "sued": "2",
}

app = Flask(__name__)

def sendCommand(command, session):
    session.write(command.encode('ascii') + b"\r")

def getSession(target = pioneer):
    return t.Telnet(target[0],target[1])

def powerOn(session):
    sendCommand("PO", session)

def powerOff(session):
    sendCommand("PF", session)

def getPowerStatus(session):
    session.read_eager()
    sendCommand("?P", session)
    return "PWR0" in session.read_some().decode('ascii')

def setUp():
    s = getSession()

    on = getPowerStatus(s)

    if not on:
        powerOn(s)
        sleep(0.1)
        sendCommand(lautsprecherOptions["alle"]+"SPK",s)

    return s

def renderedIndex():
    lautsprecher = list(lautsprecherOptions.keys())
    lautsprechWidth = (80-len(lautsprecher)*2)/len(lautsprecher)

    return render_template("index.html", lautsprecher=lautsprecher, lautsprechWidth = lautsprechWidth)

@app.route("/")
def index():
    return renderedIndex()

@app.route("/receiver/setups/<setting>")
def setups(setting):
    s = setUp()

    if setting in setupCommands.keys():
        for command in setupCommands[setting]:
            sendCommand(command, s)
    return redirect("/")

@app.route("/receiver/power/<state>")
def power(state):
    if state == "on":
        s = setUp()
    elif state == "off":
        s = getSession()
        powerOff(s)
    return redirect("/")

@app.route("/receiver/lautsprecher")
def lautsprecher():
    s = setUp()


    choice = request.args.get('welche')
    if choice in lautsprecherOptions.keys():
        sendCommand(lautsprecherOptions[choice]+"SPK",s)
    return redirect("/")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002)
