#-*- encoding: utf-8 -*-
# make questions from the database with given input level
# schema word_bymeanings : mid(pk), frequency(index), word(not null), pos(not null), meaning(not null), synopsis, examples
# schema us_bymeanings : uid(pk), mid(fk), us_word(not null)
# word of the question should be provided only once while testing

import random
import sqlite3
import re
import os, sys
import pdb
from parse_cefr import is_sentence
if __name__ == "__main__":
  sys.path.append("../english-inflection")
  from get_conjugation import get_conjugation
  from get_plural import get_plural
  from get_comparative import get_comparative
else:
  from english_inflection.get_conjugation import get_conjugation
  from english_inflection.get_plural import get_plural
  from english_inflection.get_comparative import get_comparative

reload(sys)
sys.setdefaultencoding('utf-8')

# contractions that should be applied at first
contractions1 = {
    "won't": 'will not',
    "can't": 'can not',
  }

contractions2_words = [
    "can", "could",
    "will", "would",
    "shall", "should",
    "have", "had", 
    "be",
    "not",
  ]
contractions2 = {
    "n't": ' not',
    "'ve": ' have',
    "'re": ' are',
    "'m": ' am',
  }

contractions3 = {
    "would": ["'d", " would"],
    "had": ["'d", " had"],
    "will": ["'ll", " will"],
    "shall": ["'ll", " shall"], 
    "be": ["'s", " is"],
    "have": ["'s", " has"],
    }

def make_log(string):
  pass
  #with open("/home/koo/english/cefr/make_qna.log", "a") as lf:
  #  lf.write(string + '\n')

# replace only when headword is in the text
def replace_contractions(word, text):
  for cont in contractions1:
    if contractions1[cont].count(word) > 0:
      text = text.replace(cont, contractions1[cont])
  for cont in contractions2:
    if word in contractions2_words > 0:
      text = text.replace(cont, contractions2[cont])
  if word in contractions3:
    text = text.replace(contractions3[word][0], contractions3[word][1])
  return text

def remove_punctuation(word):
  removed = ""
  for ch in word:
    if ch not in ['"', ',', '?', '!', '.', '-']:  # keep ' for o'clock (- for make-up, . for a.m.)
      removed += ch
    elif removed != "":
      break
  return removed

# when a word is explained by itself
def bad_meaning(word, pos, meaning):
  if word in ['be']: return False # meaning for be should be checked manually
  inflections, inf_tags = get_inflections(word.lower(), pos)
  if meaning.lower().count(word.lower()) > 0 and (meaning.startswith("If") or meaning.startswith("if")):
    print "meaning is not useful:", word, ">", meaning
    return True
  else:
    tokens = meaning.split(" ")
    for token in tokens:
      if token.lower() in inflections:
        print "meaning may not be useful:", word, ">", meaning
        return True
  return False

def remove_front_paren(meaning):
  if meaning.startswith("("):
    meaning = re.sub(r'\(.*\)', '', meaning)
  return meaning.strip()

# why the second pos?
def get_1pos(pos):
  tokens = pos.split(";")
  if len(tokens) == 1:
    return pos + "%"
  elif tokens[0] == 'PHRASE':
    return tokens[1].strip() + "%"
  else:
    print pos, tokens[0].strip() + "%"
    return tokens[0].strip() + "%"

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
def get_frequencies(level, sub_level):
  a1_freq = [23135851162, 950751722, 371852748, 215178488, 142014927, 92709785, 60054650, 35595812, 20976724, 8267976, 0]
  a2_freq = [23135851162, 391577361, 191963867, 102234743, 64112042, 39701600, 21926890, 12459909, 5666591, 1708851, 0]
  b1_freq = [23135851162, 210601244, 102234743, 56063953, 35383071, 21156261, 12539579, 6863738, 3503935, 1083379, 0]
  b2_freq = [23135851162, 107853068, 52029690, 30095341, 17372103, 10519219, 6528999, 3654922, 1765968, 450571, 0]
  c1_freq = [13151942776, 59154507, 26457942, 13443395, 7193446, 4505086, 2748376, 1618749, 767668, 236617, 0]
  c2_freq = [8469404971, 40345803, 14971773, 7037352, 3654411, 1876379, 1102986, 500872, 176385, 9806, 0]
  if level == 'A1':
    freq_max = a1_freq[sub_level-1]
    freq_min = a1_freq[sub_level]
  elif level == 'A2':
    freq_max = a2_freq[sub_level-1]
    freq_min = a2_freq[sub_level]
  elif level == 'B1':
    freq_max = b1_freq[sub_level-1]
    freq_min = b1_freq[sub_level]
  elif level == 'B2':
    freq_max = b2_freq[sub_level-1]
    freq_min = b2_freq[sub_level]
  elif level == 'C1':
    freq_max = c1_freq[sub_level-1]
    freq_min = c1_freq[sub_level]
  elif level == 'C2':
    freq_max = c2_freq[sub_level-1]
    freq_min = c2_freq[sub_level]
  return freq_max, freq_min

