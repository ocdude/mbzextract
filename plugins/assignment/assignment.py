import os
import xml.etree.ElementTree as et
from html.parser import HTMLParser
from datetime import datetime
from jinja2 import Environment, PackageLoader

class moodle_module:
    def __init__(self,**kwargs):
        self.backup = kwargs['backup']
        self.temp_dir = kwargs['temp_dir']
        self.db = kwargs['db']
        self.directory = kwargs['directory']
        self.final_dir = kwargs['working_dir']
        self.db_cursor = self.db.cursor()
        self.files = []

        # create table for this activity
        query = 'CREATE TABLE IF NOT EXISTS assignments (activityid int PRIMARY KEY,moduleid int,contextid int,name text,intro text,assignmenttype text)'
        self.db_cursor.execute(query)

        if kwargs['student_data'] == True:
            # create table for the submissions to the assignments
            query = 'CREATE TABLE IF NOT EXISTS assignment_submissions (submissionid int PRIMARY KEY,activityid int,userid int,timecreated int,timemodified int,data text,grade real,comment text,teacher int,timemarked int)'
            self.db_cursor.execute(query)
            self.student_data = kwargs['student_data']

        # commit the changes
        self.db.commit()

    def parse(self):
        """Parse the assignment.xml and inforef.xml files to get the details
         for the assignment and any files associated with it."""
        assignment_xml = et.parse(self.backup.open(self.directory+"/assignment.xml")).getroot()
        inforef_xml = et.parse(self.backup.open(self.directory+"/inforef.xml")).getroot()

        # add assignments to the database
        assignment = (assignment_xml.get('id'),
            assignment_xml.get('moduleid'),
            assignment_xml.get('contextid'),
            assignment_xml.find('./assignment/name').text,
            assignment_xml.find('./assignment/intro').text,
            assignment_xml.find('./assignment/assignmenttype').text)
        self.db_cursor.execute('INSERT INTO assignments VALUES(?,?,?,?,?,?)',assignment)

        # check to see if the backup file has student data in it
        if self.student_data == True:
            for submission in assignment_xml.findall('./assignment/submissions/submission'):
                entry = (submission.get('id'),
                    assignment_xml.get('id'),
                    submission.find('userid').text,
                    submission.find('timecreated').text,
                    submission.find('timemodified').text,
                    submission.find('data1').text,
                    submission.find('grade').text,
                    submission.find('submissioncomment').text,
                    submission.find('teacher').text,
                    submission.find('timemarked').text)
                self.db_cursor.execute('INSERT INTO assignment_submissions VALUES(?,?,?,?,?,?,?,?,?,?)', entry)


        # print some info about the assignment
        print('\tName:',assignment_xml.find('./assignment/name').text)
        print('\tType:',assignment_xml.find('./assignment/assignmenttype').text)

        # create a list of files
        if inforef_xml.find('fileref') is not None:
            for f in inforef_xml.findall('./fileref/file'):
                self.files.append(f.find('id').text)
        print('\tNumber of files:',len(self.files))

        # commit all changes to db
        self.db.commit()
    def extract(self):
        pass
    def extract_file(self,fileid):
        pass
