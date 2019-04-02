#-*- encoding: utf-8 -*-
import json
import re
import pickle
import os, sys
import pdb
reload(sys)
sys.setdefaultencoding('utf-8')

def read_ukus(ufile):
  uf = open(ufile, 'r')
  while True:
    line = uf.readline()
    if not line: break
    tokens = line.split('\t')
    uk = tokens[0].strip()
    if uk == "UK": continue
    only = tokens[3].strip()
    whether = tokens[4].strip()
    us = tokens[1].strip()
    if uk not in ukus_words:
      ukus_words[uk] = us
      ukus_whether[uk] = whether
      ukus_only[uk] = only

def check_ukus(word, pos, synopsis, meaning):
  pos = pos.lower()
  synopsis = synopsis.lower()
  if word in ukus_words or word.replace("-", " ") in ukus_words:
    count_us = 0
    if word not in ukus_words: word = word.replace("-", " ")
    if ukus_whether[word] == "NA":
      pass
    elif ukus_only[word] != "":
      if ukus_only[word] == "noun" or ukus_only[word] == "verb":
        if pos.startswith(ukus_only[word]):
          #print word, "only to", ukus_only[word], pos, "applicable", ukus_words[word]
          return ukus_words[word]
        else:
          pass
      elif synopsis.count(ukus_only[word]) > 0:
        #print word, "only to", ukus_only[word], synopsis, "applicable", ukus_words[word]
        return ukus_words[word]
      else:
        pass
    else:
      return ukus_words[word]
      #print word, "\t", ukus_words[word], "\t", pos, "\t", meaning
  return ""

def check_voca(cfile):
  cf = open(cfile, 'r')
  while True:
    line = cf.readline()
    if not line: break
    tokens = line.split('\t')
    if len(tokens) < 2: pdb.set_trace()
    word = tokens[1].strip()
    pos = tokens[2].strip()
    synopsis = tokens[5].strip()
    meaning = tokens[6].strip()
    ukus = check_ukus(word, pos, synopsis, meaning)
    if ukus != "":
      print word, ukus, pos, synopsis, meaning

ukus_words = {}
ukus_whether = {}
ukus_only = {}
read_ukus("../general/ukus/uk_us_spells_spellzone.csv")
read_ukus("../general/ukus/uk_us_terms_oxford.csv")

if __name__ == "__main__":
  check_voca("cefr.tsv")
