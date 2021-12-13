import sys
from setuptools import setup, find_packages

if sys.version_info.major != 3:
    print("This code is only compatable with Python 3")

setup(name='spot',
      packages=[package for package in find_packages()
                if package.startswith('spot')],
      package_data={
          'spot': ['py.typed'],
      },
      install_requires=[],
      extras_require={},
      description='Serverless Price Optimization Tool',
      version='0.0.1'
      )
