# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
import sys, datetime
from cefr.make_qna import make_qna_type2or4, get_new_user_id, insert_qna_result

cefr_levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
cefr_text = ['초등학생', '중학교 1,2학년', '중학교 3학년', '고등학교 1,2학년', '고등학교 3학년', '대학생']
# Create your views here.

# selecting level
def index(request):
  context = None
  seg = request.GET.get('seg', '00')
  if 'seg' not in request.session:
    request.session['seg'] = int(seg)
  if seg != '00':
    request.session['seg'] = int(seg)
  if request.GET.get('reset', '0') == '1':
    request.session['level'] = 0
  if 'user_id' not in request.session:
    request.session['user_id'] = get_new_user_id()
  if 'trial' not in request.session:
    request.session['trial'] = 1
  else:
    request.session['trial'] += 1
  if 'level' not in request.session:
    request.session['level'] = 0
  if request.session['level'] == 0:
    request.session['sub_level'] = 6
    request.session['scores'] = ''
    request.session['excepts'] = ''
    return render(request, 'quiz/index.html', context)
  else:
    return redirect("/quiz/" + str(request.session['level']))

# provide question/answer
def detail(request, level):
  if 'user_id' not in request.session:
    request.session['user_id'] = get_new_user_id()
  cefr_level = cefr_levels[int(level)-1]
  level_text = cefr_text[int(level)-1]
  if request.session['sub_level'] > 10: request.session['sub_level'] = 10
  if request.session['sub_level'] < 1: request.session['sub_level'] = 1
  qnas = make_qna_type2or4(cefr_level, request.session['sub_level'], request.session['excepts'])  # quiz type2 or 4
  if len(qnas) < 1:
    qnas = [['word'], ['pos'], ['meaning'], ['question4'], [''], ['answer1', 'answer2', 'answer3']]
  if qnas[0][3] == "":  # type2
    qtype = 2
    request.session['question'] = qnas[0][2]
  else: # type4
    qtype = 4
    request.session['question'] = qnas[0][3]
  num_t = request.session['scores'].count('T')
  num_f = request.session['scores'].count('F')
  context = {'num_t':num_t, 'num_f':num_f, 'qtype':qtype, 'level':level, 'level_text':level_text, 'question':request.session['question'], 'answer1':qnas[0][4][0], 'answer2':qnas[0][4][1], 'answer3':qnas[0][4][2]}
  request.session['answers'] = qnas[0][4][0] + '|' + qnas[0][4][1] + '|' + qnas[0][4][2]
  request.session['word'] = qnas[0][0]
  request.session['a_index'] = qnas[0][5]
  request.session['level'] = level
  return render(request, 'quiz/detail.html', context)

# check answer and set next level
# if wrong, lower sub-level
# if right 3 times, higher sub-level or stop
def results(request, level, choice):
  if 'user_id' not in request.session:
    request.session['user_id'] = get_new_user_id()
  cefr_level = cefr_levels[int(level)-1]
  #choice = request.POST['choice']
  a_index = request.session['a_index']
  word = request.session['word']
  stop_test = False
  if int(choice) == a_index + 1:  # correct
    result = "T"
    request.session['scores'] += 'T'
    if request.session['scores'].endswith('TTT'):
      if request.session['scores'].count('F') == 0:
        request.session['scores'] += '|'
        if request.session['sub_level'] < 10:
          request.session['sub_level'] += 1
        else:
          stop_test = True
          request.session['sub_level'] += 1
      else:
        stop_test = True
  else:
    result = "F"
    if choice != '5':
      request.session['scores'] += 'F'
      if request.session['sub_level'] > 1:
        request.session['sub_level'] -= 1
      else:
        stop_test = True
        request.session['sub_level'] -= 1

  if stop_test:
    request.session['level'] = 0

  if request.session['excepts'] == '':
    request.session['excepts'] = cefr_level + '|' + word
  else:
    request.session['excepts'] += '&' + cefr_level + '|' + word

  if 'seg' not in request.session or request.session['seg'] == "": request.session['seg'] = 0
  if 'trial' not in request.session or request.session['trial'] == "": request.session['trial'] = 1

  text_time = datetime.datetime.now()
  insert_qna_result([request.session['user_id'], request.session['seg'], request.session['trial'], text_time, int(level), request.session['sub_level'], word, request.session['question'], request.session['answers'], result+choice])
  total = request.session['scores'].count('T') + request.session['scores'].count('F')
  n_correct = request.session['scores'].count('T')
  if request.session['sub_level'] > 10 or request.session['sub_level'] < 1:
    level_text = cefr_text[int(level)-1]
  else:
    level_text = cefr_text[int(level)-1] + ' ' + str(request.session['sub_level']*10) + '%'
  context = {'session_level':request.session['level'], 'word':request.session['word'], 'question':request.session['question'].replace("____", request.session['word']), 'seg':request.session['seg'], 'trial':request.session['trial'], 'level':level, 'choice':int(choice), 'a_index':a_index+1, 'total':total, 'n_correct': n_correct, 'sub_level':request.session['sub_level'], 'scores':request.session['scores'], 'excepts':request.session['excepts'], 'stop_test':stop_test, 'level_text':level_text, 'user_id':request.session['user_id']}
  return render(request, 'quiz/results.html', context)
