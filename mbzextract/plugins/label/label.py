import os
import shutil
from jinja2 import Environment, PackageLoader
import html
import xml.etree.ElementTree as et


class moodle_module:

    def __init__(self, **kwargs):
        self.backup = kwargs['backup']
        self.temp_dir = kwargs['temp_dir']
        self.db = kwargs['db']
        self.directory = kwargs['directory']
        self.final_dir = kwargs['working_dir']
        self.db_cursor = self.db.cursor()

        query = "CREATE TABLE IF NOT EXISTS labels (activityid int, moduleid int, contextid int, name text, content text)"
        self.db_cursor.execute(query)
        self.db.commit()
        self.env = Environment(loader=PackageLoader(
            'mbzextract.plugins.label', 'templates'))

    def parse(self):
        label_xml = et.parse(self.backup.open(
            self.directory + "/label.xml")).getroot()
        inforef_xml = et.parse(self.backup.open(
            self.directory + "/inforef.xml")).getroot()

        label = (label_xml.get('id'),
                    label_xml.get('moduleid'),
                    label_xml.get('contextid'),
                    label_xml.find('./label/name').text,
                    html.unescape(label_xml.find('./label/intro').text))

        self.name = label_xml.find('./label/name').text
        self.db_cursor.execute(
            "INSERT INTO labels VALUES(?,?,?,?,?)", label)
        self.db.commit()
        self.current_id = label_xml.get('id')

        # create a list of files
        self.files = self.backup.list_files(inforef_xml, self.db_cursor)

    def extract(self):
        self.db_cursor.execute('SELECT name,content FROM labels WHERE activityid=?',(self.current_id,))
        results = self.db_cursor.fetchone()
        template = self.env.get_template('label.html')
        output = (template.render(name=results[0],content=results[1]))

        path = os.path.join(self.final_dir, self.backup.stripped(self.name))
        if os.path.exists(path) == False:
            os.makedirs(path)
        os.chdir(path)

        # write the label
        f = open("label.html",'w+')
        f.write(output)
        f.close()

        # files
        for fileid in self.files:
            self.db_cursor.execute(
                'SELECT contenthash,filename FROM files WHERE filename != "." AND id=?', (fileid,))
            results = self.db_cursor.fetchone()
            if results is not None:
                os.chdir(self.temp_dir)
                self.backup.extract_file(
                    results[0], os.path.join(path, results[1]))
