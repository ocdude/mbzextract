import os
import xml.etree.ElementTree as et
import re
from html.parser import HTMLParser
from datetime import datetime
from jinja2 import Environment, PackageLoader

class moodle_module:
    def __init__(self,backup_file,temp_dir,db,directory,working_dir,student_data=False):
        self.backup = backup_file
        self.temp_dir = temp_dir
        self.db = db
        self.db_cursor = self.db.cursor()
        self.directory = directory
        self.files = []
        self.final_dir = working_dir

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
        print('\tName:',self.url_xml.find('./url/name').text)
        print('\tURL:',self.url_xml.find('./url/externalurl').text)

    def extract(self):

        # create the folder for the urls to be extracted to
        if os.path.exists(self.final_dir+"/"+self.stripped(self.url_xml.find('./url/name').text)+"_url") == False:
            os.makedirs(self.final_dir+"/"+self.stripped(self.url_xml.find('./url/name').text)+"_url")
        os.chdir(self.final_dir+"/"+self.stripped(self.url_xml.find('./url/name').text)+"_url")

        # write a .url file
        f = open(self.stripped(self.url_xml.find('./url/name').text)+".url",'w')
        f.write("[InternetShortcut]\nURL="+self.url_xml.find('.url/externalurl').text)
        f.close()

        # write a .desktop file for linux users
        f = open(self.stripped(self.url_xml.find('./url/name').text)+".desktop",'w')
        f.write("[Desktop Entry]\nName="+self.url_xml.find('./url/name').text+"\nEncoding=UTF-8\nType=Link\nIcon=text-html\nURL="+self.url_xml.find('.url/externalurl').text)
        f.close()

        # write a file explaining what's going on
        f = open("readme.txt",'w')
        f.write('The original url was:'+self.url_xml.find('./url/externalurl').text+'\n\nThe .url file should open the web page for this link when you double click on it. Use the .desktop file if you are on Linux instead.\n\nNote that if the website for this link is no longer online, you will not be able to open it.')
        f.close()

    def stripped(self,x):
        the_string = "".join([i for i in x if 31 < ord(i) < 127])
        the_string = the_string.strip()
        the_string = re.sub(r'[^\w]','_',the_string)
        return the_string
