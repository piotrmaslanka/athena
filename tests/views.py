# coding=UTF-8
from athena.rteacher.models import Exam, Term, Group
from athena.tests.models import Test, TestBeingWritten
from athena.users import User, must_be_student
from athena.core import render_to_response
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
import json

@must_be_student
def test(request):
    return render_to_response('tests/test.html', request)

@must_be_student
def ajax(request):
    """Interface to doing a test. Interface is as follows: POST, JSON

    REQUEST ---------------------------------
    command:
                    heartbeat   -   periodical checkup
                    answer      -   a response to a question
                    presented   -   when a question has fully loaded
                    switchto    -   request a switch to a particular question
                    finish      -   end the exam


    answers:        only if command is answer
        JSON, list of booleans that are answers to question, in order they were received
        
    qid:            only if command is switchto
        int, number (zero-based) of question to switch to

    RESPONSE --------------------------------
    
    Response basically contains what should be displayed on-screen right now
    
    status:
                    wait        -   if there is no test for you currently to write
                    finished    -   you finished writing a test
                    content     -   following fields are present, you are writing a test

    question_content:       String, what content is
    question_attachment:    null or URL for a image
    answers:    array of 2-array (answer content, bool whether_its_ticked)
    time_remaining: seconds remaining for this question
    question_id:    number of the question presented (zero-based)
    tot_questions:  total number of questions in this test
    can_go_back:    boolean, whether it is possible to freely pick questions
    is_multichoice: boolean, whether user can pick more than one question
    testname:   string, name of the test base
    term_name: string, name of the term
    exam_name: string, name of the exam

    can_review_mistakes: whether mistakes can be reviewed after the test
    total_test_time: total time in seconds for the exam or null if inferred
    
    grade:  grade with which exam was passed (or not), only if status is finished
"""
    # -------------------------------------------------------------------- Preparatory work
    if request.method != 'POST': return HttpResponse(status=400)        # Must be POST
    try:
        tbw = TestBeingWritten.objects.get(written_by=request.user)
    except TestBeingWritten.DoesNotExist:
        return HttpResponse(json.dumps({'status': 'wait'}), mimetype='application/json')
    
    tw = tbw.get_test_written()
    
    # -------------------------------------------------------------------- Handle the request
    if 'command' not in request.POST: return HttpResponse(status=400)
    
    if request.POST['command'] == 'heartbeat':
        tw.on_heartbeat()
    elif request.POST['command'] == 'presented':
        tw.on_presentation()
    elif request.POST['command'] == 'answer':
        answers = json.loads(request.POST['answers'])
        tw.on_answer(answers)
    elif request.POST['command'] == 'switchto':
        qid = int(request.POST['qid'])
        tw.on_switchto(qid)
    elif request.POST['command'] == 'finish':
        tw.on_finish()
    
    # -------------------------------------------------------------------- Return the data
    tbw.set_test_written(tw)
    
    if tw.is_test_finished:
        tr = tbw.transform_to_TestResult()
        return HttpResponse(json.dumps({'status': 'finished',
                                        'grade': float(tr.grade),
                                        'protocol': tr.id if tbw.term.exam.test.can_review_mistakes else None}), mimetype='application/json')
    else:
        pi = tw.get_presentation_info()
        pi['term_name'] = tbw.term.name
        pi['exam_name'] = tbw.term.exam.name
        pi['status'] = 'content'
        return HttpResponse(json.dumps(pi), mimetype='application/json')

    