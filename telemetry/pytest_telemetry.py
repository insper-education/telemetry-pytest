#!/usr/bin/env python3
import pytest
from telemetry import Telemetry
import os.path as osp
from pathlib import Path
import inspect
import time


def getSrcCode(item):
    test_name = item.nodeid.split("::")[-1]
    func_name = test_name.split("_")[1]
    func = item.listchain()[1]
    module = getattr(func.module, func_name)
    return inspect.getsource(module.func)


def push(result, config):
    name = result["nodeid"].split("::")[1].replace("_", "-")
    log = {
        "ts": time.time(),
        "id": config["name"],
        "status": result["outcome"],
        "srcCode": config["srcCode"],
    }

    if log["status"] == "failed":
        log["msg"] = result["longrepr"]["reprcrash"]["message"]

    t = Telemetry(config["ip"])
    t.push(
        config["name"],
        config["prefix"] + "-" + name,
        config["tags"],
        config["points"],
        log,
    )


def parse_marks(item):
    marks_global = []
    marks_tags = []
    marks_points = ""

    for mark in item.iter_markers(name="telemetry"):
        marks_global = mark.args
        break

    for mark in item.iter_markers(name="telemetry_tags"):
        marks_tags = list(mark.args)
        break

    for mark in item.iter_markers(name="telemetry_points"):
        marks_points = list(mark.args)
        break

    tags = []
    tags.append(marks_global[2])
    tags.extend(marks_tags)
    tags = [x for x in tags if x != ""]

    return {
        "ip": marks_global[0],
        "name": marks_global[1],
        "prefix": marks_global[2],
        "tags": tags,
        "points": marks_points,
        "srcCode": getSrcCode(item),
    }


def pytest_configure(config):
    config.addinivalue_line("markers", "telemetry(name, prefix, tags): course name")
    config.addinivalue_line("markers", "telemetry_tags(name): telemetry tag")
    config.addinivalue_line("markers", "telemetry_points(name): telemetry points")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    result = outcome.get_result()

    if result.when == "call":
        push(result._to_json(), parse_marks(item))
