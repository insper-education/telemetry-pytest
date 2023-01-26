#!/usr/bin/env python3

import pytest
import json
from telemetry import telemetry


def push(t, result):



def pytest_configure(config):
    config.addinivalue_line(
        "markers", "telemetry(name, prefix, tags): course name"
    )

    config.addinivalue_line(
        "markers", "telemetry_tags(name): telemetry tag"
    )


def pytest_sessionstart(session):
    session.results = []


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    marks = [mark.args for mark in item.iter_markers(name="telemetry")][0]
#    tags = [mark.args for mark in item.iter_markers(name="telemetry_tags")][0]
    tconfig = {'name': marks[0], 'prefix': marks[1], 'tag': marks[2]}
    outcome = yield
    result = outcome.get_result()
    if result.when == "call":
        item.session.results.append(result._to_json())
        breakpoint()
        item.session.results['tconfig'] = tconfig


def pytest_sessionfinish(session, exitstatus):
    t = telemetry()
    for v in session.results:
        breakpoint()
        name = v["nodeid"].split("::")[1].replace('_', '-')
        status = t.statusOk
        log = {"id": name, "status": v["outcome"]}

        if log["status"] == "failed":
            log["msg"] = v["longrepr"]["reprcrash"]["message"]
            status = t.statusFail

#        slug = LOG_NAME_PREFIX + '-' + name
#        tags = TAGS
#        points = 0
#        t.push(COURSE_NAME, slug, tags, points, log)
