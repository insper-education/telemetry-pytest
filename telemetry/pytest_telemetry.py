#!/usr/bin/env python3
import pytest
from telemetry import telemetry

t = telemetry()

def push(result, config):
    name = result["nodeid"].split("::")[1].replace('_', '-')
    log = {"id": name, "status": result["outcome"]}

    if log["status"] == "failed":
        log["msg"] = result["longrepr"]["reprcrash"]["message"]

    t.push(config['name'], config['prefix'] + '-' + name, config['tags'], config['points'], log)


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
    tags = [x for x in tags if x != '']
    return {'name': marks_global[0], 'prefix': marks_global[1], 'tags': tags, 'points': marks_points}


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "telemetry(name, prefix, tags): course name"
    )

    config.addinivalue_line(
        "markers", "telemetry_tags(name): telemetry tag"
    )

    config.addinivalue_line(
        "markers", "telemetry_points(name): telemetry points"
    )


def pytest_sessionstart(session):
    session.results = []


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    result = outcome.get_result()

    if result.when == "call":
        push(result._to_json(), parse_marks(item))
