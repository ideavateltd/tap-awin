#!/usr/bin/env python

from setuptools import setup

setup(name='tap-awin',
      version='0.0.1',
      description='Singer.io tap for extracting data from the Affiliate Window API',
      author='Onedox',
      url='https://onedox.com',
      classifiers=['Programming Language :: Python :: 3 :: Only'],
      py_modules=['tap_awin'],
      install_requires=[
          'zeep>=1.4.1',
          'singer-python>=1.4.2',
          'tzlocal>=1.3',
      ],
      entry_points='''
          [console_scripts]
          tap-awin=tap_awin:main
      ''',
      packages=['tap_awin'],
      package_data = {
          'tap_awin/schemas': [
              "transactions.json",
              "merchants.json",
          ],
      },
      include_package_data=True,
)
