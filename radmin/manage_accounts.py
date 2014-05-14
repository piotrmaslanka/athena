# coding=UTF-8
"""
View for managing accounts
"""

from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django import forms
from athena.core import render_to_response
from athena.users.models import User
from athena.users import must_be_admin


def klist(**kwargs):
    kwargs.update({
        'teachers': [x for x in User.objects.filter(status=1) if not x.is_demo()],
        'admins': User.objects.filter(status=2),
    })
    return kwargs


@must_be_admin
def list(request):
    return render_to_response('radmin/manage_accounts_list.html', request, **klist())

@must_be_admin
def account(request, account_id):
    try:
        acc = User.objects.get(id=int(account_id))
    except:
        raise Http404

    class AccountBaseForm(forms.ModelForm):
        class Meta:
            model = User
            fields = ['name', 'surname', 'number']
            widgets = {
                'name': forms.TextInput(),
                'surname': forms.TextInput(),
            }

    if request.method == 'POST':
        form = AccountBaseForm(request.POST, instance=acc)

        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, u'Zapisano.')

    else:
        form = AccountBaseForm(instance=acc)

    if acc.status != 0:
        return render_to_response('radmin/manage_accounts_acc.html', request, **klist(
                account=acc,
                selected_user_id=acc.id,
                form=form))
    else:
        return render_to_response('radmin/manage_accounts_students_acc.html', request,
                account=acc,
                selected_user_id=acc.id,
                form=form,
                page=Paginator(User.objects.filter(status=0).order_by('surname', 'name'), 30).page(1))


@must_be_admin
def reset_pwd(request, account_id):
    if request.method != 'POST':
        return HttpResponse(status=400)

    try:
        acc = User.objects.get(id=int(account_id))
    except:
        raise Http404

    from random import choice
    randompass = ''.join([choice('1234567890qwertyupasdfghjklzxcvbnm') for i in range(7)])

    acc.set_password(randompass)

    messages.add_message(request, messages.SUCCESS, u'Nowe hasło to %s' % (randompass, ))

    return redirect('/admin/accounts/%s/' % (acc.id, ))


@must_be_admin
def su(request, account_id):
    """Login as this user"""
    if request.method != 'POST':
        return HttpResponse(status=400)

    try:
        acc = User.objects.get(id=int(account_id))
    except:
        raise Http404

    request.logout()
    request.login(acc.login)

    messages.add_message(request, messages.SUCCESS, u'Zalogowano jako %s' % (acc.login, ))

    return redirect('/')

@must_be_admin
def delete(request, account_id):
    if request.method != 'POST':
        return HttpResponse(status=400)

    try:
        acc = User.objects.get(id=int(account_id))
    except:
        raise Http404

    if acc.login in ('demo@example.com', 'teacher@example.com', 'root@example.com'):
        messages.add_message(request, messages.ERROR, u'Nie można usunąć konta wbudowanego')
        return redirect('/admin/accounts/%s/' % (acc.id, ))

    if acc.status == 1:
        # This is a teacher. You should reparent all of it's tests
        # and groups to user to teacher@example.com
        pass

    messages.add_message(request, messages.SUCCESS, u'Konto "%s %s" usunięte.' % (acc.name, acc.surname))

    acc.delete()

    return redirect('/admin/accounts/')


@must_be_admin
def create(request):

    class NewAccountForm(forms.Form):
        _CHOICE = ((1, 'Nauczyciel'), (2, 'Adminstrator'))
        login = forms.EmailField(label=u'E-mail')
        name = forms.CharField(label=u'Imię', required=False)    
        surname = forms.CharField(label=u'Nazwisko', required=False)
        status = forms.ChoiceField(choices=_CHOICE, initial=1, label=u'Typ')

    if request.method == 'POST':
        form = NewAccountForm(request.POST)

        if form.is_valid():

            # grab a random password
            from random import choice
            randompass = ''.join([choice('1234567890qwertyupasdfghjklzxcvbnm') for i in range(7)])

            u = User(login=form.cleaned_data['login'],
                     name=form.cleaned_data['name'],
                     surname=form.cleaned_data['surname'],
                     status=form.cleaned_data['status'])
            u.save()
            u.set_password(randompass)

            messages.add_message(request, messages.SUCCESS, u'Konto stworzone. Nowe hasło to %s' % (randompass, ))

            return redirect('/admin/accounts/%s/' % (u.id, ))

    else:
        form = NewAccountForm()

    return render_to_response('radmin/manage_accounts_add.html', request, **klist(
                                    selected_user_id='create',
                                    form=form))

from django.core.paginator import Paginator

@must_be_admin
def view_students(request, page='1'):
    page = int(page)
    students = User.objects.filter(status=0).order_by('surname', 'name')
    students = [x for x in students if not x.is_demo()]
    p = Paginator(students, 30)

    cpage = p.page(page)

    return render_to_response('radmin/manage_accounts_students_list.html', request,
                                    page=cpage)