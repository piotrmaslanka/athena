# coding=UTF-8
from athena.rteacher import Group, JoinRequest
from athena.users import User, must_be_teacher
from athena.core import render_to_response
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django import forms
from django.contrib import messages

def klist(**kwargs):
    request = kwargs['request']
    kwargs.update({
            'archival': Group.objects.filter(is_archival=True, teacher=request.user),
            'current': Group.objects.filter(is_archival=False, teacher=request.user)
        })
    del kwargs['request']

    return kwargs

@must_be_teacher
def list(request):
    """Displays a list of all groups"""
    return render_to_response('rteacher/manage_groups_list.html', request, **klist(
            request=request
        ))

@must_be_teacher
def group(request, group_id):
    try:
        grp = Group.objects.get(id=int(group_id))
    except:
        raise Http404

    if grp.teacher != request.user:
        return HttpResponse(status=403)

    class GroupForm(forms.ModelForm):
        class Meta:
            model = Group
            fields = ['name', 'description', 'is_archival']

    if request.method == 'POST':
        form = GroupForm(request.POST, instance=grp)

        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, u'Zapisano')

    else:
        form = GroupForm(instance=grp)

    return render_to_response('rteacher/manage_groups_grp.html', request, **klist(
            group=grp,
            request=request,
            form=form))



@must_be_teacher
def members(request, group_id):
    try:
        grp = Group.objects.get(id=int(group_id))
    except:
        raise Http404

    if grp.teacher != request.user:
        return HttpResponse(status=403)

    if request.method == 'POST':
        try:
            student = User.objects.get(id=int(request.POST['user_id']))
            grp.students.remove(student)
        except:
            return redirect('/teacher/groups/%s/members/' % (grp.id, ))

        messages.add_message(request, messages.SUCCESS, u'Usunięto studenta z grupy')
        return redirect('/teacher/groups/%s/members/' % (grp.id, ))


    return render_to_response('rteacher/manage_groups_members.html', request, **klist(
                                    selected_group_id=grp.id,
                                    request=request,
                                    group=grp))

@must_be_teacher
def requests(request, group_id):
    try:
        grp = Group.objects.get(id=int(group_id))
    except:
        raise Http404

    if grp.teacher != request.user:
        return HttpResponse(status=403)

    if request.method == 'POST':
        try:
            jr = JoinRequest.objects.get(id=int(request.POST['request_id']))
            request.POST['action']
            if jr.group != grp: raise Exception
        except:
            return redirect('/teacher/groups/%s/requests/' % (grp.id, ))

        if request.POST['action'] == 'confirm':
            jr.execute()
            messages.add_message(request, messages.SUCCESS, u'Zaakceptowano')
        else:
            jr.delete()
            messages.add_message(request, messages.SUCCESS, u'Usunięto wniosek')

        return redirect('/teacher/groups/%s/requests/' % (grp.id, ))


    return render_to_response('rteacher/manage_groups_requests.html', request, **klist(
                                    selected_group_id=grp.id,
                                    request=request,
                                    group=grp))   


@must_be_teacher
def create(request):

    class NewGroupForm(forms.Form):
        name = forms.CharField(max_length=30, label=u'Nazwa')
        description = forms.CharField(required=True, label=u'Opis', widget=forms.TextInput())

    if request.method == 'POST':
        form = NewGroupForm(request.POST)

        if form.is_valid():

            g = Group(teacher=request.user,
                     name=form.cleaned_data['name'],
                     description=form.cleaned_data['description'])
            g.save()

            messages.add_message(request, messages.SUCCESS, u'Grupa utworzona')

            return redirect('/teacher/groups/%s/' % (g.id, ))

    else:
        form = NewGroupForm()

    return render_to_response('rteacher/manage_groups_add.html', request, **klist(
                                    selected_group_id='create',
                                    request=request,
                                    form=form))


@must_be_teacher
def delete(request, group_id):
    if request.method != 'POST':
        return HttpResponse(status=400)

    try:
        grp = Group.objects.get(id=int(group_id))
    except:
        raise Http404

    if grp.teacher != request.user:
        return HttpResponse(status=403)


    messages.add_message(request, messages.SUCCESS, u'Grupa "%s" usunięta' % (grp.name,))

    grp.delete()

    return redirect('/teacher/groups/')    