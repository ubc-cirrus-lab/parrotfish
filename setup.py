import sys
from setuptools import setup, find_packages

if sys.version_info.major != 3:
    print("This code is only compatable with Python 3")

setup(
    name="parrotfish",
    packages=[package for package in find_packages() if package.startswith("src")],
    package_data={
        "src": ["py.typed"],
    },
    install_requires=[],
    extras_require={},
    entry_points={"console_scripts": ["parrotfish=src.main:main"]},
    description="Parametric Regression for Optimizing Serverless Functions",
    version="0.0.1",
)