# qtype1, qtype2
# columns = [level, freq_max, freq_min]
def select_questions(conn, columns, count):
  sql = "select distinct(word) from words_bymeaning where " + \
    "level = ? and pos not like 'PHRASE%' and frequency < ? and frequency >= ? order by random() limit " + str(count) + ";"
  try:
    cur = conn.cursor()
    cur.execute(sql, columns)
    rows = cur.fetchall()
  except sqlite3.Error as e:
    print(e)

  return rows

# columns = [level, freq_max, freq_min]
def select_questions_q3(conn, columns, count):
  sql = "select distinct(word) from words_bymeaning where " + \
    "level = ? and pos not like 'PHRASE%' and frequency < ? and frequency >= ? order by random() limit " + str(count) + ";"
  try:
    cur = conn.cursor()
    cur.execute(sql, columns)
    rows = cur.fetchall()
  except sqlite3.Error as e:
    print(e)

  return rows

# columns = [level, freq_max, freq_min]
def select_questions_q4(conn, columns, count):
  sql = "select distinct(word) from words_bymeaning where " + \
    "level = ? and frequency < ? and frequency >= ? order by random() limit " + str(count) + ";"
  #sql = 'select word from words_bymeaning where word like "%o' + "'clock" + '";'
  try:
    cur = conn.cursor()
    cur.execute(sql, columns)
    #cur.execute(sql)
    rows = cur.fetchall()
  except sqlite3.Error as e:
    print(e)

  return rows

# columns = [level, word]
def select_1answer(conn, columns):
  sql = "select pos, meaning, example1, example2, synopsis from words_bymeaning where " + \
    "level = ? and word = ? order by random()"
  try:
    cur = conn.cursor()
    cur.execute(sql, columns)
    rows = cur.fetchall()
  except sqlite3.Error as e:
    print(e)

  return rows

# input columns = [level, word]
def select_1answer_q3(conn, columns):
  sql = "select pos, meaning, example1, example2 from words_bymeaning where " + \
    "level >= ? and word = ? order by random()"
  try:
    cur = conn.cursor()
    cur.execute(sql, columns)
    rows = cur.fetchall()
  except sqlite3.Error as e:
    print(e)

  return rows

# input columns = [level, pos, word]
def select_2wrong(conn, columns):
  sql = "select word, pos, meaning, example1, example2 from words_bymeaning where " + \
    "level = ? and pos like ? and word != ? order by random() limit 2;"
  try:
    cur = conn.cursor()
    cur.execute(sql, columns)
    rows = cur.fetchall()
  except sqlite3.Error as e:
    print(e)

  if len(rows) < 2:
    print "cannot find 2 wrong answers", word
    pdb.set_trace()

  return rows

# input columns = [level, pos, word]
# output = [(word, pos, meaning, examples)]
def select_2wrong_q2(conn, columns):
  word = columns[2]
  if len(word) < 2:
    word_postfix = word[-1]
  else:
    word_postfix = word[-2:]
  sql = "select distinct(word) from words_bymeaning where " + \
    "level = ? and word like '%" + word_postfix + "' and pos like ? and word != ? order by random() limit 2;"

  try:
    cur = conn.cursor()
    cur.execute(sql, columns)
    rows = cur.fetchall()
  except sqlite3.Error as e:
    print(e)

  if len(rows) < 2:
    sql = "select distinct(word) from words_bymeaning where " + \
      "level = ? and pos like ? and word != ? order by random() limit 2;"
    try:
      cur = conn.cursor()
      cur.execute(sql, columns)
      rows = cur.fetchall()
    except sqlite3.Error as e:
      print(e)
  return rows

