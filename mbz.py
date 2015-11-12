import os
import zipfile
import tarfile
import sys
import tempfile
import shutil
import re
import xml.etree.ElementTree as et
import sqlite3
import magic
import importlib
from datetime import datetime
from html.parser import HTMLParser

class MBZ:
    def __init__(self):

        # create temporary directory for sqlite database and file extraction
        self.temp_dir = tempfile.mkdtemp()

        # create the database and cursor
        self.db_file = self.temp_dir + "/moodle.db"
        self.db = sqlite3.connect(self.db_file, detect_types=sqlite3.PARSE_DECLTYPES)
        self.db_cursor = self.db.cursor()

        # create a table for course information
        query = "CREATE TABLE course (fullname text, shortname text, moodle_release text, startdate int, www_root text)"
        self.db_cursor.execute(query)

        # create a table for list of activites and resources
        query = "CREATE TABLE activities (moduleid int, modulename text, title text, directory text)"
        self.db_cursor.execute(query)

        # create a table for users
        query = "CREATE TABLE users (userid int, firstname text, lastname text, email text)"
        self.db_cursor.execute(query)

        # create a table for files
        query = "CREATE TABLE files (id int, contenthash text, contextid int, filename text, mime text)"
        self.db_cursor.execute(query)

        # commit the transaction
        self.db.commit()

    def parse_backup(self,backup_file):

        self.backup = mbzFile(backup_file)

        # try opening the moodle_backup.xml file and create the moodle_backup object
        try:
            self.moodle_backup = et.parse(self.backup.open('moodle_backup.xml')).getroot()
            self.moodle_files = et.parse(self.backup.open('files.xml')).getroot()

            # check to see if this backup file has users
            if self.moodle_backup.find('./information/settings/setting/[name="users"]/value').text == "1":
                self.moodle_users = et.parse(self.backup.open('users.xml')).getroot()
                # add users into the database we just created
                for user in self.moodle_users.findall('./user'):
                    user_info = (user.get('id'),
                        user.find('firstname').text,
                        user.find('lastname').text,
                        user.find('email').text)
                    self.db_cursor.execute('INSERT INTO users VALUES(?,?,?,?)',user_info)

        except KeyError:
            sys.exit('The backup file provided does not seem to be a standard Moodle backup file. Exiting.')

        # activities next

        for activity in self.moodle_backup.findall('./information/contents/activities/activity'):
            activity_info = (activity.find('moduleid').text,
                activity.find('modulename').text,
                activity.find('title').text,
                activity.find('directory').text)
            self.db_cursor.execute('INSERT INTO activities VALUES(?,?,?,?)',activity_info)

        # then files

        for f in self.moodle_files.findall('./file'):
            file_info = (f.get('id'),
                f.find('contenthash').text,
                f.find('contextid').text,
                f.find('filename').text,
                f.find('mimetype').text)
            self.db_cursor.execute('INSERT INTO files VALUES (?,?,?,?,?)',file_info)

        self.db.commit()

    def extract(self):
        # function to load plugins, then extract files based on what we have plugins for
        pass

    def clean(self):
        shutil.rmtree(self.temp_dir)

class mbzFile(MBZ):

    # This class is intended to deal with the fact that the moodle backup files
    # can come in two flavors, zip and gzip. The python libraries for both
    # vary slightly.

    def __init__(self,backup_file):

        if magic.from_file(backup_file,mime=True) == b'application/zip':
            self.backup_type = "zip"
        elif magic.from_file(backup_file,mime=True) == b'application/x-gzip':
            self.backup_type = "gzip"
        self.file = backup_file

    def open(self,f):

        if self.backup_type == "zip":
            backup = zipfile.ZipFile(self.file,'r')
            return backup.open(f)

        elif self.backup_type == "gzip":
            backup = tarfile.open(self.file,'r')
            return backup.extractfile(f)

    def extract(self,file):
        pass
