from setuptools import setup, find_packages

setup(
    name="active handout telemetry",
    version="1.0",
    packages=["telemetry"],
    install_requires=["click", "requests", "wheel", "pytest", "pyyaml"],
    entry_points={
        "pytest11": [
            "pytest-telemetry = telemetry.pytest_telemetry",
        ],
        "console_scripts": ["telemetry=telemetry:cli"],
    },
)
