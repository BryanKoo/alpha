#-*- encoding: utf-8 -*-
# parse and save data
# find uk word and change to us(uk)
# bind google frequency with each word
# change synopsis with headword if synopsis is really a idiom/phrase
# save parsing result at sqlite3
# schema word_bymeanings : mid(pk), frequency(index), word(not null), pos(not null), meaning(not null), synopsis, examples
# schema also_bymeanings : aid(pk), mid(fk), also_words(not null)
# schema us_bymeanings : uid(pk), mid(fk), us_word(not null)
# schema family_words : fid(pk), original_word(not null), family_words(not null)
# rule check: 1 or more example sentences

import sqlite3
import re
import os, sys
import pdb
import pickle
from check_ukus import check_ukus
reload(sys)
sys.setdefaultencoding('utf-8')

def split_slash_phrase(text):
  phrases = []
  pre_word = ""
  post_word = ""
  pos_last_slash = text.rfind("/")
  pos_etc = text.find("etc.")
  if pos_etc > 0 and pos_etc + 4 < len(text):
    post_etc = text[pos_etc+4:]
  if pos_last_slash < pos_etc:
    pre_etc = text[pos_last_slash+1:post_etc]
    text = text[:pos_last_slash]
  tokens = text.split(" ")
  found_slash = False
  for token in tokens:
    if not found_slash and token.count("/") == 0:
      pre_word += token + " "
    elif token.count("/") > 0:
      sub_tokens = token.split('/')
      found_slash = True
    else:
      post_word += token + " "
  for sub_token in sub_tokens:
    phrases.append(pre_word + sub_token + post_etc)
  return phrases

def split_phrase(line):
  phrases = []
  if line.count(';') > 1:
    tokens = line.split(';')
    for token in tokens:
      if token.count('/') == 0:
        phrases.append(token)
      else:
        phrases += split_slash_phrase(token)
  elif token.count('/') == 0:
    phrases.append(line)
  else:
    phrases += split_slash_phrase(line)
    
def write_also(word, pos, meaning, also, also_pos, also_syn, also_ex):
  if also_pos != "": also += also_pos
  if also_syn != "": also += also_syn
  if also_ex != "": also += also_ex
  if also != "":
    also = also.replace("US ", "")
    also = also.replace("UK ", "")
    cefr_also_pos_meaning.append(also + "|" + pos + '|' + meaning)
    with open("cefr_also.tsv", "a") as fp:
      fp.write(word + "\t" + also + "\n")
  return also

# write word|pos|meaning for also words
def write_also_pass2():
  for also_pos_meaning in cefr_also_pos_meaning:
    also = also_pos_meaning.split('|')[0]
    if also not in cefr_words:
      cefr_word_pos_meaning.append(also_pos_meaning)

# write inflection rule of cefr words
def write_inflection(word, pos, inflection, inflection_pos, grammar_pos):
  #if word == "permit": pdb.set_trace()
  if grammar_pos == "[U]": inflection = "UNCOUNTABLE"
  if inflection == "" and inflection_pos == "": return
  elif inflection == "": inflection = inflection_pos
  elif inflection_pos != "": inflection += " " + inflection_pos
  if pos.startswith("VERB") or pos.startswith("AUXILIARY VERB") or pos.startswith("MODAL VERB"):
    with open("../english-inflection/cefr_conjugations.tsv", "a") as fp:
      fp.write(word + "\t" + inflection + "\n")
  if pos.startswith("NOUN") or pos.startswith("NUMBER"):
    if inflection.count('PLURAL') > 0 or inflection.count('UNCOUNTABLE') > 0:
      with open("../english-inflection/cefr_plurals.tsv", "a") as fp:
        fp.write(word + "\t" + inflection + "\n")
  if pos.startswith("AD") or pos.startswith("DETER"):
    with open("../english-inflection/cefr_comparatives.tsv", "a") as fp:
      fp.write(word + "\t" + inflection + "\n")

def has_upperword(text):
  tokens = text.split(" ")
  for token in tokens:
    if token.isupper() and len(token) > 1:
      if token not in ["CD", "US", "MP3", "IT", "DVD", "UK"]:
        return True
  return False

def identify_phrase(word, pos, synopsis):
  if synopsis.isupper() or synopsis == "":
    return word, pos, synopsis
  else:
    return synopsis, "PHRASE; "+ pos, word

def is_sentence(text):
  if text.endswith(".") or text.endswith("?") or text.endswith("!"):
    return True
  elif text.endswith('."') or text.endswith('?"') or text.endswith('!"'):
    return True
  elif text.endswith('.)') or text.endswith('?)') or text.endswith('!)'):
    return True
  elif text.endswith(".'") or text.endswith("?'") or text.endswith("!'"):
    return True
  elif text.endswith("'") or text.endswith('"'):
    return False
  else:
    return False

def cleanse_meaning(meaning):
  meaning = meaning.replace("ABBREVIATION FOR", "")
  meaning = meaning.replace("  ", " ").strip()
  return meaning

def write_sentence(meaning, examples):
  with open("cefr_sentences.txt", "a") as fp:
    fp.write(meaning + '\n')
    for example in examples:
      fp.write(example + '\n')

# cleanse parenthesis without nesting
# remove parenthesis and keep in-between when 1 word or has headword or short
# remove parenthesis and in-between when multi-word and long
def cleanse_example(word, example):
  while True:
    pos1 = example.find('(')
    pos2 = example.find(')')
    if pos1 < 0: break
    if pos1 >= pos2: pdb.set_trace()  # check nested paren
    parened = example[pos1:pos2+1]
    if parened.count(' ') == 0:
      example = example[:pos1] + example[pos1+1:pos2] + example[pos2+1:]
    elif parened.lower().count(word.lower()) > 0:
      example = example[:pos1] + example[pos1+1:pos2] + example[pos2+1:]
    elif len(example.split(' ')) <= 16:
      example = example[:pos1] + example[pos1+1:pos2] + example[pos2+1:]
    else:
      example = example[:pos1] + example[pos2+1:]
  return example
  
