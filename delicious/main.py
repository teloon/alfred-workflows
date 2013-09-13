#!/usr/bin/env python
#-*- coding:utf-8 -*-

import chardet
import re
import requests
import sqlite3
import cPickle as pickle

from lxml import etree
from pprint import pprint

DB_FN = "datas.db"
PICKLE_FN = "datas.pkl"
HEADERS = {"User-Agent": "Mozilla/5.0",
           "HOST": "api.del.icio.us",
           }

def fetch(usr, passwd):
    print "getting contents"
    r = requests.get("https://api.del.icio.us/v1/posts/all", auth=(usr, passwd), headers=HEADERS)
    print "got contents"
    if len(r.text) == 0:
        return
    parser = etree.XMLParser()
    parser.feed(r.text)
    root = parser.close()
    last_time = root[0].get("time")
    data_dic = {}
    """
        {
            tag: [
                    {
                        url: ...,
                        desc: ...,
                        time: ...,
                    },
                    ...
                ],
            ...
        }
    """
    for post in root:
        tag = post.get("tag")
        desc = post.get("description")
        time = post.get("time")
 #       print desc, chardet.detect(desc)
 #       desc = desc.decode(chardet.detect(desc)['encoding'])
 #       print desc
        url = post.get("href")
        if tag not in data_dic:
            data_dic[tag] = []
        data_dic[tag].append({"url": url, "desc": desc, "time": time})

    #pprint(data_dic)
    #pprint(last_time)
    pickle.dump(data_dic, open(PICKLE_FN, "wb"))

def create_table(cursor):
    print "creating table bookmark"
    cursor.execute("""CREATE TABLE bookmark(
                 id INTEGER PRIMARY KEY,
                 url TEXT UNIQUE NOT NULL,
                 description TEXT,
                 time TEXT
                 )""")
    print "creating table tags"
    cursor.execute("""CREATE TABLE tags(
                 id INTEGER PRIMARY KEY,
                 bid INTEGER,
                 tag TEXT NOT NULL,
                 FOREIGN KEY(bid) REFERENCES bookmark(id)
                 )""")

def drop_table(cursor):
    print "droping table bookmark"
    cursor.execute("""drop TABLE bookmark""")
    print "droping table tags"
    cursor.execute("""drop TABLE tags""")

def save_to_db():
    data_dic = pickle.load(open(PICKLE_FN, "rb"))
    conn = sqlite3.connect(DB_FN)
    c = conn.cursor()
    drop_table(c)
    create_table(c)
    print "inserting data"
    bm_cnter = 1
    for tags, bms in data_dic.items():
        for bm in bms:
            desc = re.sub(r"'", r"''", bm["desc"])
            sql = "INSERT INTO bookmark(url, description, time) VALUES('%s', '%s', '%s')" % (bm["url"], desc, bm['time'])
            c.execute(sql)
            for tag in tags.strip().split():
                re.sub("'", "''", tag)
                c.execute("INSERT INTO tags(bid, tag) VALUES(%d, '%s')" % (bm_cnter, tag))
            bm_cnter += 1

    conn.commit()
    conn.close()

    #pprint(data_dic)


if __name__ == '__main__':
    #usr = raw_input("username: ")
    #passwd = raw_input("password: ")
    #fetch(usr, passwd)
    save_to_db()
