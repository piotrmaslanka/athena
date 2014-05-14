# coding=UTF-8
from athena.users import User, must_be_teacher
from athena.core import render_to_response
from athena.tests.models import Test, Category, Question, Answer, Attachment
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django import forms
from django.contrib import messages
import json

@must_be_teacher
def list(request):
    return render_to_response('rteacher/tests_list.html', request,
            tests=Test.objects.filter(owner=request.user))

@must_be_teacher
def create(request):

    class NewTestForm(forms.Form):
        name = forms.CharField(label=u'Nazwa')

        can_go_back = forms.BooleanField(label=u'Można się cofać?', required=False)
        is_time_per_question = forms.BooleanField(label=u'Pytania determinują czas', required=False)
        is_multichoice = forms.BooleanField(label=u'Test wielokrotnego wyboru?', required=False)
        can_review_mistakes = forms.BooleanField(label=u'Czy można przejrzeć wyniki?', required=False)
        is_demo = forms.BooleanField(label=u'Dostępne dla konta demonstracyjnego?', required=False)
        
        time = forms.IntegerField(label=u'Czas (w sekundach) na wykonanie', required=False)


        def clean(self):
            data = super(NewTestForm, self).clean()
            try:
                is_time_per_question = data.get('is_time_per_question')
                time = data.get('time')
            except KeyError:
                return data

            if not is_time_per_question:
                try:
                    int(time)
                except:
                    self._errors['time'] = self.error_class([u'Pole wymagane'])

            return data

    if request.method == 'POST':
        form = NewTestForm(request.POST)    

        if form.is_valid():
            t = Test(owner=request.user,
                     name=form.cleaned_data['name'],
                     time=form.cleaned_data['time'],
                     is_demo=form.cleaned_data['is_demo'],
                     can_go_back=form.cleaned_data['can_go_back'],
                     can_review_mistakes=form.cleaned_data['can_review_mistakes'],
                     is_multichoice=form.cleaned_data['is_multichoice'],
                     is_time_per_question=form.cleaned_data['is_time_per_question'])

            t.save()

            messages.add_message(request, messages.SUCCESS, u'Dodano test "%s"' % (t.name, ))
            return redirect('/teacher/tests/%s/' % (t.id, ))

    else:
        form = NewTestForm()

    return render_to_response('rteacher/tests_add.html', request,
                                form=form)


@must_be_teacher
def test_ajax(request, test_id):
    try:
        test = Test.objects.get(id=int(test_id))
    except:
        raise Http404

    if test.owner != request.user: return HttpResponse(status=403)

    if request.POST['operation'] == 'change_time':
        if not test.is_time_per_question:
            try:
                test.time = int(request.POST['time'])
            except:
                pass
            else:
                test.save()

            return HttpResponse('{"value":"%s"}' % (test.time, ), mimetype='application/json')

    elif request.POST['operation'] == 'questions_number':
        try:
            cat = Category.objects.get(id=int(request.POST['category']))
            if cat.test != test: raise Exception
            qn = int(request.POST['questions'])
        except:
            pass
        else:
            cat.question_amount = qn
            cat.save()

            return HttpResponse(json.dumps({'value': cat.question_amount}), mimetype='application/json')

    elif request.POST['operation'] == 'delete_answer':
        #
        #   answer - ID of the answer
        #
        try:
            a = Answer.objects.get(id=int(request.POST['answer']))
            if a.question.category.test != test: raise Exception
        except:
            pass
        else:
            a.delete()
            return HttpResponse('{"success":1}', mimetype='application/json')

    elif request.POST['operation'] == 'create_answer':
        #
        #   question - ID of the question
        #
        try:
            q = Question.objects.get(id=int(request.POST['question']))
            if q.category.test != test: raise Exception
        except:
            pass
        else:
            a = Answer(question=q,
                       content=u'(( wpisz odpowiedź)))',
                       is_right=False)
            a.save()

            return HttpResponse(json.dumps({'value': (a.content, a.is_right),
                                            'id': a.id}), mimetype='application/json')

    elif request.POST['operation'] == 'modify_answer':
        #
        #   answer - ID of the answer
        #   content - text, content of the answer
        #   is_right - 0 or 1, whether this answer is right
        #
        try:
            a = Answer.objects.get(id=int(request.POST['answer']))
            if a.question.category.test != test: raise Exception
            is_right = {0:False, 1:True}[int(request.POST['is_right'])]
            content = request.POST['content']
        except:
            pass
        else:
            is_multichoice = a.question.category.test.is_multichoice

            # if not multichoice and answer is_right then we should zero all others answers
            if not is_multichoice and is_right:
                for answer in a.question.answer_set.all():
                    answer.is_right = False
                    answer.save()

            # update the answer
            a.is_right = is_right
            a.content = content
            a.save()

            return HttpResponse(json.dumps({'value': (a.content, a.is_right),
                                            'id': a.id}), mimetype='application/json')

    return HttpResponse(status=400)

@must_be_teacher
def test(request, test_id):
    try:
        test = Test.objects.get(id=int(test_id))
    except:
        raise Http404

    if test.owner != request.user: return HttpResponse(status=403)


    class TestGradingForm(forms.ModelForm):
        class Meta:
            model = Test
            fields = ('g3_starts_at', 'g35_starts_at', 'g4_starts_at', 'g45_starts_at',
                      'g5_starts_at')
            
    if request.method == 'POST':
        form = TestGradingForm(request.POST, instance=test)
        if form.is_valid():
            messages.add_message(request, messages.SUCCESS, u'Zapisano zmiany')
            form.save()
    else:
        form = TestGradingForm(instance=test)        


    return render_to_response('rteacher/tests_test.html', request,
                                form=form,
                                test=test)

