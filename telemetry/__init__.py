#!/usr/bin/env python3

import click
import configparser
import webbrowser
import requests
import json
import os
import pickle
import signal

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".telemetry.ini")
QUEUE_FILE = os.path.join(os.path.expanduser("~"), ".telemetry.obj")

URL_BASE = "http://localhost:8080/"
URL_LOGIN = URL_BASE + "api/login?next=/api/user-token"
URL_GET_USER = URL_BASE + "api/user-info"
URL_PUSH_DATA = URL_BASE + "api/telemetry"


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


class telemetry:
    def __init__(self):
        self.queue = Queue(QUEUE_FILE)
        self.userToken = ""
        self.statusOk = "O"
        self.statusFail = "F"
        self.statusNone = "N"
        self.TIMEOUT = 400
        signal.signal(signal.SIGALRM, self.interrupted)

    def checkToken(self, token):
        response = requests.get(URL_GET_USER, headers={'Authorization': f'Token {token}'}, timeout=self.TIMEOUT)
        if response.ok != 200:
            student = json.loads(response.content)
            if student and 'id' in student:
                return True
        return False

    def interrupted(signum, frame):
        signal.signal(signal.SIGALRM, interrupted)

    def prompToken(self):
        try:
            print("Past the token provide by the website after autentication")
            return input("Token:")
        except:
            return

    def createConfig(self, token):
        config = configparser.ConfigParser()
        config["active handout"] = {}
        config["active handout"]["token"] = token
        with open(CONFIG_FILE, "w") as configfile:
            config.write(configfile)

    def isFromCI(self):
        return True if os.environ.get("CI") == "CI" else False

    def getStudentFromCI(self):
        return os.environ.get("GITHUB_ACTOR")

    def auth(self):
        config = configparser.ConfigParser()
        if config.read(CONFIG_FILE):
            if 'token' in config['active handout']:
                token = config["active handout"]["token"]
                if self.checkToken(token):
                    self.userToken = token
                    return True

        webbrowser.open(URL_LOGIN, new=1)
        print("Wrong token, please update")

        while True:
            signal.alarm(self.TIMEOUT)
            token = self.prompToken()
            signal.alarm(0)
            if self.checkToken(token):
                break
            self.userToken = None
            return False

        self.createConfig(token)

        self.userToken = token
        return True

    def appendUserConfig(self, data):
        data["userToken"] = self.userToken

    def pushDataToServer(self, data):
        headers = {'Authorization': f'Token {self.userToken}',
                   "Content-type": "application/json"}
        try:
            response = requests.post(
                URL_PUSH_DATA,
                data=json.dumps(data),
                headers=headers,
                timeout=self.TIMEOUT,
            )
            return response.ok
        except:
            print("[ERRO] telemetry timeout")
            return False

    def createTelemetryData(self, course_name, slug, tags, points, log):
        if isinstance(tags, str):
            tags = [tags]

        exercise = {'course': course_name,
                    'slug': slug,
                    'tags': tags,
                    'points': points}

        data = {'exercise': exercise,
                'log': log}

        return data

    def push(self, course_name, slug, tags, points, log):
        if self.userToken == "":
            self.auth()

        data = self.createTelemetryData(course_name, slug, tags, points, log)
        self.queue.put(data)

        if self.userToken != None:
            for i in range(self.queue.len()):
                data = self.queue.read()
                self.appendUserConfig(data)
                if not self.pushDataToServer(data):
                    self.queue.put(data)
                    break

        self.queue.dump()


@click.group()
@click.option("--debug", "-b", is_flag=True, help="Enables verbose mode.")
@click.pass_context
def cli(ctx, debug):
    pass


@click.command()
def auth():
    t = telemetry()
    if t.auth():
        print("All set! Configuration ok")


@click.command()
def check():
    t = telemetry()
    t.auth()
    data = t.createTelemetryData('test-connection', 'test-connection', 'test', 0, '')
    if t.pushDataToServer(data):
        print('Connection ok, pushed data to server')
    else:
        print('Connection failed')


cli.add_command(auth)
cli.add_command(check)

if __name__ == "__main__":
    cli()
