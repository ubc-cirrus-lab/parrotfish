import os

from setuptools import setup, find_packages

version = os.environ["PACKAGE_VERSION"]

with open("README.md", "r") as f:
    long_description = f.read()

with open("requirements.txt", "r") as r:
    requirements = r.read()

with open("requirements-dev.txt", "r") as rdev:
    requirements_dev = rdev.read()

setup(
    name="parrotfish",
    version=version,
    description="Parametric Regression for Optimizing Serverless Functions",
    packages=[package for package in find_packages() if package.startswith("src")],
    entry_points={"console_scripts": ["parrotfish=src.main:main"]},
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ubc-cirrus-lab/parrotfish",
    license="Apache License 2.0",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
    ],
    install_requires=requirements.split("\n"),
    extras_require={
        "dev": requirements_dev.split("\n"),
    },
    python_requires=">=3.8",
)
