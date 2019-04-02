# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
import sys
sys.path.append("../cefr")
from make_qna import make_qna_type2or4

cefr_levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
# Create your views here.
# selecting level
def index(request):
  context = None
  request.session['excepts'] = ''
  request.session['scores'] = ''
  request.session['sub_level'] = 5
  return render(request, 'quiz/index.html', context)

# provide question/answer
def detail(request, level):
  cefr_level = cefr_levels[int(level)-1]
  qnas = make_qna_type2or4(cefr_level, request.session['sub_level'], request.session['excepts'])  # quiz type2 or 4
  if qnas[0][3] == "":  # type2
    context = {'qtype':2, 'level':level, 'question':qnas[0][2], 'answer1':qnas[0][4][0], 'answer2':qnas[0][4][1], 'answer3':qnas[0][4][2]}
  else: # type4
    context = {'qtype':4, 'level':level, 'question':qnas[0][3], 'answer1':qnas[0][4][0], 'answer2':qnas[0][4][1], 'answer3':qnas[0][4][2]}
  request.session['word'] = qnas[0][0]
  request.session['a_index'] = qnas[0][5]
  return render(request, 'quiz/detail.html', context)

# check answer and set next level
# if wrong, lower sub-level
# if right 3 times, higher sub-level or stop
def results(request, level, choice):
  cefr_level = cefr_levels[int(level)-1]
  #choice = request.POST['choice']
  a_index = request.session['a_index']
  word = request.session['word']
  stop_test = False
  if int(choice) == a_index + 1:
    result = "correct"
    request.session['scores'] += 'T'
    if request.session['scores'].endswith('TTT'):
      if request.session['scores'].count('F') == 0:
        request.session['scores'] += '|'
        if request.session['sub_level'] < 10: request.session['sub_level'] += 1
        elif int(level) == 6: stop_test = True
        else:
          level = int(level) + 1
          request.session['sub_level'] = 1
      else: stop_test = True
  else:
    result = "incorrect"
    request.session['scores'] += 'F'
    if request.session['sub_level'] > 1: request.session['sub_level'] -= 1
    elif int(level) == 1: stop_test = True
    else:
      level = int(level) - 1
      request.session['sub_level'] = 10

  if request.session['excepts'] == '':
    request.session['excepts'] = cefr_level + '|' + word
  else:
    request.session['excepts'] += '&' + cefr_level + '|' + word
  total = request.session['scores'].count('T') + request.session['scores'].count('F')
  n_correct = request.session['scores'].count('T')
  levels = ['Beginner', 'Elementary', 'Intermediate', 'Upper Intermediate', 'Advanced', 'Proficient']
  level_text = levels[int(level)-1] + ' ' + str(request.session['sub_level']*10) + '%'
  context = {'level':level, 'choice':int(choice), 'a_index':a_index+1, 'total':total, 'n_correct': n_correct, 'sub_level':request.session['sub_level'], 'scores':request.session['scores'], 'excepts':request.session['excepts'], 'stop_test':stop_test, 'level_text':level_text}
  return render(request, 'quiz/results.html', context)