# input columns = [level, pos, word]
def select_2wrong_q4(conn, columns):
  level = columns[0]
  pos = columns[1]
  word = columns[2]
  word_postfix = word[-1]
  if pos.startswith("NUMBER") or pos.startswith("EXCL") or \
    (level in ['A1', 'A2', 'B1', 'B2'] and (pos.startswith("AD") or pos.startswith("NOUN"))):
    sql = "select distinct(word) from words_bymeaning where " + \
      "level = ? and pos not like ? and pos not like 'PHRASE%' and word like '%" + word_postfix + "' and word != ? " + \
      "order by random() limit 2;"
  else:
    sql = "select distinct(word) from words_bymeaning where " + \
      "level = ? and pos like ? and word != ? order by random() limit 2;"
  try:
    cur = conn.cursor()
    cur.execute(sql, columns)
    rows = cur.fetchall()
  except sqlite3.Error as e:
    print(e)

  if len(rows) < 2:
    make_log("few result of wrong answers for " + word)
    if pos.startswith("NUMBER") or (level in ['A1', 'A2', 'B1', 'B2'] and (pos.startswith("AD") or pos.startswith("NOUN"))):
      sql = "select distinct(word) from words_bymeaning where " + \
        "level = ? and pos not like ? and pos not like 'PHRASE%' and word != ? order by random() limit 2;"
    else:
      sql = "select distinct(word) from words_bymeaning where " + \
        "level = ? and pos like ? and word != ? order by random() limit 2;"
    try:
      cur = conn.cursor()
      cur.execute(sql, columns)
      rows = cur.fetchall()
    except sqlite3.Error as e:
      print(e)
  return rows

# qnas = [word, pos, meaning, "", choices, a_index]
def print_qna_type1(qnas):
  print "Choose the closest description for the given word."
  print ""
  for qna in qnas:
    word = qna[0]
    choices = qna[4]
    print word
    for i in range(len(choices)):
      print str(i+1) + ".", choices[i]
    print ""

# qnas = [word, pos, meaning, "", choices, a_index]
def print_qna_type2(qnas):
  print "Choose a word that the following phrase is describing."
  print ""
  for qna in qnas:
    meaning = qna[2]
    choices = qna[4]
    print meaning
    for i in range(len(choices)):
      print str(i+1) + ".", choices[i]
    print ""

def mark_word_example(word, pos, example):
  inflections, inf_tags = get_inflections(word, pos)
  found = ""
  if word.count(" ") > 0 or word.count("-") > 0 or example.count("'") > 0:
    idx = example.lower().find(word.lower())
    if idx >= 0:
      found = remove_punctuation(example[idx:idx+len(word)])
  else:
    tokens = example.split(" ")
    for token in tokens:
      if remove_punctuation(token.lower()) in inflections or remove_punctuation(token) in inflections:
        found = remove_punctuation(token)
        break

  if found == "":
    return example + " (" + word + ")"
  else:
    return example.replace(found, "["+found+"]")

# qnas = [word, pos, meaning, example, choices, a_index]
def print_qna_type3(qnas):
  print "Choose the closest description for the word in the sentence."
  print ""
  for qna in qnas:
    word = qna[0]
    pos = qna[1]
    example = qna[3]
    choices = qna[4]
    print example
    for i in range(len(choices)):
      print str(i+1) + ".", choices[i]
    print ""