@must_be_teacher
def delete_test(request, test_id):
    try:
        test = Test.objects.get(id=int(test_id))
    except:
        raise Http404

    if test.owner != request.user: return HttpResponse(status=403)

    test.delete()

    return redirect('/teacher/tests/')

@must_be_teacher
def category(request, test_id, category_id):
    try:
        test = Test.objects.get(id=int(test_id))
        category = Category.objects.get(id=int(category_id))
    except:
        raise Http404

    if test.owner != request.user: return HttpResponse(status=403)
    if category.test != test: return HttpResponse(status=403)

    return render_to_response('rteacher/tests_category.html', request,
                                    test=test,
                                    category=category)

@must_be_teacher
def delete_category(request, test_id, category_id):
    try:
        test = Test.objects.get(id=int(test_id))
        category = Category.objects.get(id=int(category_id))
    except:
        raise Http404

    if test.owner != request.user: return HttpResponse(status=403)
    if category.test != test: return HttpResponse(status=403)

    category.delete()

    return redirect('/teacher/tests/%s/' % (test_id, ))

@must_be_teacher
def create_category(request, test_id):    
    try:
        test = Test.objects.get(id=int(test_id))
    except:
        raise Http404

    if test.owner != request.user: return HttpResponse(status=403)

    class NewCategoryForm(forms.Form):
        name = forms.CharField(label=u'Nazwa')

    if request.method == 'POST':
        form = NewCategoryForm(request.POST)

        if form.is_valid():
            c = Category(test=test,
                         name=form.cleaned_data['name'])
            c.save()

            messages.add_message(request, messages.SUCCESS, u'Dodano kategorię "%s"' % (c.name, ))
            return redirect('/teacher/tests/%s/category/%s/' % (test.id, c.id))
    else:
        form = NewCategoryForm()

    return render_to_response('rteacher/tests_category_add.html', request,
                                    test=test,
                                    creating_new_category=True,
                                    form=form)

def create_question(request, test_id, category_id):
    """Creates an empty question and redirects to it's edit page"""
    try:
        test = Test.objects.get(id=int(test_id))
        category = Category.objects.get(id=int(category_id))
    except:
        raise Http404

    if test.owner != request.user: return HttpResponse(status=403)
    if category.test != test: return HttpResponse(status=403)

    q = Question(content=u'(( wpisz treść pytania ))',
                 points=0,
                 category=category)
    q.save()

    messages.add_message(request, messages.SUCCESS, u'Dodano nowe pytanie')

    return redirect('/teacher/tests/%s/category/%s/question/%s/' % (test.id, category.id, q.id))

def question(request, test_id, category_id, question_id):
    try:
        test = Test.objects.get(id=int(test_id))
        category = Category.objects.get(id=int(category_id))
        question = Question.objects.get(id=int(question_id))
    except:
        raise Http404

    if test.owner != request.user: return HttpResponse(status=403)
    if category.test != test: return HttpResponse(status=403)
    if question.category != category: return HttpResponse(status=403)


    class QuestionFormWithTime(forms.ModelForm):
        class Meta:
            model = Question
            exclude = ('category', )
            widgets = {
                'content': forms.Textarea(attrs={'rows': 4})
            }
    class QuestionFormWithoutTime(forms.ModelForm):
        class Meta:
            model = Question
            exclude = ('category', 'time')
            widgets = {
                'content': forms.Textarea(attrs={'rows': 4})
            }

    class ImageForm(forms.Form):
        image = forms.ImageField(label=u'Obrazek')

    TM = {True: QuestionFormWithTime,
          False: QuestionFormWithoutTime}[test.is_time_per_question]


    if (request.method == 'POST') and ('save_content' in request.POST):
        form = TM(request.POST, instance=question)
        if form.is_valid():
            form.save()

        messages.add_message(request, messages.SUCCESS, u'Zapisano zmiany')

    if (request.method == 'POST') and ('delete_image' in request.POST):
        q = question.get_attachment_or_None()
        if q != None:
            q.delete()

            messages.add_message(request, messages.SUCCESS, u'Obrazek usunięty')

    if (request.method == 'POST') and ('delete_question' in request.POST):
        s = redirect('/teacher/tests/%s/category/%s/' % (test.id, category.id))
        question.delete()
        return s

    if (request.method == 'POST') and ('save_image' in request.POST):
        imgform = ImageForm(request.POST, request.FILES)
        if imgform.is_valid():

            q = question.get_attachment_or_None() 

            f = imgform.cleaned_data['image']

            a = Attachment(question=question,
                           description=u'Załącznik',
                           filetype=f.name.split('.')[-1])
            a.save()

            with open(a._get_path(), 'wb+') as destination:     # Save the file
                for chunk in f.chunks():
                    destination.write(chunk)

            if q != None: q.delete()        # delete attachment

            messages.add_message(request, messages.SUCCESS, u'Obrazek zapisany')
    try:
        form
    except:
        form = TM(instance=question)

    try:
        imgform
    except:
        imgform = ImageForm()

    return render_to_response('rteacher/tests_question.html', request,
                        test=test,
                        question=question,
                        category=category,
                        form=form,
                        imgform=imgform)