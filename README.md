# Active handout telemetry python plugin

This plugin can be used standalone or with pytest to send telemetry data to the active handout server.

## Using with pytest

1. Install `pip3 install https://github.com/insper-education/active-handout-telemetry-py`
1. Run in terminal to authenticate with server: `telemetry auth` 
    - will return a token that must be past on terminal

### `test_` file

To identify the telemetry you must configure the plugin on the pytest file, adding the following code lines to the top of the test file:

``` py
import pytest
pytestmark = pytest.mark.telemetry(COURSE_NAME, PREFIX, TAGS)
```

Where:

- `COURSE_NAME`: A string to identify the course (i.e: `22b-bits`)
- `PREFIX`: A prefix to identify the exercise (i.e: `lab-5`)
- ``TAGS`: Tags to classify the test (i.e: `"comb", "easy"`)

For each individual test you can configure `tags` and `points`:

``` python
@pytest.mark.telemetry_tags("comb", "easy")
@pytest.mark.telemetry_points(1)
def test_exe1():
    ...
```

> Individual tags will be appended to the globals

## Config

TODO

- config server IP 