def blank_word_example(word, pos, example):
  inflections, inf_tags = get_inflections(word, pos)
  found = ""
  if word.count(" ") > 0 or word.count("-") > 0 or word.count("'") > 0:
    for inflection in inflections:
      idx = example.lower().find(inflection.lower())
      if idx >= 0:
        found = remove_punctuation(example[idx:idx+len(inflection)])
  else:
    tokens = example.replace('-', ' ').replace("'", ' ').replace("(", ' ').replace(")", ' ').replace(':', ' ').replace(';', ' ').split(" ")
    for token in tokens:
      if token in inflections or remove_punctuation(token.lower()) in inflections or remove_punctuation(token) in inflections:
        found = remove_punctuation(token)
        break
  if found == "": pdb.set_trace()
  if example.count(' ' + found + ' ') >= 1:
    return example.replace(' ' + found + ' ', " [ ___ ] "), found
  elif example.count(' ' + found) >= 1:
    return example.replace(' ' + found, " [ ___ ]"), found
  elif example.count(found + ' ') >= 1:
    return example.replace(found + ' ', "[ ___ ] "), found
  elif example.count(found + ',') >= 1:
    return example.replace(found + ',', "[ ___ ],"), found
  elif example.count(found + '!') >= 1:
    return example.replace(found + '!', "[ ___ ]!"), found
  elif example.count(found + '?') >= 1:
    return example.replace(found + '?', "[ ___ ]?"), found
  elif example.count(found + '.') >= 1:
    return example.replace(found + '.', "[ ___ ]."), found
  elif example.count(found + "'") >= 1:
    return example.replace(found + '.', "[ ___ ]'"), found
  elif example.count(found + '"') >= 1:
    return example.replace(found + '.', '[ ___ ]"'), found
  else:
    print "not found replaceable from", found, example
    pdb.set_trace()

# qnas = [word, pos, meaning, example, choices, a_index]
def print_qna_type4(qnas):
  print "Choose the best word that can be inserted into the marked position of the sentence."
  print ""
  for qna in qnas:
    example = qna[3]
    choices = qna[4]
    print example
    for i in range(len(choices)):
      print str(i+1) + ".", choices[i]
    print ""

def make_qna_type1(conn, level, sub_level, count):
  freq_max, freq_min = get_frequencies(level, sub_level)
  qrows = select_questions(conn, [level, freq_max, freq_min], count)
  qnas = []
  for qrow in qrows:
    word = qrow[0]
    arows = select_1answer(conn, [level, word])
    pos = get_1pos(arows[0][0])
    meaning = arows[0][1]
    if bad_meaning(word, pos, meaning): continue
    wrongs = select_2wrong(conn, [level, pos, word])
    choices = []
    for wrong in wrongs:
      choices.append(remove_front_paren(wrong[2]))
    a_index = random.randrange(0, len(wrongs)+1)
    choices.insert(a_index, remove_front_paren(meaning))
    qnas.append([word, pos, meaning, "", choices, a_index])
  return qnas

def make_qna_type2(conn, level, sub_level, count):
  freq_max, freq_min = get_frequencies(level, sub_level)
  qrows = select_questions(conn, [level, freq_max, freq_min], count)
  qnas = []
  for qrow in qrows:
    word = qrow[0]
    arows = select_1answer(conn, [level, word])
    pos = get_1pos(arows[0][0])
    meaning = arows[0][1]
    if bad_meaning(word, pos, meaning): continue

    meaning = remove_front_paren(meaning)
    wrongs = select_2wrong_q2(conn, [level, pos, word])
    choices = []
    for wrong in wrongs:
      choices.append(wrong[0])
    a_index = random.randrange(0, len(wrongs)+1)
    choices.insert(a_index, word)
    qnas.append([word, pos, meaning, "", choices, a_index])
  return qnas

def has_headword(word, example):
  if word.count(" ") > 0 or word.count("-") > 0 or word.count("'") > 0:
    if example.lower().count(word.lower()) > 0:
      return True
    else:
      return False
  else:
    tokens = example.replace('-', ' ').replace("'", ' ').replace('(', ' ').replace(')', ' ').replace(':', ' ').replace(';', ' ').split(" ")
    for token in tokens:
      if remove_punctuation(token).lower() == word.lower() or token.lower() == word.lower():
        return True
    return False

def conjugate(word, pos, tag):
  make_log("conjugate word:" + word + " pos:" + pos + " tag:" + tag)
  inflections, tags = get_inflections(word, pos)
  for inflection, inf_tag in zip(inflections, tags):
    if tag == inf_tag: return inflection
  return word

# result includes the word itself
def get_inflections(word, pos=None):
  result = [word]
  tags = ["IN"]
  if pos == None or pos.startswith("NOUN") or pos.startswith("NUMBER") or word == 'other':
    inflections = get_plural(word)[1] # [0] is singular, [1] is list of plurals
    for inflection in inflections:
      result.append(inflection[3:])
      tags.append(inflection[0:2])
  if pos == None or pos.startswith("AD") or pos.startswith("DETER"):
    inflections = get_comparative(word)[1]
    for inflection in inflections:
      result.append(inflection[3:])
      tags.append(inflection[0:2])
  if pos == None or pos.startswith("VERB") or pos.startswith("AUXILIARY VERB") or pos.startswith("MODAL VERB"):
    inflections = get_conjugation(word)[1]
    for inflection in inflections:
      result.append(inflection[3:])
      tags.append(inflection[0:2])
  if word == 'a':
    result.append('an')
    tags.append("VO")
  return result, tags

