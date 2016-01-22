import os
import shutil
import xml.etree.ElementTree as et


class moodle_module:

    def __init__(self, **kwargs):
        self.backup = kwargs['backup']
        self.temp_dir = kwargs['temp_dir']
        self.db = kwargs['db']
        self.directory = kwargs['directory']
        self.final_dir = kwargs['working_dir']
        self.db_cursor = self.db.cursor()

        query = "CREATE TABLE IF NOT EXISTS folders (activityid int, moduleid int, contextid int, name text)"
        self.db_cursor.execute(query)
        self.db.commit()

    def parse(self):
        folder_xml = et.parse(self.backup.open(
            self.directory + "/folder.xml")).getroot()
        inforef_xml = et.parse(self.backup.open(
            self.directory + "/inforef.xml")).getroot()

        folder = (folder_xml.get('id'),
                    folder_xml.get('moduleid'),
                    folder_xml.get('contextid'),
                    folder_xml.find('./folder/name').text)

        self.name = folder_xml.find('./folder/name').text
        self.db_cursor.execute(
            "INSERT INTO folders VALUES(?,?,?,?)", folder)
        self.db.commit()

        # create a list of files
        self.files = self.backup.list_files(inforef_xml, self.db_cursor)

    def extract(self):
        path = os.path.join(self.final_dir, self.backup.stripped(self.name))
        if os.path.exists(path) == False:
            os.makedirs(path)
        os.chdir(path)
        for fileid in self.files:
            self.db_cursor.execute(
                'SELECT contenthash,filename FROM files WHERE filename != "." AND id=?', (fileid,))
            results = self.db_cursor.fetchone()
            if results is not None:
                os.chdir(self.temp_dir)
                self.backup.extract_file(
                    results[0], os.path.join(path, results[1]))
