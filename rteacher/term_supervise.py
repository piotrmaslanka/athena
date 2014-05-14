# coding=UTF-8
from athena.rteacher.models import Exam, Term, Group
from athena.tests.models import Test, TestBeingWritten, TestResult
from athena.tests.composer import TestWritten
from athena.users import User, must_be_teacher
from athena.core import render_to_response
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django import forms
from django.contrib import messages
import json

@must_be_teacher
def protocol(request, testresult_id):
    tres = get_object_or_404(TestResult, id=int(testresult_id))
    if tres.term.exam.owner != request.user: return HttpResponse(status=403)
    
    proto = tres.get_protocol()
    try:
        percentage = round(float(proto['score']) / float(proto['max_score']) * 100.0, 2)
    except:
        percentage = None
    
    return render_to_response('rteacher/protocol.html', request,
                                    protocol=proto,
                                    percentage=percentage,
                                    testresult=tres,
                                    term=tres.term,
                                    exam=tres.term.exam)

@must_be_teacher
def supervise(request, exam_id, term_id):
    term = Term.objects.get(id=int(term_id))
    if term.exam.id != int(exam_id): raise Exception
    if term.exam.owner != request.user: raise Exception
                
    return render_to_response('rteacher/term_supervise.html', request, 
                                term=term)
    
@must_be_teacher
def ajax(request, exam_id, term_id):
    """
    AJAX interface for supervision
    
    REQUEST -------------------------------------
    
    command:
            refresh     -   returns list of students and their states
            kill        -   kill a particular examination session
            finish      -   finishes the exam, students who did not finished will be killed
            
    session_to_kill: ID of TestBeingWritten to kill, specify only if command kill
            was used
            
    RESPONSE -------------------------------------
    status: ok
    students: array of 6-array (student name, student surname, student number, int status, grade, sessid or protoid)
                appears only if refresh was requested
                status is:
                        0 - waiting to undertake test
                        1 - writing the test
                        2 - finished writing the test
                        3 - test killed
                grade is:
                        null if not available
                        string with grade result
                sessid or protocol id:
                        TestResult ID if student finished or was killed
                        else TestBeingWritten ID to use for killing
                        
            
    """
    if request.method != 'POST': return HttpResponse(status=400)
    if 'command' not in request.POST: return HttpResponse(status=400)        
    term = Term.objects.get(id=int(term_id))
    if term.exam.id != int(exam_id): raise Exception
    if term.exam.owner != request.user: raise Exception
    
    if request.POST['command'] == 'refresh':
        
        stattab = []        # output status table
        
        # Load students who are currrently writing
        for tbw in TestBeingWritten.objects.filter(term=term):
            stattab.append((tbw.written_by.name,
                            tbw.written_by.surname,
                            tbw.written_by.number,
                            1 if tbw.get_test_written().is_test_started else 0,
                            None,
                            tbw.id
                            ))
        # Load students who finished writing
        for tw in TestResult.objects.filter(term=term):
            stattab.append((tw.written_by.name,
                            tw.written_by.surname,
                            tw.written_by.number,
                            3 if tw.is_killed else 2,
                            float(tw.grade),
                            tw.id
                            ))
            
        stattab.sort(key=lambda e: '%s %s' % (e[0], e[1]))
        
        return HttpResponse(json.dumps({'status': 'ok',
                                        'students': stattab}), mimetype='application/json')
    
    elif request.POST['command'] == 'kill':
        tbwtk = TestBeingWritten.objects.get(id=int(request.POST['session_to_kill']))
        if tbwtk.term != term: raise Exception
        
        tbwtk.kill()
        
        return HttpResponse(json.dumps({'status': 'ok'}), mimetype='application/json')
    elif request.POST['command'] == 'finish':
        if term.is_closed: return HttpResponse(status=400)

        for tbw in TestBeingWritten.objects.filter(term=term):
            tbw.kill()
        term.is_closed = True
        term.is_progressing = False
        term.save()
        return HttpResponse(json.dumps({'status': 'ok'}), mimetype='application/json')        