# return the found inflection
def find_inflected(word, pos, line):
  #if word == "focus": pdb.set_trace()
  inflections, inf_tags = get_inflections(word, pos)
  for inflection, tag in zip(inflections, inf_tags):
    if has_headword(inflection, line):
      return inflection, tag
  return "", ""

# example should have word or inflected word
def find_example(word, pos, examples):
  inflection = ""
  found = ""
  example = ""
  for line in examples:
    if not is_sentence(line): continue
    line = replace_contractions(word, line)
    if has_headword(word, line):
      found = word
      tag = "IN"
      example = line
      break
    else:
      found, tag = find_inflected(word, pos, line)
      if found != "":
        print "found inflected", word, found, tag
        example = line
        break
  if example == "":
    print "cannot find a good example:", word, pos, ">", examples
    print ""
    pdb.set_trace()
  return found, tag, example

def make_qna_type3(conn, level, sub_level, count):
  freq_max, freq_min = get_frequencies(level, sub_level)
  qrows = select_questions_q3(conn, [level, freq_max, freq_min], count)
  qnas = []
  for qrow in qrows:
    word = qrow[0]
    arows = select_1answer(conn, [level, word])
    pos = get_1pos(arows[0][0])
    meaning = arows[0][1]
    if bad_meaning(word, pos, meaning): continue
    examples = [arows[0][2], arows[0][3]]
    found, tag, example = find_example(word, pos, examples)
    if example == "": continue
    example = mark_word_example(found, pos, example)
    wrongs = select_2wrong(conn, [level, pos, found])
    choices = []
    for wrong in wrongs:
      choices.append(remove_front_paren(wrong[2]))
    a_index = random.randrange(0, len(wrongs)+1)
    choices.insert(a_index, remove_front_paren(meaning))
    qnas.append([found, pos, meaning, example, choices, a_index])
  return qnas

def make_qna_type4(conn, level, sub_level, count):
  freq_max, freq_min = get_frequencies(level, sub_level)
  qrows = select_questions_q4(conn, [level, freq_max, freq_min], count)
  qnas = []
  for qrow in qrows:
    word = qrow[0]
    arows = select_1answer(conn, [level, word])
    pos = get_1pos(arows[0][0])
    meaning = arows[0][1]
    examples = [arows[0][2], arows[0][3]]
    synopsis = arows[0][4]
    phrase = ""
    if arows[0][0].startswith("PHRASE"):
      phrase = word
      word = synopsis
    found, tag, example_org = find_example(word, pos, examples)
    if example_org == "": continue
    wrongs = select_2wrong_q4(conn, [level, pos, found])
    choices = []
    example, removed = blank_word_example(found, pos, example_org)
    for wrong in wrongs:
      if removed[0].isupper() and (not word[0].isupper() or example_org.find(removed) == 0):
        choices.append(wrong[0].capitalize())
      else:
        choices.append(wrong[0])

    a_index = random.randrange(0, len(wrongs)+1)
    choices.insert(a_index, removed)
    qnas.append([found, pos, meaning, example, choices, a_index])
  return qnas

def make_qna(qtype, level, sub_level, count):
  path = os.path.split(__file__)[0]
  dbfile = os.path.join(path, "cefr.db")
  conn = create_connection(dbfile)

  if qtype == 1:
    qnas = make_qna_type1(conn, level, sub_level, count)
  elif qtype == 2:
    qnas = make_qna_type2(conn, level, sub_level, count)
  elif qtype == 3:
    qnas = make_qna_type3(conn, level, sub_level, count)
  elif qtype == 4:
    qnas = make_qna_type4(conn, level, sub_level, count)

  conn.close()
  return qnas

