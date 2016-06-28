"""Basic template for creating new plugins.

A basic plugin should have at the very minimum a class called 'moodle_module',
with an '__init__(self, **kwargs)' method that populates a table in the temporary
backup database with the structure of the module it is attempting to extract, a
parse method that parses the backup xml file for the module, and an extract method
that does the actual extraction of the contents of the module, whatever it may be.

The very minimum imports should be os and shutil.
"""
import os
import shutil

class moodle_module:

    def __init__(self,**kwargs):
        pass

    def parse(self):
        pass

    def extract(self):
        pass
