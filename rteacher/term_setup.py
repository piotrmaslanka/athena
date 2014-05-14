# coding=UTF-8
from athena.rteacher.models import Exam, Term, Group
from athena.tests.models import Test, TestBeingWritten
from athena.tests.composer import TestWritten
from athena.users import User, must_be_teacher
from athena.core import render_to_response
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django import forms
from django.contrib import messages
import json

def get_applicable_students(term, dont_sort=False):
    """Returns a list of students allowed to write this term.
    List is sorted by name+surname, ascending"""

    all_students = set(term.exam.group.students.all())
    excluded_students = set([x.written_by for x in term.exam.get_passing_testresults()])
    result = list(all_students - excluded_students)
    
    def is_writing_exam(stud):
        try:
            TestBeingWritten.objects.get(written_by=student)
        except TestBeingWritten.DoesNotExist:
            return False
        else:
            return True

    result = [student for student in result if not is_writing_exam(student)]
    
    if not dont_sort:
        return sorted(result, key=lambda x: u'%s %s' % (x.name, x.surname))
    else:
        return result

@must_be_teacher
def setup_ajax(request, exam_id, term_id):
    """POST variable 'students' should be a JSON-encoded list of student IDs 
    to partake in the test"""

    if 'students' not in request.POST: raise HttpResponse(status=400)

    try:
        trm = Term.objects.get(id=int(term_id))
    except:
        raise Http404

    if trm.exam.group.teacher != request.user:
        return HttpResponse(status=403)
    
    # Ok, now we will take those students take these damn exams
    try:
        students = set([User.objects.get(id=x) for x in json.loads(request.POST['students'])])
    except User.DoesNotExist:
        return HttpResponse(status=400)
    
    applicable_students = set(get_applicable_students(trm, dont_sort=True))
    
    if not students.issubset(applicable_students):
        return HttpResponse(status=403)
    
    # Students can attempt writing exams!
    for student in students:
        tbw = TestBeingWritten(term=trm, written_by=student)
        tbw.save()
        tbw.set_test_written(TestWritten(trm.exam.test))
        
    trm.is_progressing = True
    trm.save()
    
    # all ready, redirect to supervision
    return redirect('/teacher/exams/%s/terms/%s/supervise/' % (trm.exam.id, trm.id))

@must_be_teacher
def setup(request, exam_id, term_id):
    try:
        trm = Term.objects.get(id=int(term_id))
    except:
        raise Http404

    if trm.exam.group.teacher != request.user:
        return HttpResponse(status=403)

    if trm.is_closed or trm.is_progressing: 
        return HttpResponse(status=400)       

    return render_to_response('rteacher/term_setup.html', request,
            term=trm,
            exam=trm.exam,
            students=get_applicable_students(trm))