# select sentence instead of phrase
# example should be not too short and not too long (6 ~ 16 words)
def select_2examples(word, examples_org):
  #if word == "what": pdb.set_trace()
  too_short = False
  too_long = False
  candidates = []
  examples = []
  for example in examples_org:
    if is_sentence(example):
      example = cleanse_example(word, example)
      if len(example.split(' ')) < 7:
        too_short = True
        candidates.append(example)
      elif len(example.split(' ')) > 16:
        too_long = True
        candidates.append(example)
      else:
        examples.append(example)
  if len(examples) == 0:
    if too_long:
      shortest = ""
      for example in candidates:
        if len(example.split(' ')) < 6: continue
        if shortest == "" or len(example.split(' ')) < len(shortest.split(' ')):
          shortest = example
      examples.append(shortest)
    elif too_short:
      longest = ""
      for example in candidates:
        if longest == "" or len(example.split(' ')) > len(longest.split(' ')):
          longest = example
      examples.append(longest)

  if len(examples) == 0:
    print "no good examples"
    pdb.set_trace()
    return examples
  elif len(examples) <= 2:
    return examples
  else:
    return examples[0:2]

  
def create_connection(db_file):
  try:
    conn = sqlite3.connect(db_file)
    return conn
  except sqlite3.Error as e:
    print(e)
    pdb.set_trace()

  return None

def create_table(conn, create_table_sql):
  try:
    c = conn.cursor()
    c.execute(create_table_sql)
  except sqlite3.Error as e:
    print(e)

def create_tables_from_file(conn, sfile):
  sf = open(sfile, 'r')
  lines = sf.readlines()
  sql = ""
  for line in lines:
    if line.strip().endswith(';'):
      sql += line
      create_table(conn, sql)
      sql = ""
    else:
      sql += line

# [freq, level, word, pos, meaning, synopsis, examples[0], examples[1]]
def insert_word(conn, columns):
  if columns[3].startswith("PHRASE"):
    cefr_word_pos_meaning.append(columns[5] + "=" + columns[2] + '|' + columns[3][8:] + '; ' + columns[3][:6] + '|' + columns[4]) # word|pos|meaning
    if columns[5] not in cefr_words: cefr_words[columns[5]] = 1
  else:
    cefr_word_pos_meaning.append(columns[2] + '|' + columns[3] + '|' + columns[4]) # word|pos|meaning
    if columns[2] not in cefr_words: cefr_words[columns[2]] = 1
  if conn == None: return None
  if has_upperword(columns[4]):
    columns[4] = cleanse_meaning(columns[4])
  sql = "insert into words_bymeaning (frequency, level, word, pos, meaning, synopsis, example1, example2) values (?,?,?,?,?,?,?,?)"
  try:
    cur = conn.cursor()
    cur.execute(sql, columns)
    conn.commit()
  except sqlite3.Error as e:
    print(e)
    pdb.set_trace()
  return cur.lastrowid

def insert_also(conn, columns):
  pass

# [word_id, us_word]
def insert_ukus(conn, columns, pos, meaning, synopsis):
  if pos.startswith("PHRASE"):
    cefr_word_pos_meaning.append(synopsis + '=' + columns[1] + '|' + pos[8:] + ';' + pos[:6] + '|' + meaning)  # word|pos|meaning
    if synopsis not in cefr_words: cefr_words[synopsis] = 1
  else:
    cefr_word_pos_meaning.append(columns[1] + '|' + pos + '|' + meaning)  # word|pos|meaning
    if columns[1] not in cefr_words: cefr_words[columns[1]] = 1
  if conn == None: return None
  sql = "insert into us_bymeaning (word_id, us_word) values (?,?)"
  try:
    cur = conn.cursor()
    cur.execute(sql, columns)
    conn.commit()
  except sqlite3.Error as e:
    print(e)
    pdb.set_trace()

def insert_family(conn, columns):
  pass

def read_google_frequency(gfile):
  g_word = {}
  gf = open(gfile, 'r')
  while True:
    line = gf.readline()
    if not line: break
    tokens = line.split('\t')
    g_word[tokens[0]] = int(tokens[1].strip())

  return g_word

def filter_slash(word):
  pos = word.find("/")
  if pos > 0:
    word = word[:pos]
  return word

def filter_semicolon(word):
  pos = word.find(";")
  if pos > 0:
    word = word[:pos]
  return word

def filter_phrase(word):
  word = word.replace("sth's", "")
  word = word.replace("sths", "")
  word = word.replace("sth", "")
  word = word.replace("sb's", "")
  word = word.replace("sbs", "")
  word = word.replace("sb", "")
  word = word.replace("...", "")
  word = word.replace("  ", " ")
  return word.strip()

