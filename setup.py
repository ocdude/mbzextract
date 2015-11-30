#!/usr/bin/env python

from moodle2extract.mbz import __version__
from setuptools import setup, find_packages

packages = find_packages()
package_dir = {'':'plugins'}

setup(name='moodle2extract',
	version=__version__,
	description='Utility to extract data from a Moodle2 backup file',
	author='Cristian Alvarado',
	author_email='ocdude@bluewavedigital.net',
	packages=packages,
	install_requires=[
		'jinja2>=2.7',
		],
	scripts=['bin/moodle2extract']
)
