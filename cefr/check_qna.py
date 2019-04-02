#-*- encoding: utf-8 -*-
# rule check for qna
# rule1: example should be a sentence and must contain the headword or its inflection

import sqlite3
import re
import os, sys
import pdb
import random
from parse_cefr import is_sentence
sys.path.append("../english-inflection")
from get_conjugation import get_conjugation
from get_plural import get_plural
from get_comparative import get_comparative

reload(sys)
sys.setdefaultencoding('utf-8')

def remove_punctuation(word):
  removed = ""
  for ch in word:
    if ch not in ['"', "'", ',', '?', '!', '.', '-']:
      removed += ch
    elif removed != "":
      break
  return removed

# when a word is explained by itself
def bad_meaning(word, pos, meaning):
  inflections = get_inflections(word, pos)
  if meaning.count(word) > 0 and (meaning.startswith("If") or meaning.startswith("if")):
    print "meaning is not useful:", word, ">", meaning
    return True
  else:
    tokens = meaning.split(" ")
    for token in tokens:
      if token in inflections:
        print "meaning may not be useful:", word, ">", meaning
        return True
  return False

def remove_front_paren(meaning):
  if meaning.startswith("("):
    meaning = re.sub(r'\(.*\)', '', meaning)
  return meaning.strip()

def get_1pos(pos):
  tokens = pos.split(";")
  if len(tokens) == 1:
    return pos + "%"
  else:
    return tokens[1].strip() + "%"

def create_connection(db_file):
  try:
    conn = sqlite3.connect(db_file)
    return conn
  except sqlite3.Error as e:
    print(e)
    pdb.set_trace()
  return None

def select_words(conn, page):
  sql = "select word, pos, synopsis, meaning, example1, example2 from words_bymeaning order by id limit " + str(page) + ", 10;"
  try:
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
  except sqlite3.Error as e:
    print(e)

  return rows

def has_headword(word, pos, example):
  if word.count(" ") > 0 or word.count("-") > 0 or word.count(".") > 0:
    if example.lower().count(word.lower()) > 0:
      return True
    else:
      return False
  else:
    tokens = example.split(" ")
    for token in tokens:
      if remove_punctuation(token).lower() == word.lower():
        return True
    return False

# result includes the word itself
def get_inflections(word, pos=None):
  result = [word]
  if word == "a":
    result.append("an")
  if pos == None or pos.startswith("NOUN") or pos.startswith("NUMBER"):
    inflections = get_plural(word)[1]
    for inflection in inflections: result.append(inflection[3:])
  if pos == None or pos.startswith("AD") or pos.startswith("DETER"):
    inflections = get_comparative(word)[1]
    for inflection in inflections: result.append(inflection[3:])
  if pos == None or pos.startswith("VERB") or pos.startswith("AUXILIARY VERB") or pos.startswith("MODAL VERB"):
    inflections = get_conjugation(word)[1]
    for inflection in inflections: result.append(inflection[3:])
  return result

# return the found inflection
def find_inflected(word, pos, line):
  inflections = get_inflections(word, pos)
  for inflection in inflections:
    if has_headword(inflection, pos, line):
      return inflection
  return ""

# example should have word or inflected word
def find_example(word, pos, lines):
  inflection = ""
  found = ""
  example = ""
  for line in lines:
    if not is_sentence(line): continue
    if has_headword(word, pos, line):
      found = word
      example = line
      break
    else:
      found = find_inflected(word, pos, line)
      if found != "":
        print "found inflected", word, found
        example = line
        break
  if example == "":
    print "cannot find a good example:", word, pos, ">", lines
    print ""
  return found, example

def check_qna():
  dbfile = "/home/koo/english/cefr/cefr.db"
  conn = create_connection(dbfile)

  page = 0
  while True:
    rows = select_words(conn, page)
    page += 10
    for row in rows:
      word = row[0]
      pos = row[1]
      synopsis = row[2]
      meaning = row[3]
      example1 = row[4]
      example2 = row[5]
      if pos.startswith("PHRASE"):
        pos = pos[8:]
        word = synopsis
      found, example = find_example(word, pos, [example1, example2])
      if example == "":
        print word, pos, meaning, example1, example2
        pdb.set_trace()

  conn.close()
  return qnas

if __name__ == "__main__":
  check_qna()

