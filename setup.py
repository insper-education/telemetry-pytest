from setuptools import setup, find_packages

setup(
    name="active handout telemetry",
    version="1.0",
    packages=["telemetry"],
    include_package_data=True,
    install_requires=["click", "requests", "wheel"],
    entry_points="""
        [console_scripts]
        telemetry=telemetry:cli
    """,
)
