# coding=UTF-8
from athena.users import must_be_demo_student
from athena.core import render_to_response
from athena.tests.models import Test, TestBeingWritten, TestResult
from athena.rteacher.models import Exam, Term, Group
from django.contrib import messages
from django.shortcuts import redirect
from athena.tests.composer import TestWritten
from django.http import HttpResponse
from datetime import datetime

@must_be_demo_student
def start_demo_exam(request, test_id):
    demogrp = Group.get_demo_group()
    test = Test.objects.get(id=int(test_id))
    if not test.is_demo: return HttpResponse(status=400)
    
    # Is the student writing an exam right now?
    try:
        tbw = TestBeingWritten.objects.get(written_by=request.user)
    except TestBeingWritten.DoesNotExist:
        pass
    else:
        messages.add_message(request, messages.ERROR, u'Egzamin już jest pisany!')
        
    # Try to automatically detect an exam and term for this one, a demo one
    try:
        exam = Exam.objects.get(test=test, group=demogrp)
    except Exam.DoesNotExist:
        exam = Exam(test=test, group=demogrp, name=u'DEMO EGZAMIN', owner=demogrp.teacher)
        exam.save()
        
    # Fetch term for this one
    try:
        term = exam.term_set.all()[0]
    except:
        term = Term(exam=exam, name=u'DEMO TERMIN', term_time=datetime.now(),
                    is_progressing=True)
        term.save()

    # Create a TBW for this student now
    tbw = TestBeingWritten(term=term, written_by=request.user)
    tbw.save()
    tbw.set_test_written(TestWritten(test)) 
    
    return redirect('/test/')