def get_manual_frequency(word):
  word_org = word
  if word.count("apreciate...") > 0: pdb.set_trace()
  word = filter_phrase(word)
  word = word.replace("-", " ")
  word = remove_parened(word).strip()
  #word = filter_slash(word)
  word = filter_semicolon(word)
  tokens = word.split(" ")
  for token in tokens:
    token = filter_slash(token)
  word = " ".join(tokens).strip()
  num_words = word.count(" ") + 1
  tokens = word.split(" ")
  if num_words == 2:
    if tokens[0] in g1w_word and tokens[1] in g1w_word:
      freq1 = g1w_word[tokens[0]]
      freq2 = g1w_word[tokens[1]]
    elif tokens[0] in g1w_word:
      freq1 = g1w_word[tokens[0]]
      freq2 = freq1 / 2
    elif tokens[1] in g1w_word:
      freq2 = g1w_word[tokens[1]]
      freq1 = freq2 / 2
    else:
      print word
      pdb.set_trace()
    if freq1 > freq2:
      small_freq = freq2
      large_freq = freq1
    else:
      small_freq = freq1
      large_freq = freq2
    freq = small_freq * large_freq / (large_freq + small_freq)
    return freq
  elif num_words == 3:
    word_12 = tokens[0] + " " + tokens[1]
    word_23 = tokens[1] + " " + tokens[2]
    if word_12 in g2w_word: freq1 = g2w_word[word_12]
    else:
      freq1 = 10000
    if word_23 in g2w_word: freq2 = g2w_word[word_23]
    else:
      freq2 = 10000
    if freq1 > freq2:
      small_freq = freq2
      large_freq = freq1
    else:
      small_freq = freq1
      large_freq = freq2
    freq = small_freq * large_freq / (large_freq + small_freq)
    return freq
  elif num_words > 3:
    word_12 = tokens[0] + " " + tokens[1]
    word_23 = tokens[1] + " " + tokens[2]
    word_34 = tokens[2] + " " + tokens[3]
    if word_12 in g2w_word: freq1 = g2w_word[word_12]
    else: freq1 = 10000
    if word_23 in g2w_word: freq2 = g2w_word[word_23]
    else: freq2 = 10000
    if word_34 in g2w_word: freq3 = g2w_word[word_34]
    else: freq3 = 10000
    if freq1 >= freq2 and freq2 >= freq3:
      small_freq = freq3
      large_freq = freq2
    elif freq3 >= freq2 and freq2 >= freq1:
      small_freq = freq1
      large_freq = freq2
    elif freq2 >= freq1 and freq1 >= freq3:
      small_freq = freq3
      large_freq = freq1
    elif freq3 >= freq1 and freq1 >= freq2:
      small_freq = freq2
      large_freq = freq1
    elif freq2 >= freq3 and freq3 >= freq1:
      small_freq = freq1
      large_freq = freq3
    elif freq1 >= freq3 and freq3 >= freq2:
      small_freq = freq2
      large_freq = freq3
    freq = small_freq * large_freq / (large_freq + small_freq)
    return freq
  pdb.set_trace()
  
def get_frequency(word, ukus, also):
  word_org = word
  if word.count(" ") > 0:
    word = filter_phrase(word)
    word = remove_parened(word).strip()
  if word.count(" ") == 0:
    word = filter_slash(word)
  word = word.replace('?', '')
  word = word.replace('!', '')
  word = word.replace("'", '')
  word = word.replace("é", 'e')
  if word == "burgle": word = "burgled"
  if not word.islower():
    word = word.lower()

  if word in g1w_word:
    frequency = g1w_word[word]
  elif word in g2w_word:
    frequency = g2w_word[word]
  elif word.count('-') and word.replace('-', '') in g1w_word:
    word = word.replace('-', '')
    frequency = g1w_word[word]
  elif word.count('-') and word.replace('-', ' ') in g2w_word:
    word = word.replace('-', ' ')
    frequency = g2w_word[word]
  else:
    if word == "a.m.":
      l_freq = g1w_word["announce"]
      r_freq = g1w_word["damages"]
      frequency = (l_freq + r_freq) / 2
    elif word == "p.m.":
      l_freq = g1w_word["blocks"]
      r_freq = g1w_word["tries"]
      frequency = (l_freq + r_freq) / 2
    else:
      frequency = get_manual_frequency(word)

  if ukus != "":
    word = ukus
    if word in g1w_word:
      frequency += g1w_word[word]
    elif word in g2w_word:
      frequency += g2w_word[word]
    elif word.count('-') and word.replace('-', '') in g1w_word:
      word = word.replace('-', '')
      frequency += g1w_word[word]
    elif word.count('-') and word.replace('-', ' ') in g2w_word:
      word = word.replace('-', ' ')
      frequency += g2w_word[word]

  if also != "":
    word = also 
    if word in g1w_word:
      frequency += g1w_word[word]
    elif word in g2w_word:
      frequency += g2w_word[word]
    elif word.count('-') and word.replace('-', '') in g1w_word:
      word = word.replace('-', '')
      frequency += g1w_word[word]
    elif word.count('-') and word.replace('-', ' ') in g2w_word:
      word = word.replace('-', ' ')
      frequency += g2w_word[word]

  if frequency == None: pdb.set_trace() 
  return frequency

def remove_bparened(line):
  if line.count("[") > 0 and line.count("]") > 0:
    line = re.sub(r'\[.*\]', '', line)
  return line.strip()

def remove_parened(line):
  if line.count("(") > 0 and line.count(")") > 0:
    line = re.sub(r'\(.*\)', '', line)
  return line.replace("  ", " ").strip()

def print_dexample(dexample):
  for example in dexample:
    print "    ", example

def cleanse_lexample(line):
  line = line.replace("[", "")
  line = line.replace("]", "")
  return line