# make a question type 2 or 4
def make_qna_type2or4(level, sub_level, excepts=None):
  if excepts != None:
    except_list = excepts.split('&')
  else:
    except_list = []

  path = os.path.split(__file__)[0]
  dbfile = os.path.join(path, "cefr.db")
  conn = create_connection(dbfile)

  freq_max, freq_min = get_frequencies(level, sub_level)
  qrows = select_questions_q4(conn, [level, freq_max, freq_min], 1)
  qrow = qrows[0]
  word = qrow[0]
  while level+'|'+word in except_list:
    qrows = select_questions_q4(conn, [level, freq_max, freq_min], 1)
    qrow = qrows[0]
    word = qrow[0]
  qnas = []
  arows = select_1answer(conn, [level, word])
  pos = get_1pos(arows[0][0])
  meaning = arows[0][1]
  examples = [arows[0][2], arows[0][3]]
  synopsis = arows[0][4]
  qtype = 2
  if bad_meaning(word, pos, meaning):
    qtype = 4
  if arows[0][0].startswith("PHRASE"):
    print "word is phrase"
    word = synopsis
    qtype = 4

  if random.randrange(1,3) == 1:
    qtype = 4
  if qtype == 4:
    found, tag, example_org = find_example(word, pos, examples)
    if example_org == "": pdb.set_trace()
    wrongs = select_2wrong_q4(conn, [level, pos, word])
    choices = []
    example, removed = blank_word_example(found, pos, example_org)
    make_log(word + '||' + pos + '||' + example + '||' + removed)
    for wrong in wrongs:
      conjugated = ""
      if pos.startswith("VERB") or pos.startswith("AUX") or pos.startswith("MODAL"):
        conjugated = conjugate(wrong[0], pos, tag)
      if removed[0].isupper() and (not word[0].isupper() or example_org.find(removed) == 0):
        if conjugated == "":
          choices.append(wrong[0].capitalize())
        else:
          choices.append(conjugated.capitalize())
      else:
        if conjugated == "":
          choices.append(wrong[0])
        else:
          choices.append(conjugated)
    a_index = random.randrange(0, len(wrongs)+1)
    choices.insert(a_index, removed)
    qnas.append([found, pos, meaning, example, choices, a_index])
  else: # qtype == 2
    meaning = remove_front_paren(meaning)
    wrongs = select_2wrong_q2(conn, [level, pos, word])
    choices = []
    for wrong in wrongs:
      choices.append(wrong[0])
    a_index = random.randrange(0, len(wrongs)+1)
    choices.insert(a_index, word)
    qnas.append([word, pos, meaning, "", choices, a_index])

  conn.close()
  return qnas

if __name__ == "__main__":
  if os.path.exists("/home/koo/english/cefr/make_qna.log"):
    os.remove("/home/koo/english/cefr/make_qna.log")
  if len(sys.argv) < 1:
    print "run with 2 arguments: level(A1~C2) and sub-level(1-10)"
    print "run with 3 arguments: type(1~4), level(A1~C2) and sub-level(1-10)"
    sys.exit()
  if len(sys.argv) <= 3:  # 0 or 2 arguments
    while True:
      if len(sys.argv) == 1:
        level = random.choice(['A1', 'A2', 'B1', 'B2', 'C1', 'C2'])
        sub_level = random.randrange(1, 11)
      else:
        level = sys.argv[1]
        sub_level = int(sys.argv[2])
      if level not in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
        print "level shoud be A1 ~ C2"
        sys.exit()
      if sub_level < 1 or sub_level > 10:
        print "sub-level shoud be 1 ~ 10"
        sys.exit()
      qnas = make_qna_type2or4(level, sub_level)
      if len(qnas) != 1: pdb.set_trace()
      if qnas[0][3] == "":
        print_qna_type2(qnas)
      else:
        print_qna_type4(qnas)
  else:
    qtype = int(sys.argv[1])
    level = sys.argv[2]
    sub_level = int(sys.argv[3])
    if qtype < 1 or qtype > 4:
      print "type shoud be 1 ~ 4"
      sys.exit()
    if level not in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
      print "level shoud be A1 ~ C2"
      sys.exit()
    if sub_level < 1 or sub_level > 10:
      print "sub-level shoud be 1 ~ 10"
      sys.exit()

    qnas = make_qna(qtype, level, sub_level, 3)
    if qtype == 1:
      print_qna_type1(qnas)
    elif qtype == 2:
      print_qna_type2(qnas)
    elif qtype == 3:
      print_qna_type3(qnas)
    elif qtype == 4:
      print_qna_type4(qnas)
