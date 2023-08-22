#!/usr/bin/env python3

import click
import configparser
import webbrowser
import requests
import json
import os
import pickle
import signal
import yaml
import pytest

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".telemetry.ini")
CONFIG_SECTION = "active handout"
QUEUE_FILE = os.path.join(os.path.expanduser("~"), ".telemetry.obj")
TIMEOUT = 10
DEFAULT_IP = "http://3.83.45.177"


class Queue:
    def __init__(self, file):
        self.file = file
        self.queue = self.open()

    def open(self):
        if os.path.exists(self.file):
            with open(self.file, "rb") as f:
                return pickle.load(f)
        else:
            return list()

    def put(self, item):
        self.queue.append(item)

    def len(self):
        return len(self.queue)

    def read(self):
        return self.queue.pop(0)

    def dump(self):
        with open(self.file, "wb+") as f:
            pickle.dump(self.queue, f)


class Config:
    def __init__(self, CONFIG_FILE):
        self.CONFIG_FILE = CONFIG_FILE
        self.config = configparser.ConfigParser()
        if self.config.read(self.CONFIG_FILE):
            self.config_section = self.config[CONFIG_SECTION]
            self.exist = True
        else:
            self.config_section = {}
            self.exist = False

    def updateConfig(self):
        self.config[CONFIG_SECTION] = self.config_section
        with open(self.CONFIG_FILE, "w") as configfile:
            self.config.write(configfile)

    def getInfo(self, info):
        if self.exist:
            if info in self.config_section:
                return self.config_section[info]
        return None

    def updateInfo(self, key, value):
        self.config_section[key] = value
        self.updateConfig()


class Telemetry:
    def __init__(self, URL_BASE=DEFAULT_IP):
        self.queue = Queue(QUEUE_FILE)
        self.config = Config(CONFIG_FILE)

        self.userToken = self.config.getInfo("token")

        self.URL_BASE = URL_BASE
        self.URL_LOGIN = self.URL_BASE + "/student/login"
        self.URL_GET_USER = self.URL_BASE + "/student/info"
        self.URL_PUSH_DATA = self.URL_BASE + "/student/push"

        signal.signal(signal.SIGALRM, self.interrupted)

    def checkToken(self, token):
        try:
            response = requests.get(
                self.URL_GET_USER,
                headers={"Authorization": token},
                timeout=TIMEOUT,
            )
            if response.ok == True:
                student = json.loads(response.content)
                if student:
                    return True
            return False
        except:
            return False

    def interrupted(signum, frame):
        signal.signal(signal.SIGALRM, interrupted)

    def prompToken(self):
        try:
            print("Past the token provide by the website after autentication")
            return input("Token:")
        except:
            return

    def isFromCI(self):
        return True if os.environ.get("CI") == "CI" else False

    def auth(self, timeout=1000):
        token = self.config.getInfo("token")
        if token is not None:
            if self.checkToken(token):
                self.userToken = token
                return True

        webbrowser.open(self.URL_LOGIN, new=1)
        while True:
            signal.alarm(timeout)
            token = self.prompToken()
            if token is None:
                return False

            signal.alarm(0)
            if self.checkToken(token):
                break

        self.config.updateInfo("token", token)
        self.userToken = token
        return True

    def appendUserConfig(self, data):
        data["userToken"] = self.userToken

    def pushDataToServer(self, data):
        headers = {
            "Authorization": self.userToken,
            "Content-type": "application/json",
        }
        try:
            response = requests.post(
                self.URL_PUSH_DATA,
                data=json.dumps(data),
                headers=headers,
                timeout=TIMEOUT,
            )
            return response.ok
        except:
            return False

    def createTelemetryData(self, course, channel, tags, points, log):
        if isinstance(tags, str):
            tags = [tags]

        return {
            "course": course,
            "channel": channel,
            #           "tags": tags,
            #           "points": points,
            "log": log,
        }

    def push(self, course, channel, tags, points, log):
        if (self.checkToken(self.userToken) is False) and (self.queue.len() == 0):
            self.auth(10000)

        data = self.createTelemetryData(course, channel, tags, points, log)
        self.queue.put(data)
        if self.userToken != None:
            for i in range(self.queue.len()):
                data = self.queue.read()
                self.appendUserConfig(data)
                if not self.pushDataToServer(data):
                    self.queue.put(data)
                    break
        self.queue.dump()


def telemetryMark():
    with open(".telemetry.yml", "r") as file:
        config = yaml.safe_load(file)["telemetry"]
        if (
            "ip" in config
            and "course" in config
            and "exercise-id" in config
            and "tags" in config
        ):
            return pytest.mark.telemetry(
                config["ip"], config["course"], config["exercise-id"], config["tags"]
            )
        print("Error: telemetry.yml file is not valid")
        os._exit(1)


def checkConfigIp():
    config = Config(CONFIG_FILE)
    ip = config.getInfo("ip")
    if ip is None:
        print("Please run telemetry config ip before")
        return False
    else:
        return ip


@click.group()
@click.option("--debug", "-b", is_flag=True, help="Enables verbose mode.")
@click.pass_context
def cli(ctx, debug):
    pass


@click.command()
def auth():
    t = Telemetry()
    if t.auth():
        print("All set! Configuration ok")
    else:
        print("Something went wrong, please try again")


@click.command()
def check():
    t = Telemetry()
    t.auth()
    data = t.createTelemetryData("test-course", "test-channel", "test", 0, "TEST LOG!")
    if t.pushDataToServer(data):
        print("Connection ok, pushed data to server")
    else:
        print("Connection failed")


@click.group()
def log():
    pass


@log.command()
def check():
    queue = Queue(QUEUE_FILE)
    print(f"There is {queue.len()} logs waiting to be pushed")


cli.add_command(auth)
cli.add_command(check)
cli.add_command(log)

if __name__ == "__main__":
    cli()