def has_pronunciation(line):
  for ch in line:
    #if ch in ['ð', 'ɪ', 'ə', 'ˈ', 'æ', 'ə', 'ː', 'ˌ', '.', ':', u'\u0329', u'\u032c', u'\u0283', u'\u0252', u'\u028c', u'\u028a', u'\u03b8', u'\u0292']:
    if ch in ['ð', 'ɪ', 'ə', 'ˈ', 'æ', 'ə', 'ː', 'ˌ', u'\u0329', u'\u032c', u'\u0283', u'\u0252', u'\u028c', u'\u028a', u'\u03b8', u'\u0292', u'\u0251']:
      return True
  return False

# remove usage keywords
def remove_keyword_ex(line):
  keywords = ['DISAPPROVING', 'INFORMAL', 'FORMAL', 'APPROVING', 'SPECIALIZED', 'SLIGHTLY', 'LITERARY']
  for word in keywords:
    line = line.replace(word, "").strip()
  return line

# remove usage keywords
def remove_keyword(line):
  keywords = ['DISAPPROVING', 'INFORMAL', 'FORMAL', 'APPROVING', 'SPECIALIZED', 'SLIGHTLY', 'LITERARY', 'UK']
  for word in keywords:
    line = line.replace(word, "").strip()
  return line

def is_headline(line, next_line):
  if not is_pos(line) and line.count('/') == 2:   # prononciation
    tokens = line.split('/')
    word = tokens[0]
    pronunciation = tokens[1]
    if has_pronunciation(pronunciation):
      return True
    elif word[-1] == ' ' and (line.endswith('/') or line.endswith(')') or line.endswith('DISAPPROVING') or line.endswith(' FORMAL') or line.endswith('INFORMAL') \
      or line.endswith('APPROVING') or line.endswith('SPECIALIZED') or line.endswith('SLIGHTLY')) and not is_meaning(next_line):
      return True
    else:
      return False
  elif line.count(' ') == 0 and line.count('.') == 0 and line.count(']') == 0 and line.count('?') == 0 and (is_pos(next_line) or next_line.startswith("Word family:")):
    return True
  elif line.count(' ') == 1 and line.count('.') == 0 and line.count('?') == 0 and line.islower() and (is_pos(next_line) or next_line.startswith("Word family:")):
    return True
  elif line.count('(ALSO ') > 0 and line.count('.') == 0 and line.count('?') == 0 and is_pos(next_line):  # online
    return True
  else:
    return False

def is_pos(line):
  tokens = line.split(";")
  tokens = tokens[0].split(" ")
  if tokens[0] in ["DETERMINER", "NOUN", "VERB", "ADVERB", "PREPOSITION", "ADJECTIVE", "CONJUNCTION", \
    "AUXILIARY", "EXCLAMATION", "MODAL", "PRONOUN", "ADV", "NUMBER", "ORDINAL", "INFINITIVE"]:
    return True
  else:
    return False

def parse_pos(word, line):
  pos = ""
  pron = ""
  also = ""
  inflection = ""
  grammar = ""
  line = line.replace("or US ALSO", "or")
  tokens = line.split(";")
  line = line.replace("ALSO US", "also us") # ?
  for token in tokens:
    ntokens = token.strip().split(" ")
    if ntokens[0] in ["AUXILIARY", "MODAL", "ORDINAL"]:   # two word pos
      if pos == "":
        pos = ntokens[0] + " " + ntokens[1]
      else:
        pos += "; " + ntokens[0] + " " + ntokens[1]
      remained = " ".join(ntokens[2:])
    else:
      if pos == "":
        pos = ntokens[0]
      else:
        pos += "; " + ntokens[0]
      remained = " ".join(ntokens[1:])

    while remained.count("ALSO") > 0:   # (UK ALSO, (ALSO
      pos1 = remained.find("ALSO")
      pos2 = remained.find(")")
      if also == "":
        also = remained[pos1+4:pos2].strip()
      else:
        also += ", " + remained[pos1+4:pos2].strip()
      remained = remained[pos2+1:]

    if remained.count('(FORMAL') > 0 or remained.count('(INFORMAL') > 0: # formal/informal are similar to ALSO
      pos1 = remained.find("FORMAL")
      pos2 = remained.rfind(")")
      if also == "":
        also = remained[pos1+6:pos2].strip()
      else:
        also += ", " + remained[pos1+6:pos2].strip()
      remained = remained[pos2+1:]

    if remained.count("/") == 2:  # pronunciation
      pos1 = remained.find("/")
      pos2 = remained[pos1+1:].find("/")
      if pron == "":
        pron = remained[pos1+1:pos1+pos2+1]
        remained = remained[pos1+pos2+2:].strip()
      else:
        print "doubled pron", line
        pdb.set_trace()

    #if word == 'permit': pdb.set_trace()

    if len(remained) > 0:
      pos1 = remained.find("[")
      pos2 = remained.find("]")
      if pos1 >= 0 and pos1 < pos2:
        grammar = remained[pos1:pos2+1]
        remained = remained[pos2+1:].strip()
      remained = remained.replace("INFORMAL", "").strip()
      remained = remained.replace("FORMAL", "").strip()
      remained = remained.replace("SPECIALIZED", "").strip()
      remained = remained.replace("SLIGHTLY", "").strip()
      remained = remained.replace("UK", "").strip()
      remained = remained.replace("LITERARY", "").strip()
      remained = remained.replace("DISAPPROVING", "").strip()
      remained = remained.replace("MARKER", "").strip()
      if len(remained) == 0:
        pass
      elif remained[0] == "(" and remained[-1] == ")":
        if inflection == "":
          inflection = remained[1:-1]
        else:
          print "doubled inflection"
          pdb.set_trace()
      else:
        print "something remained", remained
        pdb.set_trace()

  return pos.strip(), pron.strip(), also.strip(), inflection.strip(), grammar.strip()


