# coding=UTF-8
from athena.users import must_be_student
from athena.core import render_to_response
from athena.rteacher import Group, JoinRequest
from athena.tests.models import Test
from django.contrib import messages
from django.shortcuts import redirect

@must_be_student
def index(request):
    return render_to_response('rstudent/index.html', request,
                demos=Test.objects.filter(is_demo=True))

@must_be_student
def join_group(request):
    if request.user.is_demo(): return redirect('/')

    # Calculate groups available for the student to join
    all_groups = set(Group.objects.filter(is_archival=False))
    you_are_in = set(request.user.group_set.all())
    you_want_to_be_in = set([x.group for x in JoinRequest.objects.filter(student=request.user)])
    available_groups = all_groups.difference(you_are_in).difference(you_want_to_be_in)

    if request.method == 'POST':
        # Verify stuff
        try:
            group = Group.objects.get(id=int(request.POST['id']))
            if group not in available_groups: raise Exception
            request.POST['description']
        except:
            return redirect('/groups/join/')

        JoinRequest(student=request.user,
                    group=group,
                    reason=request.POST['description']).save()

        messages.add_message(request, messages.SUCCESS, u'Złożono podanie do grupy "%s"' % (group.name, ))

        return redirect('/groups/')

    return render_to_response('rstudent/groups_join.html', request,
            available=available_groups)

@must_be_student
def groups(request):
    return render_to_response('rstudent/groups.html', request,
            you_are_in=request.user.group_set.all(),
            you_want_to_be_in=JoinRequest.objects.filter(student=request.user))