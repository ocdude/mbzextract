__version__ = "0.0.2a"
import os
import zipfile
import tarfile
import sys
import tempfile
import shutil
import re
import xml.etree.ElementTree as et
import sqlite3
import importlib


class MBZ:
    """This class has functions to deal with .mbz moodle backup files. It
    provides several functions to parse and extract files out of a moodle backup."""

    def __init__(self, output=None):
        if output == None:
            # set the output directory to the current working directory
            # if an explicit output directory was not specified
            self.out_dir = os.getcwd()
        else:
            # check to see if the output directory already exists
            if os.path.exists(output):
                self.out_dir = output
            else:
                # otherwise create the directory
                os.makedirs(output)
                self.out_dir = output

        # create temporary directory for sqlite database and file extraction
        self.temp_dir = tempfile.mkdtemp()

        # create the database and cursor
        self.db_file = os.path.join(self.temp_dir, 'moodle.db')
        self.db = sqlite3.connect(self.db_file,
                                  detect_types=sqlite3.PARSE_DECLTYPES)
        self.db_cursor = self.db.cursor()

        # create a table for course information
        query = '''CREATE TABLE IF NOT EXISTS course
            (fullname text, shortname text, moodle_release text,
            startdate int, www_root text)'''
        self.db_cursor.execute(query)

        # create a table for list of activites and resources
        query = '''CREATE TABLE IF NOT EXISTS activities
            (moduleid int, modulename text, title text, directory text,
            sectionid int)'''
        self.db_cursor.execute(query)

        # create a table for sections
        query = '''CREATE TABLE IF NOT EXISTS sections
            (sectionid int,title text,directory text)'''
        self.db_cursor.execute(query)

        # create a table for users
        query = '''CREATE TABLE IF NOT EXISTS users
            (userid int, firstname text, lastname text, email text)'''
        self.db_cursor.execute(query)

        # create a table for files
        query = '''CREATE TABLE IF NOT EXISTS files
            (id int, contenthash text, contextid int, filename text, userid int,
            mime text)'''
        self.db_cursor.execute(query)

        # commit the transaction
        self.db.commit()

        # TODO: There probably should be a table created for grades, but that
        # is for a future revision

    def parse_backup(self, backup_file):
        """Open the moodle_backup.xml and files.xml files and parse
        the contents into the database"""
        print("Parsing the moodle backup file...")
        self.backup = mbzFile(backup_file)

        # try opening the moodle_backup.xml file and create the moodle_backup
        # object
        try:
            self.moodle_backup = et.parse(
                self.backup.open('moodle_backup.xml')).getroot()
            self.moodle_files = et.parse(
                self.backup.open('files.xml')).getroot()

            # check to see if this backup file has users
            if self.moodle_backup.find('./information/settings/setting/[name="users"]/value').text == "1":
                self.moodle_users = et.parse(
                    self.backup.open('users.xml')).getroot()
                # add users into the database we just created
                for user in self.moodle_users.findall('./user'):
                    user_info = (user.get('id'),
                                 user.find('firstname').text,
                                 user.find('lastname').text,
                                 user.find('email').text)
                    self.db_cursor.execute(
                        'INSERT INTO users VALUES(?,?,?,?)', user_info)
                self.user_data = True
            else:
                self.user_data = False

            # grab course information
            course_info = (self.moodle_backup.find('./information/original_course_fullname').text,
                           self.moodle_backup.find(
                               './information/original_course_shortname').text,
                           self.moodle_backup.find(
                               './information/moodle_release').text,
                           self.moodle_backup.find(
                               './information/original_course_startdate').text,
                           self.moodle_backup.find('./information/original_wwwroot').text)
            self.db_cursor.execute(
                'INSERT INTO course VALUES (?,?,?,?,?)', course_info)
            self.course = self.moodle_backup.find(
                './information/original_course_fullname').text
            print("Course:", self.course)
        except KeyError:
            sys.exit(
                'The backup file provided does not seem to be a standard Moodle backup file. Exiting.')

        # sections first
        for section in self.moodle_backup.findall('./information/contents/sections/section'):
            section_info = (section.find('sectionid').text,
                            section.find('title').text,
                            section.find('directory').text)
            self.db_cursor.execute(
                'INSERT INTO sections VALUES(?,?,?)', section_info)

        # activities next
        for activity in self.moodle_backup.findall('./information/contents/activities/activity'):
            activity_info = (activity.find('moduleid').text,
                             activity.find('modulename').text,
                             activity.find('title').text,
                             activity.find('directory').text,
                             activity.find('sectionid').text)
            self.db_cursor.execute(
                'INSERT INTO activities VALUES(?,?,?,?,?)', activity_info)

        # then files
        for f in self.moodle_files.findall('./file'):
            # do a sanity check on file name before continuing
            if f.find('filename').text == ".":
                continue
            else:
                filename = f.find('filename').text
            id = f.get('id')
            contenthash = f.find('contenthash').text
            contextid = f.find('contextid').text
            mimetype = f.find('mimetype').text
            userid = f.find('userid').text

            # create a file listing
            file_info = (id,
                         contenthash,
                         contextid,
                         filename,
                         userid,
                         mimetype)

            self.db_cursor.execute(
                'INSERT INTO files VALUES (?,?,?,?,?,?)', file_info)

        self.db.commit()
        return self.moodle_backup, self.moodle_files

    def extract(self):
        """Loops through the activities and resources in the backup file and attempts
        to load a plugin for the module. If a plugin does not exist for the module, it skips
        to the next one. Each plugin is responsible for extracting the content for each module type."""

        # create the output directory for extracting the contents
        if os.path.exists(os.path.join(self.out_dir, self.stripped(self.course))) == False:
            os.mkdir(os.path.join(self.out_dir, self.stripped(self.course)))
        os.chdir(os.path.join(self.out_dir, self.stripped(self.course)))
        self.final_dir = os.getcwd()

        # create directory structure by section
        self.db_cursor.execute('SELECT * FROM sections')
        for section in self.db_cursor.fetchall():
            if os.path.exists("Section - " + self.stripped(section[1]) + "_" + str(section[0])) == False:
                os.mkdir("Section - " +
                         self.stripped(section[1]) + "_" + str(section[0]))
            os.chdir("Section - " +
                     self.stripped(section[1]) + "_" + str(section[0]))

            # set the working directory to the path for the section we just
            # created
            work_dir = os.path.join(
                self.final_dir, "Section - " + self.stripped(section[1]) + "_" + str(section[0]))

            # create a directory for files if this section has files associated with it
            # that are not part of an activity
            inforef_xml = et.parse(self.backup.open(
                section[2] + "/inforef.xml")).getroot()
            if inforef_xml.find('./fileref') is not None:
                if os.path.exists('files') == False:
                    os.mkdir('files')

                # extract the files
                os.chdir(self.temp_dir)
                for f in inforef_xml.findall('./fileref/file'):
                    self.db_cursor.execute(
                        'SELECT contenthash,filename FROM files WHERE filename != "." and id=?', (f.find('id').text,))
                    results = self.db_cursor.fetchone()
                    if results is not None:
                        out_path = os.path.join(self.final_dir, "Section - " + self.stripped(
                            section[1]) + "_" + str(section[0]), "files", results[1])
                        self.extract_file(results[0], out_path)
                os.chdir(os.path.join(self.final_dir, "Section - " +
                                      self.stripped(section[1]) + "_" + str(section[0])))

            # fetch the activities in this section
            self.db_cursor.execute(
                'SELECT modulename,moduleid,directory FROM activities WHERE sectionid=?', (section[0],))
            activities = self.db_cursor.fetchall()

            # import plugin for the activity if we have one
            for activity in activities:
                try:
                    plugin_string = "mbzextract.plugins." + \
                        activity[0] + "." + activity[0]
                    plugin = importlib.import_module(
                        plugin_string, 'mbzextract')
                    print("\033[32;1mExtracting\033[0m", activity[0])
                except ImportError as e:
                    print("\033[31;1mSkipping\033[0m", activity[0],e)
                    continue

                mod = plugin.moodle_module(backup=self.backup,
                                           temp_dir=self.temp_dir,
                                           db=self.db,
                                           directory=activity[2],
                                           working_dir=work_dir,
                                           student_data=self.user_data)
                mod.parse()
                mod.extract()
            os.chdir(self.final_dir)

        # create a copy of the sqlite database in the extracted folder
        shutil.copy(self.db_file, os.path.join(
            self.final_dir, "backup_database.db"))

        # create a readme file in the folder
        #f = open(os.path.join(self.final_dir, "readme.txt"), 'w')
        #f.write("The folders are organized by the sections as they existed in your moodle course. Inside each section folder is a folder for each activity or resource that existed. In each activity or resource folder is a folder called 'files' that contains the files from that activity or resource.")
        #f.close()

    def clean(self):
        """Cleans the temporary directory of any remaining files and removes the temporary directory."""
        shutil.rmtree(self.temp_dir)

    def stripped(self, x):
        """A helper function that strips symbols and non-safe characters. Plugins can use
        this function to provide safe file and folder names."""
        the_string = x.strip()
        the_string = re.sub(r'(?u)[^\w\s]', '', the_string)
        return the_string.lstrip(' ').rstrip(' ')

    def extract_file(self, f, dest):
        """A helper function to extract the file from the .mbz data structure. Inside
        the .mbz file is a folder called `files` that contains hashed versions of files in order to
        prevent duplicate copies of files being stored. The `files` table in the sqlite database this
        class creates contains a key that matches the hashed value from the backup with the filename
        the file originally had."""
        try:
            self.backup.extract(os.path.join('files', f[:2], f))
            shutil.move(os.path.join('files', f[:2], f), dest)
        except KeyError:
            print("File not found:",f)
            return "File not found"

    def list_files(self, inforef_xml, db_cursor):
        """A helper function that each plugin can use to find the files that are associated
        with the specific module that is currently being extracted."""
        # create list to hold file ids
        ids = []
        files = []
        # find files associated with a particular module
        # compared against the list of files in the backup
        if inforef_xml.find('fileref') is not None:
            for f in inforef_xml.findall('fileref/file/id'):
                ids.append(f.text)
            ids = tuple(ids)
            db_cursor.execute(
                'SELECT id FROM files WHERE id IN (' + ','.join('?' * len(ids)) + ')', ids)
            results = db_cursor.fetchall()
            for fileid in results:
                files.append(fileid[0])
        return files

    def get_progress(self, extracted, total):
        pass


