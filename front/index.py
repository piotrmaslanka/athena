# coding=UTF-8
from athena.core import render_to_response


def about(request):
    return render_to_response('front/about.html', request)

def index(request):
    """Determines user role and redirects him to suitable page"""


    if request.user == None:
        # not logged in
        return render_to_response('front/index.html', request)

    if request.user.status == 0:
        # student
        from athena.rstudent.views import index
        return index(request)

    if request.user.status == 1:
        # student
        from athena.rteacher.views import index
        return index(request)

    if request.user.status == 2:
        # student
        from athena.radmin.views import index
        return index(request)
