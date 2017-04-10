import os
import xml.etree.ElementTree as et
import html
from datetime import datetime
from jinja2 import Environment, PackageLoader

# this is a very unfortunate hack and needs to be fixed

class moodle_module:

    def __init__(self, **kwargs):
        self.backup = kwargs['backup']
        self.temp_dir = kwargs['temp_dir']
        self.db = kwargs['db']
        self.directory = kwargs['directory']
        self.final_dir = kwargs['working_dir']
        self.db_cursor = self.db.cursor()

        # create table for this activity
        query = 'CREATE TABLE IF NOT EXISTS assignments (activityid int PRIMARY KEY,moduleid int,contextid int,name text,intro text)'
        self.db_cursor.execute(query)

        if kwargs['student_data'] == True:
            # this is temporary until I figure out student submission logic

            # create table for the submissions to the assignments
            # query = 'CREATE TABLE IF NOT EXISTS assignment_submissions (submissionid int PRIMARY KEY,activityid int,userid int,timecreated int,timemodified int,data text,grade real,comment text,teacher int,timemarked int)'
            # self.db_cursor.execute(query)
             self.student_data = kwargs['student_data']
        else:
            self.student_data = False

        # commit the changes
        self.db.commit()
        self.env = Environment(loader=PackageLoader(
            'mbzextract.plugins.assign', 'templates'))

    def parse(self):
        """Parse the assignment.xml and inforef.xml files to get the details
         for the assignment and any files associated with it."""
        assignment_xml = et.parse(self.backup.open(
            self.directory + "/assign.xml")).getroot()
        inforef_xml = et.parse(self.backup.open(
            self.directory + "/inforef.xml")).getroot()

        # add assignments to the database
        assignment = (assignment_xml.get('id'),
                      assignment_xml.get('moduleid'),
                      assignment_xml.get('contextid'),
                      assignment_xml.find('./assign/name').text,
                      html.unescape(assignment_xml.find(
                          './assign/intro').text))
        self.db_cursor.execute(
            'INSERT INTO assignments VALUES(?,?,?,?,?)', assignment)
        self.current_id = assignment_xml.get('id')

        #this is temporary
        self.student_data = False
        # check to see if the backup file has student data in it
        if self.student_data == True:
            for submission in assignment_xml.findall('./assign/submissions/submission'):
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
                self.db_cursor.execute(
                    'INSERT INTO assignment_submissions VALUES(?,?,?,?,?,?,?,?,?,?)', entry)

        self.files = self.backup.list_files(inforef_xml, self.db_cursor)

        # commit all changes to db
        self.db.commit()

    def extract(self):
        self.db_cursor.execute(
            'SELECT * FROM assignments WHERE activityid=?', (self.current_id,))
        results = self.db_cursor.fetchone()
        path = os.path.join(self.final_dir, self.backup.stripped(results[3]))
        if os.path.exists(path) == False:
            os.makedirs(path)
        os.chdir(path)

        # this is temporary until I rebuild assignment submission logic
        self.student_data = False


        if self.student_data == True:
            self.db_cursor.execute(
                'SELECT submissionid,userid,timemodified,data,grade,comment,teacher,timemarked FROM assignment_submissions WHERE activityid=? ORDER BY timemodified DESC', (self.current_id,))
            sub_results = self.db_cursor.fetchall()
            submissions = []
            if results[5] == 'online' or results[5] == 'offline':
                # extract online text
                for sub in sub_results:
                    # grab name of student from db
                    self.db_cursor.execute(
                        'SELECT firstname,lastname FROM users WHERE userid=?', (sub[1],))
                    user = self.db_cursor.fetchone()
                    username = user[0] + " " + user[1]

                    # grab name of teacher from db
                    self.db_cursor.execute(
                        'SELECT firstname,lastname FROM users WHERE userid=?', (sub[6],))
                    teacher = self.db_cursor.fetchone()
                    if teacher is not None:
                        grader = teacher[0] + " " + teacher[1]
                    else:
                        grader = ""

                    # construct submission
                    submissions.append({'id': sub[0],
                                        'user': username,
                                        'timemodified': datetime.fromtimestamp(sub[2]),
                                        'data': sub[3],
                                        'grade': sub[4],
                                        'comment': sub[5],
                                        'teacher': grader,
                                        'timemarked': sub[7]})
                template = self.env.get_template('online_text.html')
                output = template.render(name=results[3],
                                         intro=results[4],
                                         student_data=self.student_data,
                                         submissions=submissions)
                os.chdir(path)
                with open('assignment.html', 'w+') as f:
                    f.write(output)
                    f.close()
            elif results[5] == 'upload' or results[5] == 'uploadsingle':

                for sub in sub_results:
                    # grab name of student from db
                    self.db_cursor.execute(
                        'SELECT firstname,lastname FROM users WHERE userid=?', (sub[1],))
                    user = self.db_cursor.fetchone()
                    username = user[0] + " " + user[1]

                    # grab name of teacher from db
                    self.db_cursor.execute(
                        'SELECT firstname,lastname FROM users WHERE userid=?', (sub[6],))
                    teacher = self.db_cursor.fetchone()
                    if teacher is not None:
                        grader = teacher[0] + " " + teacher[1]
                    else:
                        grader = ""

                    # construct submission
                    submissions.append({'id': sub[0],
                                        'user': username,
                                        'timemodified': datetime.fromtimestamp(sub[2]),
                                        'grade': sub[4],
                                        'comment': sub[5],
                                        'teacher': grader,
                                        'timemarked': sub[7]})

                    # grab all files submitted by this student
                    self.db_cursor.execute(
                        'SELECT contenthash,contextid,filename,userid FROM files WHERE userid=? AND contextid=?', (sub[1], results[2]))
                    files = self.db_cursor.fetchall()
                    submitted_files = []
                    if files is not None:
                        for f in files:
                            os.chdir(self.temp_dir)
                            if not os.path.exists(os.path.join(path, username)):
                                os.makedirs(os.path.join(path, username))
                            self.backup.extract_file(
                                f[0], os.path.join(path, username, f[2]))
                            # construct file list
                            submitted_files.append(
                                {'url':os.path.join(username, f[2]), 'filename': f[2]})

                # write the output assignment.html
                template = self.env.get_template('upload.html')
                output = template.render(name=results[3],
                                         intro=results[4],
                                         student_data=self.student_data,
                                         submissions=submissions,
                                         files=submitted_files)
                os.chdir(path)
                f = open('assignment.html', 'w+')
                f.write(output)
                f.close()

        else:
            template = self.env.get_template('no-submissions.html')
            output = template.render(name=results[3],
                                     intro=results[4],
                                     student_data=self.student_data)
            os.chdir(path)
            with open('assignment.html', 'w+') as f:
                f.write(output)
                f.close()