class mbzFile(MBZ):

    """This class is intended to deal with the fact that the moodle backup files
     can come in two flavors, zip and gzip. The python libraries for both
     vary slightly."""

    def __init__(self, backup_file):

        if zipfile.is_zipfile(backup_file) == True:
            self.backup_type = "zip"

        elif tarfile.is_tarfile(backup_file) == True:
            self.backup_type = "gzip"

        else:
            sys.exit('This file is of an unknown type. Exiting.')

        self.file = backup_file

    def open(self, f):

        if self.backup_type == "zip":
            self.backup = zipfile.ZipFile(self.file, 'r')
            return self.backup.open(f)

        elif self.backup_type == "gzip":
            self.backup = tarfile.open(self.file, 'r:gz')
            return self.backup.extractfile(f)

    def extract(self, f):
        # This seems unecessary and probably is considering both libraries have
        # the same method, but whatever, this is staying for fear of breaking
        # something later down the line.
        if self.backup_type == "zip":
            return self.backup.extract(f)

        elif self.backup_type == "gzip":
            return self.backup.extract(f)

    def get_file_size(self, f):
        """Returns the file size of the file in bytes."""
        if self.backup_type == "zip":
            info = self.backup.getinfo(os.path.join('files', f[:2], f))
            return info.file_size

        elif self.backup_type == "gzip":
            info = self.backup.getmember(os.path.join('files', f[:2], f))
            return info.size
