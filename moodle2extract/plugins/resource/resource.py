import os
import shutil
import xml.etree.ElementTree as et

class moodle_module:
    def __init__(self,**kwargs):
        self.backup = kwargs['backup']
        self.temp_dir = kwargs['temp_dir']
        self.db = kwargs['db']
        self.directory = kwargs['directory']
        self.final_dir = kwargs['working_dir']
        self.db_cursor = self.db.cursor()
        self.files = []

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
        path = os.path.join(self.final_dir,self.backup.stripped(self.name))
        if os.path.exists(path) == False:
            os.makedirs(path)
        os.chdir(path)
        for fileid in self.files:
            self.db_cursor.execute('SELECT contenthash,filename FROM files WHERE filename != "." AND id=?',(fileid,))
            results = self.db_cursor.fetchone()
            if results is not None:
                os.chdir(self.temp_dir)
                self.backup.extract_file(results[0],os.path.join(path,results[1]))
