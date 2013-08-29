#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
import sys

def parse(cmd):
    c_lst = cmd.strip().split()
    c, args = c_lst[0], c_lst[1:]
    url = "http://www.explainshell.com/explain/%s?args=%s" % (c, "+".join(args))
    os.system("open %s" % url)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        query = sys.argv[1]
        parse(query)
