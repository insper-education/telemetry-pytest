#!/usr/bin/env python3
import pytest
from telemetry import Telemetry
import os.path as osp
from pathlib import Path
import inspect
import time


def get_module_code(item):
    test_name = item.nodeid.split("::")[-1]
    func_name = test_name.split("_")[1]
    func = item.listchain()[1]
    try:
        module = getattr(func.module, func_name)
        return inspect.getsource(module.func)
    except:
        print(f"[erro] Telemetry try to get src code {func}")
        return None


def get_src_code(item):
    src_code = ""

    for src in item:
        src_code = src_code + f"File name: {src} \r\n"
        if osp.isfile(src):
            src_file = open(src, "r")
            src_code = src_code + src_file.read() + "\r\n"
            src_file.close()
        else:
            print(f"[erro] Telemetry try to get src code {src}")
            src_code = src_code + "None" + "\r\n"

    return src_code


def push(result, telemetry, config):
    name = result["nodeid"].split("::")[1].replace("_", "-")
    log = {
        "ts": time.time(),
        "id": config["name"],
        "status": result["outcome"],
        "src": config["src"],
    }

    if log["status"] == "failed":
        log["msg"] = result["longrepr"]["reprcrash"]["message"]

    telemetry.push(
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

    src_code_list = []
    for mark in item.iter_markers(name="telemetry_files"):
        src_code_list = list(mark.args)
        break

    if len(src_code_list) == 0:
        src_code_string = get_module_code(item)
    else:
        src_code_string = get_src_code(src_code_list)

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
        "src": src_code_string,
    }


def pytest_configure(config):
    config.addinivalue_line("markers", "telemetry(name, prefix, tags): course name")
    config.addinivalue_line("markers", "telemetry_tags(name): telemetry tag")
    config.addinivalue_line("markers", "telemetry_points(name): telemetry points")
    config.addinivalue_line("markers", "telemetry_files(name): telemetry files")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    result = outcome.get_result()
    config = parse_marks(item)

    telemetry = Telemetry(config["ip"])
    if result.when == "call":
        push(result._to_json(), telemetry, config)
