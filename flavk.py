#!/usr/bin/env python3

import argparse
import telnetlib as t

from flask import Flask, request, render_template, redirect
from time import sleep

pioneer = ("83.133.178.82", 23)
optoma = ("83.133.178.103", 1023)

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

projectorCommands = {
    "on": "~0000 1",
    "off": "~0000 0",
    "power?": "~00124 1",
}

projectorSetupCommands = {
    "receiver": ("~0012 1",),
    "vga": ("~0012 13",)
}

app = Flask(__name__)

def sendCommand(command, session):
    session.write(command.encode('ascii') + b"\r")

def getSession(target):
    return t.Telnet(target[0],target[1])

def getReceiverSession():
    return getSession(pioneer)

def getProjectorSession():
    return getSession(optoma)

def powerOnReceiver(session):
    sendCommand("PO", session)

def powerOffReceiver(session):
    sendCommand("PF", session)

def powerOnProjector(session):
    sendCommand(projectorCommands["on"], session)

def powerOffProjector(session):
    sendCommand(projectorCommands["off"], session)

def getReceiverPowerStatus(session):
    session.read_eager()
    sendCommand("?P", session)
    return "PWR0" in session.read_some().decode('ascii')

def getProjectorPowerStatus(session):
    sendCommand(projectorCommands["power?"], session)
    response = session.read_some()
    return "Ok1" in response.decode('ascii')

def setUpReceiver():
    s = getReceiverSession()
    on = getReceiverPowerStatus(s)

    if not on:
        powerOnReceiver(s)
        sleep(0.1)
        sendCommand(lautsprecherOptions["alle"]+"SPK",s)

    return s

def setUpProjector():
    s = getProjectorSession()

    ## Multiple commands seem to be a problem with the projector
    #on = getProjectorPowerStatus(s)
    on = False

    if not on:
        sleep(0.3)
        powerOnProjector(s)
    sleep(0.3)
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
    s = setUpReceiver()

    if setting in setupCommands.keys():
        for command in setupCommands[setting]:
            sendCommand(command, s)
    return redirect("/")

@app.route("/receiver/power/<state>")
def power(state):
    if state == "on":
        s = setUpReceiver()
    elif state == "off":
        s = getReceiverSession()
        sleep(0.3)
        powerOffReceiver(s)
    return redirect("/")

@app.route("/receiver/lautsprecher")
def lautsprecher():
    s = setUpReceiver()

    choice = request.args.get('welche')
    if choice in lautsprecherOptions.keys():
        sendCommand(lautsprecherOptions[choice]+"SPK",s)
    return redirect("/")

@app.route("/projector/power/<state>")
def projectorPower(state):
    if state == "on":
        s = setUpProjector()
    elif state == "off":
        s = getProjectorSession()
        powerOffProjector(s)
    return redirect("/")

@app.route("/projector/setups/<setting>")
def projectorSetups(setting):
    s = setUpProjector()

    if setting in projectorSetupCommands.keys():
        for command in projectorSetupCommands[setting]:
            sendCommand(command, s)
    return redirect("/")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Hauptraum AV Setup Control Server')
    parser.add_argument('--port', '-p', type=int, default=5002)
    args = parser.parse_args()

    app.run(host='0.0.0.0', port=args.port)
