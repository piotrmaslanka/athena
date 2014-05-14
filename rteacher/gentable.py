"""Generates a table about people passing the exam (or not)"""
# coding=UTF-8
from athena.rteacher.models import Exam, Term, Group
from athena.tests.models import TestResult
from athena.users import User, must_be_teacher
from athena.core import render_to_response
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django import forms
from django.contrib import messages
import json

@must_be_teacher
def gentable(request, exam_id):
    exam = Exam.objects.get(id=int(exam_id))
    # Gotta get all people that written that and their results
    written = set()
    results = set()
    terms = list(exam.term_set.all().order_by('term_time'))
    for term in terms:
        s = list(term.testresult_set.all())
        results = results.union(s)
        written = written.union([x.written_by for x in s])
        
    written = list(written)
    written.sort(key=lambda x: u'%s %s' % (x.name, x.surname))

    def lutfor(user, term):
        """Return None if not present or grade"""
        for res in results:
            if (res.written_by == user) and (res.term == term):
                return res.grade
             
    xtab = [] # list of list (surname, name, number, list of (grades for respective terms))
    for user in written:
        grades = [lutfor(user, term) for term in terms]
        xtab.append([user.surname, user.name, user.number, grades])
        
    return render_to_response('rteacher/gentable.html', request,
                                exam=exam,
                                xtab=xtab,
                                terms=terms,
                                writers=written)
    
        