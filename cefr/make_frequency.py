#-*- encoding: utf-8 -*-
# calculate word frequencies for prepating sub-level for cefr 6 levels

import sqlite3
import re
import os, sys
import pdb
import random

reload(sys)
sys.setdefaultencoding('utf-8')

def create_connection(db_file):
  try:
    conn = sqlite3.connect(db_file)
    return conn
  except sqlite3.Error as e:
    print(e)
    pdb.set_trace()
  return None

# select level, count(*) from words_bymeaning group by level;
# A1 780, A2 1567, B1 2806, B2 3904, C1 2318, C2 3633
# select word, frequency from words_bymeaning where level = 'A1' order by frequency desc limit 780/10*0, 1;
def get_frequencies(conn):
  sql = 'select level, count(*) from words_bymeaning group by level;'
  cur = conn.cursor()
  cur.execute(sql)
  rows = cur.fetchall()

  for row in rows:
    level = row[0]
    count = row[1]
    frequencies = []
    for i in range(0,10):
      sql = "select word, frequency from words_bymeaning where level = '" + level \
        + "' order by frequency desc limit " + str(count) + "/10*" + str(i) + ", 1;"
      cur = conn.cursor()
      cur.execute(sql)
      rows = cur.fetchall()
      frequencies.append(rows[0][1])
    sys.stdout.write(level.lower() + "_freq = [")
    for f in frequencies:
      sys.stdout.write(str(f) + ", ")
    sys.stdout.write("0]\n")
    sys.stdout.flush()

if __name__ == "__main__":
  dbfile = "/home/koo/english/cefr/cefr.db"
  conn = create_connection(dbfile)
  get_frequencies(conn)
  conn.close()
