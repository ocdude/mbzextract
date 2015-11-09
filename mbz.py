import os
import zipfile
import tarfile
import sys
import tempfile
import re
import xml.etree.ElementTree as et
import sqlite3
import magic
import importlib
from datetime import datetime
from html.parser import HTMLParser

class MBZ:
    def __init__(self):
        # create temporary file for sqlite database
        self.db_file = tempfile.NamedTemporaryFile().name

        # create the database and cursor
        self.db = sqlite3.connect(self.db_file, detect_types=sqlite3.PARSE_DECLTYPES)
        self.db_cursor = self.db.cursor()

        # create a table for list of activites and resources
        query = "CREATE TABLE activities (moduleid int, modulename text, title text, directory text)"
        self.db_cursor.execute(query)

        # create a table for users
        query = "CREATE TABLE users (userid int, firstname text, lastname text, email text)"
        self.db_cursor.execute(query)

        # commit the transaction
        self.db.commit()

    def parse_backup(self,backup_file):
        # check if the file provided is a zip file
        if magic.from_file(backup_file,mime=True) == b'application/zip':
            # open the zip file
            self.backup = zipfile.ZipFile(backup_file,'r')

            # try opening the moodle_backup.xml file and create the moodle_backup object
            try:
                self.moodle_backup = et.parse(self.backup.open('moodle_backup.xml')).getroot()
                self.moodle_users = et.parse(self.backup.open('users.xml')).getroot()
            except KeyError:
                sys.exit('The backup file provided does not seem to be a standard Moodle backup file. Exiting.')

        # if not a zip file, check if it's a tar.gz
        elif magic.from_file(backup_file,mime=True) == b'application/x-gzip':
            self.backup = tarfile.open(backup_file,'r')

            # try opening the moodle_backup.xml file and create the moodle_backup object
            try:
                self.moodle_backup = et.parse(self.backup.extractfile('moodle_backup.xml')).getroot()
                self.moodle_backup = et.parse(self.backup.extractfile('users.xml')).getroot()
            except KeyError:
                sys.exit('The backup file provided does not seem to be a standard Moodle backup file. Exiting.')

        else:
            sys.exit('The backup file provided does not seem to be a standard Moodle backup file. Exiting.')

        # parse the xml and add entries to the database

        # users first

        for user in self.moodle_users.findall('./user'):
            user_info = (user.get('id'),
                user.find('firstname').text,
                user.find('lastname').text,
                user.find('email').text)
            self.db_cursor.execute('INSERT INTO users VALUES(?,?,?,?)',user_info)

        # activities next

        for activity in self.moodle_backup.findall('./information/contents/activities/activity'):
            activity_info = (activity.find('moduleid').text,
                activity.find('modulename').text,
                activity.find('title').text,
                activity.find('directory').text)
            self.db_cursor.execute('INSERT INTO activities VALUES(?,?,?,?)',activity_info)

        self.db.commit()
        self.db_cursor.execute('SELECT DISTINCT modulename FROM activities')
        for module in self.db_cursor.fetchall():
            try:
                importlib.invalidate_caches()
                importlib.import_module("plugins."+module[0])
            except ImportError:
                print('A plugin for ' + module[0] + ' does not currently exist. Skipping.')
                continue