def is_meaning(line):
  if line.startswith('[') and line[1:3] in ["A1", "A2", "B1", "B2", "C1", "C2"]:
    return True
  else:
    return False

def is_family(line):
  if line[0].isupper() and line[1].islower() and line.count(":") == 1:
    return True
  else:
    return False

def parse_family(line):
  tokens = line.split(":")
  fpos = tokens[0].strip()
  fwords = tokens[1].strip()
  return fwords

def is_eos(line):
  if line[-1] in ['.', '?', '!']:
    if len(line) > 1 and line[-2].isdigit():
      return False
    else:
      return True
  elif line[-1] in ['"', "'"] and line[-2] in ['.', '?', '!']:
    return True
  elif line == "With best wishes,":
    return True
  else:
    return False

def parse_headline(line):
  also = ""
  pron = ""
  inflection = ""

  if line.count('/') == 2:
    tokens = line.split("/")
    if tokens[0].count('(') == 0: # also before pronunciation
      word = tokens[0].strip()
    elif tokens[0].count('ALSO') > 0: # also
      pos1 = tokens[0].find('(')
      pos2 = tokens[0].find("ALSO")
      pos3 = tokens[0].find(")")
      word = tokens[0][:pos1].strip()
      also = tokens[0][pos2+4:pos3].strip()
    else: # optional part (added ALSO if not optional)
      pos1 = tokens[0].find('(')
      word = tokens[0][:pos1].strip()
      optional = tokens[0][pos1:] # may be also (a.m. am, easygoing easy-going)
    pron = tokens[1].strip()
    remained = tokens[2].strip()
    if len(remained) > 0:
      while remained.count("ALSO") > 0:  # also after pronunciation
        pos1 = remained.find("ALSO")
        pos2 = remained.rfind(")")
        if also == "":
          also = remained[pos1+4:pos2].strip()
        else:
          also += ", " + remained[pos1+4:pos2].strip()
        remained = remained[pos2+1:]
      if len(remained) > 0 and remained.count("(") > 0:  # extract inflection(tense or plural or comparative) or also
        if remained.count('(FORMAL') > 0 or remained.count('(INFORMAL') > 0: # formal/informal are similar to ALSO
          pos1 = remained.find("FORMAL")
          pos2 = remained.rfind(")")
          if also == "":
            also = remained[pos1+6:pos2].strip()
          else:
            also += ", " + remained[pos1+6:pos2].strip()
        elif remained.count('(SYMBOL') > 0: # symbol is similar to ALSO
          pos1 = remained.find("SYMBOL")
          pos2 = remained.rfind(")")
          if also == "":
            also = remained[pos1+6:pos2].strip()
          else:
            also += ", " + remained[pos1+6:pos2].strip()
        else:
          pos1 = remained.find("(")
          pos2 = remained.rfind(")")
          inflection = remained[pos1+1:pos2]
  elif line.count("(") > 0:
    if line.count('ALSO') > 0: # also
      pos1 = line.find('(')
      pos2 = line.find("ALSO")
      pos3 = line.find(")")
      word = line[:pos1].strip()
      also = line[pos2+4:pos3].strip()
    else: # optional part (added ALSO if not optional)
      pos1 = line.find('(')
      word = line[:pos1].strip()
      optional = line[pos1:] # may be also (a.m. am, easygoing easy-going)
  else:
    word = line

  if word[-1].isdigit():
    word = word[:-1]
  return word, pron, also, inflection

  
def parse_meaning(line):
  also = ""
  grammar = ""
  level = line[1:3]
  line = line[4:].strip()
  if len(line) > 0 and line[0] == "!":
    line = line[1:].strip()
  
  line = line.replace(", MAINLY", "").strip()   # mainly used with also
  line = line.replace("MAINLY", "").strip()     # mainly used with also

  pos1 = line.find("[")
  pos2 = line.find("]")
  if pos1 == 0 and pos1 < pos2:
    grammar = line[pos1:pos2+1]
    line = line[pos2+1:].strip()

  while line.count("ALSO") > 0:
    pos1 = line.find("ALSO")
    pos2 = line.find(")")
    if also == "":
      also = line[pos1+4:pos2].strip()
    else:
      also += ", " + line[pos1+4:pos2].strip()
    line = line[pos2+1:]

  if line.count('(SYMBOL') > 0: # symbol similar to ALSO
    pos1 = line.find("SYMBOL")
    pos2 = line.rfind(")")
    if also == "":
      also = line[pos1+6:pos2].strip()
    else:
      also += ", " + line[pos1+6:pos2].strip()
    line = line[pos2+1:]

  meaning = remove_keyword_ex(line.strip())
  return level, meaning, also, grammar

def parse_synopsis(line):
  also = ""
  line = line.replace(", MAINLY", "").strip()
  line = line.replace("MAINLY", "").strip()
  line = remove_bparened(line)
  while line != "ALSO" and line.count("ALSO") > 0:
    pos1 = line.find("ALSO")
    pos2 = line.find(")")
    if also == "":
      also = line[pos1+4:pos2].strip()
    else:
      also += ", " + line[pos1+4:pos2].strip()
    line = line[pos2+1:]
  synopsis = line.strip()
  synopsis = remove_keyword(synopsis)
  return synopsis, also


