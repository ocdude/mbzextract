#!/usr/bin/env python

from distutils.core import setup

package_dir = {'':'plugins'}

setup(name='Moodle2 data extrator',
	version='0.1',
	description='Utility to extract data from a Moodle2 backup file',
	author='Cristian Alvarado',
	author_email='ocdude@bluewavedigital.net',
	packages=['mbz','mbz.plugins'],
	install_requires=[
		'jinja2',
		],
)
