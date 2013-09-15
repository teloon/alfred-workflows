#!/usr/bin/env python
#-*- coding:utf-8 -*-

import chardet
import cPickle as pickle
import os
import re
import requests
import sqlite3
import sys
import HTMLParser

from datetime import datetime
from Feedback import Feedback
from lxml import etree

DB_FN = "datas.db"
PICKLE_FN = "datas.pkl"
HEADERS = {"User-Agent": "Mozilla/5.0",
           "HOST": "api.del.icio.us",
           }
LAST_TIME_FN = "last_time.txt"
USR, PASSWD = "", ""

def fetch():
    r = requests.get("https://api.del.icio.us/v1/posts/all", auth=(USR, PASSWD), headers=HEADERS)
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
        url = post.get("href")
        if tag not in data_dic:
            data_dic[tag] = []
        data_dic[tag].append({"url": url, "desc": desc, "time": time})

    with open(LAST_TIME_FN, "w") as f:
        f.write(last_time + "\n")
        f.write(datetime.now().strftime("%y/%m/%d"))
    pickle.dump(data_dic, open(PICKLE_FN, "wb"))

def create_table(cursor):
    cursor.execute("""CREATE TABLE bookmark(
                 id INTEGER PRIMARY KEY,
                 url TEXT UNIQUE NOT NULL,
                 description TEXT,
                 time TEXT
                 )""")
    cursor.execute("""CREATE TABLE tags(
                 id INTEGER PRIMARY KEY,
                 bid INTEGER,
                 tag TEXT NOT NULL,
                 FOREIGN KEY(bid) REFERENCES bookmark(id)
                 )""")

def drop_table(cursor):
    cursor.execute("""drop TABLE bookmark""")
    cursor.execute("""drop TABLE tags""")

def save_to_db():
    data_dic = pickle.load(open(PICKLE_FN, "rb"))
    conn = sqlite3.connect(DB_FN)
    c = conn.cursor()
    drop_table(c)
    create_table(c)
    bm_cnter = 1
    for tags, bms in data_dic.items():
        for bm in bms:
            desc = sanitize_sql(bm["desc"])
            sql = "INSERT INTO bookmark(url, description, time) VALUES('%s', '%s', '%s')" % (bm["url"], desc, bm['time'])
            c.execute(sql)
            for tag in tags.strip().split():
                re.sub("'", "''", tag)
                c.execute("INSERT INTO tags(bid, tag) VALUES(%d, '%s')" % (bm_cnter, tag))
            bm_cnter += 1

    conn.commit()
    conn.close()

def dump_data():
    fetch()
    save_to_db()

def sanitize_sql(s):
    return re.sub(r"'", r"''", s)

def filtering(tag_lst):
    tag_lst[:] = map(sanitize_sql, tag_lst)
    tags = "'" + "', '".join(tag_lst) + "'"
    sql = """SELECT bm.*
             FROM bookmark bm, tags t
             WHERE (t.tag IN (%s))
             AND t.bid=bm.id
             GROUP BY bm.id
             HAVING COUNT(bm.id)=%d
    """ % (tags, len(tag_lst))
    conn = sqlite3.connect(DB_FN)
    c = conn.cursor()
    fb = Feedback()
    parser = HTMLParser.HTMLParser()
    for bid, url, desc, tm in c.execute(sql):
        fb.add_item("""%s""" % parser.unescape(desc),
                    subtitle="""%s""" % url,
                    uid=bid,
                    arg=url)
    print fb

def parse_time(ts):
    mat = re.match("(.+)T(.+)Z", ts)
    day, t = mat.group(1), mat.group(2)
    y, m, d = map(int, re.findall("(\d+)", day))
    hr, mnt, sec =map(int, t.split(":"))
    dt = datetime(y, m, d, hr, mnt, sec)
    return dt

def need_update():
    if not os.path.exists(LAST_TIME_FN):
        return True
    last_time = ""
    with open(LAST_TIME_FN) as f:
        last_time = f.readline().strip()
        last_time_query = f.readline().strip()
    with open(LAST_TIME_FN, "w") as f:
        f.write(last_time + "\n")
        f.write(datetime.now().strftime("%y/%m/%d"))
    last_time_query = datetime.strptime(last_time_query, "%y/%m/%d")
    if last_time_query.date() == datetime.now().date():
        return False
    dt = parse_time(last_time)
    r = requests.get("https://api.del.icio.us/v1/posts/update", auth=(USR, PASSWD), headers=HEADERS)
    parser = etree.XMLParser()
    parser.feed(r.text)
    root = parser.close()
    curr_last_time = root.get("time")
    curr_dt = parse_time(curr_last_time)
    if curr_dt > dt:
        return True
    return False

if __name__ == '__main__':
    global USR, PASSWD
    if len(sys.argv) >= 4:
        tags, USR, PASSWD = sys.argv[1], sys.argv[2], sys.argv[3]
        if need_update():
            dump_data()
        filtering(tags.strip().split())