# read vocabulary text file and parse line by line using patterns for headword, pos, meaning, examples
# headword (ALSO ???) /pronunciation/ (ALSO ???)
# Word family:
# pos [?] (ALSO ???)  /pronunciation/
# synopsis
# [level] (ALSO ???) meaning
# Dictionary example(s):
# sentence(s) or phrase(s)
# Learner example:
# sentence(s)
def parse_vocabulary(conn, vocfile):
  fp = open(vocfile, 'r')
  lines = fp.readlines()
  fp.close()

  # state: head > (word_family) > (pos > ((synopsis) > meaning > dict_examples > sentences > (learner example > sentence)))
  state = "na"
  word = ""
  num_word = 0
  num_level = 0
  is_blank = False

  for i in range(len(lines)):
    line = lines[i].decode('utf-8').strip()
    next_line = ""
    if i+1 < len(lines):
      next_line = lines[i+1].strip()
    if (next_line == "" or next_line.isdigit()) and i+2 < len(lines):
      next_line = lines[i+2].strip()
      if (next_line == "" or next_line.isdigit()) and i+3 < len(lines):
        next_line = lines[i+3].strip()
        if (next_line == "" or next_line.isdigit()) and i+4 < len(lines):
          next_line = lines[i+4].strip()
    if line == "":
      is_blank = True
      continue
    else:
      if is_blank == True and (line.isdigit() or (line.isupper() and len(line) == 1)):
        continue
      else:
        is_blank = False

    if state == "na":
      if is_headline(line, next_line):
        state = "head"
        word, pron, also, inflection = parse_headline(line)
        f_words = ""
        num_word += 1
    elif state == "head":
      if line.startswith("Word family:"):
        state = "family"
      else:
        if is_pos(line):
          state = "pos"
          pos, pron_pos, also_pos, inflection_pos, grammar_pos = parse_pos(word, line)
          write_inflection(word, pos, inflection, inflection_pos, grammar_pos)
        else:
          print state, "error"
    elif state == "family":
      if is_family(line):
        fwords = parse_family(line)
        if f_words == "":
          f_words = fwords
        else:
          f_words += ", " + fwords
      else:
        if f_words != "":
          #print f_words
          pass
        if is_pos(line):
          state = "pos"
          pos, pron_pos, also_pos, inflection_pos, grammar_pos = parse_pos(word, line)
          write_inflection(word, pos, inflection, inflection_pos, grammar_pos)
        else:
          print state, "error"
          pdb.set_trace()
    elif state == "pos":
      if line.endswith("PHRASAL VERB"):
        pass
      elif is_meaning(line):
        synopsis = ""
        state = "meaning"
        level, meaning, also_ex, grammar_ex = parse_meaning(line)
        num_level += 1
        lexample = ""
        dexample = []
      else:
        state = "synopsis"
        synopsis, also_syn = parse_synopsis(line)
    elif state == "synopsis":
      if is_meaning(line):
        state = "meaning"
        level, meaning, also_ex, grammar_ex = parse_meaning(line)
        num_level += 1
        lexample = ""
        dexample = []
      else:
        print state, "error"
    elif state == "meaning":
      if line.startswith("Dictionary example"):
        state = "dexample"
      elif line.startswith("Learner example"):  # no dictionary example
        state = "lexample"
      elif is_headline(line, next_line):  # no example case 1
        print "no example", word
        pdb.set_trace()
        ukus = check_ukus(word, pos, synopsis, meaning)
        word, pos, synopsis = identify_phrase(word, pos, synopsis)
        also4 = write_also(word, pos, meaning, also, also_pos, also_syn, also_ex)
        freq = get_frequency(word, ukus, also4)
        row_id = insert_word(conn, [freq, level, word, pos, meaning, synopsis, "", ""])
        if ukus != "": insert_ukus(conn, [row_id, ukus], pos, meaning, synopsis)
        print str(num_level) + '\t' + word + '\t' + pos + '\t' + str(freq) + '\t' + level + '\t' + "[" + synopsis + "]" + '\t' + meaning
        state = "head"
        word, pron, also, inflection = parse_headline(line)
        f_words = ""
        num_word += 1
      elif is_meaning(next_line): # no example case 2
        # "\t("+also+also_pos+also_syn+also_ex+")" grammar_pos+grammar_ex
        print "no example", word
        pdb.set_trace()
        word_org = word
        pos_org = pos
        ukus = check_ukus(word, pos, synopsis, meaning)
        word, pos, synopsis = identify_phrase(word, pos, synopsis)
        also4 = write_also(word, pos, meaning, also, also_pos, also_syn, also_ex)
        freq = get_frequency(word, ukus, also4)
        row_id = insert_word(conn, [freq, level, word, pos, meaning, synopsis, "", ""])
        if ukus != "": insert_ukus(conn, [row_id, ukus], pos, meaning, synopsis)
        print str(num_level) + '\t' + word + '\t' + pos + '\t' + str(freq) + '\t' + level + '\t' + "[" + synopsis + "]" + '\t' + meaning
        word = word_org
        pos = pos_org
        state = "synopsis"
        synopsis, also_syn = parse_synopsis(line)
      else:
        meaning += " " + line
    elif state == "dexample":
      if len(dexample) == 0 and not line.startswith("Learner example"):
        dexample.append(line)
      elif line.startswith("Learner example"):
        state = "lexample"
      elif is_pos(line):
        examples = select_2examples(word, dexample)
        write_sentence(meaning, dexample)
        if len(examples) < 2: examples.append("")
        word_org = word
        ukus = check_ukus(word, pos, synopsis, meaning)
        word, pos, synopsis = identify_phrase(word, pos, synopsis)
        also4 = write_also(word, pos, meaning, also, also_pos, also_syn, also_ex)
        freq = get_frequency(word, ukus, also4)
        row_id = insert_word(conn, [freq, level, word, pos, meaning, synopsis, examples[0], examples[1]])
        if ukus != "": insert_ukus(conn, [row_id, ukus], pos, meaning, synopsis)
        print str(num_level) + '\t' + word + '\t' + pos + '\t' + str(freq) + '\t' + level + '\t' + "[" + synopsis + "]" + '\t' + meaning
        print examples
        word = word_org
        state = "pos"
        pos, pron_pos, also_pos, inflection_pos, grammar_pos = parse_pos(word, line)
        write_inflection(word, pos, inflection, inflection_pos, grammar_pos)
      elif is_meaning(line):
        examples = select_2examples(word, dexample)
        write_sentence(meaning, dexample)
        if len(examples) < 2: examples.append("")
        ukus = check_ukus(word, pos, synopsis, meaning)
        word_org = word
        pos_org = pos
        word, pos, synopsis = identify_phrase(word, pos, synopsis)
        also4 = write_also(word, pos, meaning, also, also_pos, also_syn, also_ex)
        freq = get_frequency(word, ukus, also4)
        row_id = insert_word(conn, [freq, level, word, pos, meaning, synopsis, examples[0], examples[1]])
        if ukus != "": insert_ukus(conn, [row_id, ukus], pos, meaning, synopsis)
        print str(num_level) + '\t' + word + '\t' + pos + '\t' + str(freq) + '\t' + level + '\t' + "[" + synopsis + "]" + '\t' + meaning
        print examples
        word = word_org
        pos = pos_org
        synopsis = ""
        state = "meaning"
        level, meaning, also_ex, grammar_ex = parse_meaning(line)
        num_level += 1
        lexample = ""
        dexample = []
      elif is_meaning(next_line):
        examples = select_2examples(word, dexample)
        write_sentence(meaning, dexample)
        if len(examples) < 2: examples.append("")
        ukus = check_ukus(word, pos, synopsis, meaning)
        word_org = word
        pos_org = pos
        word, pos, synopsis = identify_phrase(word, pos, synopsis)
        also4 = write_also(word, pos, meaning, also, also_pos, also_syn, also_ex)
        freq = get_frequency(word, ukus, also4)
        row_id = insert_word(conn, [freq, level, word, pos, meaning, synopsis, examples[0], examples[1]])
        if ukus != "": insert_ukus(conn, [row_id, ukus], pos, meaning, synopsis)
        print str(num_level) + '\t' + word + '\t' + pos + '\t' + str(freq) + '\t' + level + '\t' + "[" + synopsis + "]" + '\t' + meaning
        print examples
        word = word_org
        pos = pos_org
        state = "synopsis"
        synopsis, also_syn = parse_synopsis(line)
      elif is_headline(line, next_line):
        examples = select_2examples(word, dexample)
        write_sentence(meaning, dexample)
        if len(examples) < 2: examples.append("")
        ukus = check_ukus(word, pos, synopsis, meaning)
        word, pos, synopsis = identify_phrase(word, pos, synopsis)
        also4 = write_also(word, pos, meaning, also, also_pos, also_syn, also_ex)
        freq = get_frequency(word, ukus, also4)
        row_id = insert_word(conn, [freq, level, word, pos, meaning, synopsis, examples[0], examples[1]])
        if ukus != "": insert_ukus(conn, [row_id, ukus], pos, meaning, synopsis)
        print str(num_level) + '\t' + word + '\t' + pos + '\t' + str(freq) + '\t' + level + '\t' + "[" + synopsis + "]" + '\t' + meaning
        print examples
        state = "head"
        word, pron, also, inflection = parse_headline(line)
        f_words = ""
        num_word += 1
      else:
        if is_sentence(dexample[-1]):
          dexample.append(line)
        elif len(dexample[-1]) > 80:  # sentence not ended
          if dexample[-1][-1] == "-" and dexample[-1][-2] != " ":
            dexample[-1] += line
          else:
            dexample[-1] += " " + line
        else:
          dexample.append(line)
    elif state == "lexample":
      #if word == "become": pdb.set_trace()
      if lexample == "":
        lexample = cleanse_lexample(line)
      elif line.startswith("Learner example"):
        continue
      elif is_headline(line, next_line):
        if lexample != "":
          dexample.append(lexample)
        examples = select_2examples(word, dexample)
        write_sentence(meaning, dexample)
        if len(examples) < 2: examples.append("")
        ukus = check_ukus(word, pos, synopsis, meaning)
        word, pos, synopsis = identify_phrase(word, pos, synopsis)
        also4 = write_also(word, pos, meaning, also, also_pos, also_syn, also_ex)
        freq = get_frequency(word, ukus, also4)
        row_id = insert_word(conn, [freq, level, word, pos, meaning, synopsis, examples[0], examples[1]])
        if ukus != "": insert_ukus(conn, [row_id, ukus], pos, meaning, synopsis)
        print str(num_level) + '\t' + word + '\t' + pos + '\t' + str(freq) + '\t' + level + '\t' + "[" + synopsis + "]" + '\t' + meaning
        print examples
        state = "head"
        word, pron, also, inflection = parse_headline(line)
        f_words = ""
        num_word += 1
      elif is_pos(line):
        if lexample != "":
          dexample.append(lexample)
        examples = select_2examples(word, dexample)
        write_sentence(meaning, dexample)
        if len(examples) < 2: examples.append("")
        ukus = check_ukus(word, pos, synopsis, meaning)
        word_org = word
        word, pos, synopsis = identify_phrase(word, pos, synopsis)
        also4 = write_also(word, pos, meaning, also, also_pos, also_syn, also_ex)
        freq = get_frequency(word, ukus, also4)
        row_id = insert_word(conn, [freq, level, word, pos, meaning, synopsis, examples[0], examples[1]])
        if ukus != "": insert_ukus(conn, [row_id, ukus], pos, meaning, synopsis)
        print str(num_level) + '\t' + word + '\t' + pos + '\t' + str(freq) + '\t' + level + '\t' + "[" + synopsis + "]" + '\t' + meaning
        print examples
        word = word_org
        state = "pos"
        pos, pron_pos, also_pos, inflection_pos, grammar_pos = parse_pos(word, line)
        write_inflection(word, pos, inflection, inflection_pos, grammar_pos)
      elif is_meaning(line):
        if lexample != "":
          dexample.append(lexample)
        examples = select_2examples(word, dexample)
        write_sentence(meaning, dexample)
        if len(examples) < 2: examples.append("")
        ukus = check_ukus(word, pos, synopsis, meaning)
        word_org = word
        pos_org = pos
        word, pos, synopsis = identify_phrase(word, pos, synopsis)
        also4 = write_also(word, pos, meaning, also, also_pos, also_syn, also_ex)
        freq = get_frequency(word, ukus, also4)
        row_id = insert_word(conn, [freq, level, word, pos, meaning, synopsis, examples[0], examples[1]])
        if ukus != "": insert_ukus(conn, [row_id, ukus], pos, meaning, synopsis)
        print str(num_level) + '\t' + word + '\t' + pos + '\t' + str(freq) + '\t' + level + '\t' + "[" + synopsis + "]" + '\t' + meaning
        print examples
        word = word_org
        pos = pos_org
        synopsis = ""
        state = "meaning"
        level, meaning, also_ex, grammar_ex = parse_meaning(line)
        num_level += 1
        lexample = ""
        dexample = []
      elif is_meaning(next_line) and is_sentence(lexample):
        if lexample != "":
          dexample.append(lexample)
        examples = select_2examples(word, dexample)
        write_sentence(meaning, dexample)
        if len(examples) < 2: examples.append("")
        ukus = check_ukus(word, pos, synopsis, meaning)
        word_org = word
        pos_org = pos
        word, pos, synopsis = identify_phrase(word, pos, synopsis)
        also4 = write_also(word, pos, meaning, also, also_pos, also_syn, also_ex)
        freq = get_frequency(word, ukus, also4)
        row_id = insert_word(conn, [freq, level, word, pos, meaning, synopsis, examples[0], examples[1]])
        if ukus != "": insert_ukus(conn, [row_id, ukus], pos, meaning, synopsis)
        print str(num_level) + '\t' + word + '\t' + pos + '\t' + str(freq) + '\t' + level + '\t' + "[" + synopsis + "]" + '\t' + meaning
        print examples
        word = word_org
        pos = pos_org
        state = "synopsis"
        synopsis, also_syn = parse_synopsis(line)
      else:
        if lexample[-1] == "-" and lexample[-2] != " ":
          lexample += cleanse_lexample(line)
        else:
          lexample += " " + cleanse_lexample(line)

  if lexample != "":
    dexample.append(lexample)
  examples = select_2examples(word, dexample)
  write_sentence(meaning, dexample)
  if len(examples) < 2: examples.append("")
  ukus = check_ukus(word, pos, synopsis, meaning)
  word, pos, synopsis = identify_phrase(word, pos, synopsis)
  also4 = write_also(word, pos, meaning, also, also_pos, also_syn, also_ex)
  freq = get_frequency(word, ukus, also4)
  row_id = insert_word(conn, [freq, level, word, pos, meaning, synopsis, examples[0], examples[1]])
  if ukus != "": insert_ukus(conn, [row_id, ukus], pos, meaning, synopsis)
  print str(num_level) + '\t' + word + '\t' + pos + '\t' + str(freq) + '\t' + level + '\t' + "[" + synopsis + "]" + '\t' + meaning
  print examples

  write_also_pass2()

