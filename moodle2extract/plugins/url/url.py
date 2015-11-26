import os
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

        # create database table for this resource
        query = "CREATE TABLE IF NOT EXISTS urls (activityid int PRIMARY KEY, moduleid int, contextid int, name text, url text)"
        self.db_cursor.execute(query)
        self.db.commit()

    def parse(self):
        self.url_xml = et.parse(self.backup.open(self.directory+"/url.xml")).getroot()
        self.inforef_xml = et.parse(self.backup.open(self.directory+"/inforef.xml")).getroot()

        url = (self.url_xml.get('id'),
            self.url_xml.get('moduleid'),
            self.url_xml.get('contextid'),
            self.url_xml.find('./url/name').text,
            self.url_xml.find('./url/externalurl').text)

        self.db_cursor.execute('INSERT INTO urls VALUES(?,?,?,?,?)', url)
        self.db.commit()

    def extract(self):

        # create the folder for the urls to be extracted to
        if os.path.exists(os.path.join(self.final_dir,self.backup.stripped(self.url_xml.find('./url/name').text))) == False:
            os.makedirs(os.path.join(self.final_dir,self.backup.stripped(self.url_xml.find('./url/name').text)))
        os.chdir(os.path.join(self.final_dir,self.backup.stripped(self.url_xml.find('./url/name').text)))

        # write a .url file
        f = open(self.backup.stripped(self.url_xml.find('./url/name').text)+".url",'w')
        f.write("[InternetShortcut]\nURL="+self.url_xml.find('.url/externalurl').text)
        f.close()

        # write a .desktop file for linux users
        f = open(self.backup.stripped(self.url_xml.find('./url/name').text)+".desktop",'w')
        f.write("[Desktop Entry]\nName="+self.url_xml.find('./url/name').text+"\nEncoding=UTF-8\nType=Link\nIcon=text-html\nURL="+self.url_xml.find('.url/externalurl').text)
        f.close()

        # write a file explaining what's going on
        f = open("readme.txt",'w')
        f.write('The original url was:'+self.url_xml.find('./url/externalurl').text+'\n\nThe .url file should open the web page for this link when you double click on it. Use the .desktop file if you are on Linux instead.\n\nNote that if the website for this link is no longer online, you will not be able to open it.')
        f.close()
