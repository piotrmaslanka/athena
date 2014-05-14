# coding=UTF-8
from athena.rteacher.models import Exam, Term, Group
from athena.tests.models import Test
from athena.users import User, must_be_teacher
from athena.core import render_to_response
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django import forms
from django.contrib import messages

@must_be_teacher
def list(request):
    """Displays a list of all groups"""
    return render_to_response('rteacher/manage_exams_list.html', request, 
            exams=Exam.objects.filter(owner=request.user)
        )


@must_be_teacher
def exam(request, exam_id):
    try:
        exm = Exam.objects.get(id=int(exam_id))
    except:
        raise Http404

    if exm.group.teacher != request.user:
        return HttpResponse(status=403)

    class ExamForm(forms.ModelForm):
        class Meta:
            model = Exam
            fields = ['name']

    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exm)

        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, u'Zapisano')

    else:
        form = ExamForm(instance=exm)

    return render_to_response('rteacher/manage_exams_exam.html', request, 
            exam=exm,
            selected_exam_id=exm.id,
            exams=Exam.objects.filter(owner=request.user),
            form=form)

@must_be_teacher
def term(request, exam_id, term_id):
    try:
        trm = Term.objects.get(id=int(term_id))
    except:
        raise Http404

    if trm.exam.group.teacher != request.user:
        return HttpResponse(status=403)

    class TermForm(forms.ModelForm):
        class Meta:
            model = Term
            fields = ['name', 'term_time']

    if request.method == 'POST':
        form = TermForm(request.POST, instance=trm)

        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, u'Zapisano')

    else:
        form = TermForm(instance=trm)

    return render_to_response('rteacher/manage_exams_term.html', request, 
            exam=trm.exam,
            term=trm,
            selected_exam_id=trm.exam.id,
            exams=Exam.objects.filter(owner=request.user),
            form=form)

@must_be_teacher
def delete_term(request, exam_id, term_id):
    try:
        trm = Term.objects.get(id=int(term_id))
    except:
        raise Http404

    if trm.exam.group.teacher != request.user:
        return HttpResponse(status=403)

    exam = trm.exam
    trm.delete()

    messages.add_message(request, messages.SUCCESS, u'Termin usunięty')    

    return redirect('/teacher/exams/%s/' % (exam.id, ))

@must_be_teacher
def addterm(request, exam_id):
    try:
        exam = Exam.objects.get(id=int(exam_id))
    except:
        raise Http404

    if exam.group.teacher != request.user:
        return HttpResponse(status=403)

    class NewTermForm(forms.ModelForm):
        class Meta:
            model = Term
            fields = ('name', 'term_time')

        def clean_term_time(self):
            term_time = form.cleaned_data['term_time']
            from datetime import datetime
            if term_time < datetime.now():
                raise forms.ValidationError(u'Termin musi wypadać w przyszłości')
            return term_time

    if request.method == 'POST':
        form = NewTermForm(request.POST)

        if form.is_valid():
            inst = form.instance
            inst.exam = exam
            inst.save()

            messages.add_message(request, messages.SUCCESS, u'Termin utworzony')

            return redirect('/teacher/exams/%s/terms/%s/' % (exam.id, inst.id, ))

    else:
        form = NewTermForm()

    return render_to_response('rteacher/manage_exams_addterm.html', request,
                                    selected_exam_id=exam.id,
                                    form=form,
                                    exam=exam,
                                    exams=Exam.objects.filter(owner=request.user))



@must_be_teacher
def delete(request, exam_id):
    if request.method != 'POST':
        return HttpResponse(status=400)

    try:
        exam = Exam.objects.get(id=int(exam_id))
    except:
        raise Http404

    if exam.group.teacher != request.user:
        return HttpResponse(status=403)


    messages.add_message(request, messages.SUCCESS, u'Egzamin "%s" usunięty' % (exam.name,))

    exam.delete()

    return redirect('/teacher/exams/')    

@must_be_teacher
def create(request):

    class NewExamForm(forms.ModelForm):
        class Meta:
            model = Exam

            exclude = ('owner', )

        def __init__(self, *args, **kwargs):
            tests = kwargs.pop('tests')
            groups = kwargs.pop('groups')
            super(NewExamForm, self).__init__(*args, **kwargs)

            self.fields['test'].queryset = tests
            self.fields['group'].queryset = groups

    tests = Test.objects.filter(owner=request.user)
    groups = Group.objects.filter(teacher=request.user)

    if request.method == 'POST':
        form = NewExamForm(request.POST, tests=tests, groups=groups)

        if form.is_valid():
            form.instance.owner = request.user
            form.save()

            messages.add_message(request, messages.SUCCESS, u'Egzamin utworzony')

            return redirect('/teacher/exams/%s/' % (form.instance.id, ))

    else:
        form = NewExamForm(tests=tests, groups=groups)

    return render_to_response('rteacher/manage_exams_add.html', request,
                                    selected_exam_id='create',
                                    form=form,
                                    exams=Exam.objects.filter(owner=request.user))