if __name__ == "__main__":
  write_db = False
  write_pickle = False
  dicfile = "A1-C2.txt"
  if len(sys.argv) < 2:
    print "run with db/pickle option for db/pickle creation"
  else:
    if sys.argv[1] == "db":
      write_db = True
    elif sys.argv[1] == "pickle":
      write_pickle = True

  if os.path.exists("../english-inflection/cefr_conjugations.tsv"):
    os.remove("../english-inflection/cefr_conjugations.tsv")
  if os.path.exists("../english-inflection/cefr_plurals.tsv"):
    os.remove("../english-inflection/cefr_plurals.tsv")
  if os.path.exists("../english-inflection/cefr_comparatives.tsv"):
    os.remove("../english-inflection/cefr_comparatives.tsv")
  if os.path.exists("cefr_sentences.txt"):
    os.remove("cefr_sentences.txt")
  if os.path.exists("cefr_also.tsv"):
    os.remove("cefr_also.tsv")

  g1w_word = read_google_frequency("../google/ngrams/count_1w.txt")
  g2w_word = read_google_frequency("../google/ngrams/count_2w.txt")
  cefr_words = {}
  cefr_also_pos_meaning = []
  cefr_word_pos_meaning = []

  if write_db:
    dbfile = "cefr.db"
    if os.path.exists(dbfile):
      os.remove(dbfile)
    conn = create_connection(dbfile)
    if conn is not None:
      create_tables_from_file(conn, "create.sql")
    else:
      pdb.set_trace()
    parse_vocabulary(conn, dicfile)
    conn.close()
  elif write_pickle:
    parse_vocabulary(None, dicfile)
    pickle_file = "cefr_word_pos_meaning.pickle"
    if os.path.exists(pickle_file):
      os.remove(pickle_file)
    with open(pickle_file, 'wb') as f:
      pickle.dump(cefr_word_pos_meaning, f)
  else:
    parse_vocabulary(None, dicfile)
