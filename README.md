# Active handout telemetry python plugin

This plugin can be used standalone or with pytest to send telemetry data to the active handout server.

## Using with pytest

1. Install `pip3 install https://github.com/insper-education/active-handout-telemetry-py`
1. Run in terminal to authenticate with server: `telemetry auth` 
    - will return a token that must be past on terminal

### Config

For each exercise/test you must configure the telemetry to work, you can create a config file called: `telemetry.yml` like:

``` yaml
telemetry:
  ip: http://127.0.0.1:3000
  course: 23a-bits
  exercise-id: lab-5
  tags: hw
```

Where:

- `IP`: Ip with the telemetry server (i.e: `http://127.0.0.1:3000`)
- `COURSE_NAME`: A string to identify the course (i.e: `22b-bits`)
- `PREFIX`: A prefix to identify the exercise (i.e: `lab-5`)
- `TAGS`: Tags to classify the test (i.e: `"comb", "easy"`)

### Individual tags

For each individual test you can configure `tags` and `points`:

``` python
@pytest.mark.telemetry_tags("obj1", "easy")
@pytest.mark.telemetry_points(1)
def test_exe1():
    ...
```

> Individual tags will be appended to the globals


