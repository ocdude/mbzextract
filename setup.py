#!/usr/bin/env python

from mbzextract.mbz import __version__
from setuptools import setup, find_packages

packages = find_packages()

setup(name='mbzextract',
      version=__version__,
      description='Utility to extract data from a Moodle backup file',
      author='Cristian Alvarado',
      author_email='ocdude@bluewavedigital.net',
      packages=packages,
      install_requires=[
          'jinja2>=2.7',
      ],
      license='MIT',
      scripts=['bin/mbzextract']
      )
