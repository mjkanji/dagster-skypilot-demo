from setuptools import find_packages, setup

setup(
    name="dagster_skypilot",
    packages=find_packages(exclude=["dagster_skypilot_tests"]),
    install_requires=[
        "dagster>=1.6.0,<1.7.0",
        "dagster-cloud",
        "skypilot[aws,azure,gcp]",
        "dagster-shell",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
