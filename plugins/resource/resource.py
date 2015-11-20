import os
import re
import shutil
import xml.etree.ElementTree as et

class moodle_module:
    def __init__(self,backup_file,temp_dir,db,directory,working_dir,student_data=False):
        self.backup = backup_file
        self.temp_dir = temp_dir
        self.db = db
        self.db_cursor = self.db.cursor()
        self.directory = directory
        self.files = []
        self.final_dir = working_dir

        query = "CREATE TABLE IF NOT EXISTS resources (activityid int, moduleid int, contextid int, name text)"
        self.db_cursor.execute(query)
        self.db.commit()

    def parse(self):
        resource_xml = et.parse(self.backup.open(self.directory+"/resource.xml")).getroot()
        inforef_xml = et.parse(self.backup.open(self.directory+"/inforef.xml")).getroot()

        resource = (resource_xml.get('id'),
            resource_xml.get('moduleid'),
            resource_xml.get('contextid'),
            resource_xml.find('./resource/name').text)
        self.name = resource_xml.find('./resource/name').text
        self.db_cursor.execute("INSERT INTO resources VALUES(?,?,?,?)",resource)
        self.db.commit()
        print('\tName:',resource_xml.find('./resource/name').text)

        # create a list of files
        if inforef_xml.find('fileref') is not None:
            for f in inforef_xml.findall('./fileref/file'):
                self.files.append(f.find('id').text)
        print('\tNumber of files:',len(self.files))

    def extract(self):
        path = self.final_dir + "/" + self.stripped(self.name) + "/files"
        if os.path.exists(path) == False:
            os.makedirs(path)
        os.chdir(path)
        for fileid in self.files:
            self.db_cursor.execute('SELECT contenthash,filename FROM files WHERE filename != "." AND id=?',(fileid,))
            results = self.db_cursor.fetchone()
            if results is not None:
                os.chdir(self.temp_dir)
                self.backup.extract('files/'+results[0][:2]+'/'+results[0])
                shutil.move(self.temp_dir+"/files/"+results[0][:2]+"/"+results[0],path + "/" + results[1])


    def stripped(self,x):
        the_string = "".join([i for i in x if 31 < ord(i) < 127])
        the_string = the_string.strip()
        the_string = re.sub(r'[^\w]','_',the_string)
        return the_string
