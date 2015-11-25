#!/usr/bin/env python

from setuptools import setup, find_packages

packages = find_packages()
package_dir = {'':'plugins'}

setup(name='moodle2extract',
	version='0.1',
	description='Utility to extract data from a Moodle2 backup file',
	author='Cristian Alvarado',
	author_email='ocdude@bluewavedigital.net',
	packages=packages,
	install_requires=[
		'jinja2',
		],
)
