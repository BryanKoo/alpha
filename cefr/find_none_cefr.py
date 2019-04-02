#-*- encoding: utf-8 -*-
# read cefr words and make inflections
# find meanings that has the headword (usually starts with if or when)
# find words in meanings and examples that are not in cefr
import re
import os, sys
import pdb
import pickle
sys.path.append("../inflection")
from get_conjugation import get_conjugation
from get_plural import get_plural
from get_comparative import get_comparative

reload(sys)
sys.setdefaultencoding('utf-8')

def add_inflections():
  count1 = len(cefr_word_pos_meaning)
  count2 = 0
  inflection_dic = {}
  for word_pos in cefr_word_pos_meaning:
    word = word_pos.split('|')[0]
    pos = word_pos.split('|')[1]
    if word not in inflection_dic:
      inflection_dic[word] = pos

  for word_pos in cefr_word_pos_meaning:
    word = word_pos.split('|')[0]
    pos = word_pos.split('|')[1]
    if word.count(" ") > 0: continue
    inflectable = False
    if pos.startswith("NOUN") or pos.startswith("NUMBER"):
      inflectable = True
      plurals = get_plural(word)[1]
      for plural in plurals:
        if plural[3:] not in inflection_dic:
          inflection_dic[plural[3:]] = pos
          #print word + '\t' + pos + '\t' + plural
          count2 += 1
    if pos.startswith("AD") or pos.startswith("DETER"):
      inflectable = True
      comparatives = get_comparative(word)[1]
      for comparative in comparatives:
        if comparative[3:] not in inflection_dic:
          inflection_dic[comparative[3:]] = pos
          #print word + '\t' + pos + '\t' + comparative
          count2 += 1
    if pos.startswith("VERB") or pos.startswith("AUXILIARY VERB") or pos.startswith("MODAL VERB"):
      inflectable = True
      conjus = get_conjugation(word)[1]
      for conju in conjus:
        if conju[3:] not in inflection_dic:
          inflection_dic[conju[3:]] = pos
          #print word + '\t' +  pos + '\t' + conju
          count2 += 1
    if inflectable == False:
      #print word + '\t' + pos
      pass
  #print count2, "words are added from cefr", count1, "words, total number is", len(inflection_dic)
  return inflection_dic

def is_ordinal(word):
  if len(word) < 3: return False
  if word == "1st" or (word[-3:] == "1st" and word[:-3].isdigit()): return True
  if word == "2nd" or (word[-3:] == "2nd" and word[:-3].isdigit()): return True
  if word == "3rd" or (word[-3:] == "3rd" and word[:-3].isdigit()): return True
  if (word[-2:] == "th" and word[:-2].isdigit()): return True
  return False

def is_number(word):
  if word.isdigit(): return True
  if is_ordinal(word): return True
  return False

def remove_apos(word):
  if word.endswith("n't"):
    return word[:-3]
  elif word.endswith("'s") or word.endswith("’s"):
    return word[:-2]
  elif word.endswith("'m"):
    return word[:-2]
  elif word.endswith("'ll"):
    return word[:-3]
  elif word.endswith("'d"):
    return word[:-2]
  elif word.endswith("'ve"):
    return word[:-3]
  elif word.endswith("'re"):
    return word[:-3]
  elif word.startswith("o'"):
    return word[2:]
  else:
    return word

def remove_symbol(word):
  word = word.replace(".", "")
  word = word.replace("!", "")
  word = word.replace("?", "")
  word = word.replace(",", "")
  word = word.replace(":", "")
  word = word.replace(";", "")
  word = word.replace("'", "")
  word = word.replace('"', "")
  word = word.replace('(', "")
  word = word.replace(')', "")
  word = word.replace('°', "")
  if word == '-ing': word = ""
  return word

def split_words(text):
  result = []
  text = text.replace("/", " ")
  tokens = text.split(" ")
  for token in tokens:
    token = remove_apos(token)
    token = remove_symbol(token).strip()
    if len(token) > 1: result.append(token)
  return result

def none_cefr_meaning(inflection_dic):
  fp = open("none_cefr_meaning.txt", "w")
  not_founds = []
  for word_meaning in cefr_word_pos_meaning:
    word = word_meaning.split('|')[0]
    meaning = word_meaning.split('|')[2]
    tokens = split_words(meaning)
    for token in tokens:
      if token not in inflection_dic and token.lower() not in inflection_dic and not is_number(token) and token not in not_founds:
        if token.count('-') == 0:
          fp.write(token + '\n')
          not_founds.append(token)
        else:
          subs = token.split("-")
          not_found = False
          for sub in subs:
            if len(sub) < 2: continue
            if sub not in inflection_dic and sub.lower() not in inflection_dic and not is_number(sub) and sub not in not_founds:
              not_found = True
          if not_found:
            fp.write(token + '\n')
            not_founds.append(token)
  fp.close()

def none_cefr_sentence(inflection_dic):
  fp = open("none_cefr_sentences.txt", "w")
  not_founds = []
  f = open("cefr_sentences.txt", "r")
  while True:
    line = f.readline()
    if not line: break
    tokens = split_words(line)
    for token in tokens:
      if token not in inflection_dic and token.lower() not in inflection_dic and not is_number(token) and token not in not_founds:
        if token.count('-') == 0:
          fp.write(token + '\n')
          not_founds.append(token)
        else:
          subs = token.split("-")
          not_found = False
          for sub in subs:
            if len(sub) < 2: continue
            if sub not in inflection_dic and sub.lower() not in inflection_dic and not is_number(sub) and sub not in not_founds:
              not_found = True
          if not_found:
            fp.write(token + '\n')
            not_founds.append(token)
  fp.close()

def word_in_meaning(inflection_dic):
  fp = open("word_in_meaning.csv", "w")
  for word_meaning in cefr_word_pos_meaning:
    phrase = ""
    word = word_meaning.split('|')[0]
    if word.count('=') > 0:
      phrase = word.split('=')[1]
      word = word.split('=')[0]
    pos = word_meaning.split('|')[1]
    meaning = word_meaning.split('|')[2]
    inflections = [word]
    if word.count(" ") == 0:
      if pos.startswith("NOUN") or pos.startswith("NUMBER"):
        inflections += get_plural(word)[1]
      if pos.startswith("AD") or pos.startswith("DETER"):
        inflections += get_comparative(word)[1]
      if pos.startswith("VERB") or pos.startswith("AUXILIARY VERB") or pos.startswith("MODAL VERB"):
        inflections += get_conjugation(word)[1]
    words = split_words(meaning)
    found_word = False
    for inflection in inflections:
      for token in words:
        if token == inflection:
          fp.write(word + "\t" + phrase + "\t" + pos + "\t" + meaning + "\n")
          found_word = True
          break
      if found_word: break
  fp.close()

if __name__ == "__main__":
  pickle_file = "cefr_word_pos_meaning.pickle"
  with open(pickle_file, 'rb') as f:
    cefr_word_pos_meaning = pickle.load(f)

  inflection_dic = add_inflections()
  none_cefr_meaning(inflection_dic)
  none_cefr_sentence(inflection_dic)
  word_in_meaning(inflection_dic)
