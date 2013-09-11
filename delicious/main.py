#!/usr/bin/env python
#-*- coding:utf-8 -*-

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
                    },
                    ...
                ],
            ...
        }
    """
    for post in root:
        tag = post.get("tag")
        desc = post.get("desc")
        url = post.get("href")
        if tag not in data_dic:
            data_dic[tag] = []
        data_dic[tag].append({"url": url, "desc": desc})

    #pprint(data_dic)
    #pprint(last_time)
    pickle.dump(data_dic, open(PICKLE_FN, "wb"))

def save_to_db():
    data_dic = pickle.load(open(PICKLE_FN, "rb"))
    conn = sqlite3.connect(DB_FN)
    c = conn.cursor()
    c.execute()

    pprint(data_dic)


if __name__ == '__main__':
    #usr = raw_input("username: ")
    #passwd = raw_input("password: ")
    #fetch(usr, passwd)
    save_to_db()
