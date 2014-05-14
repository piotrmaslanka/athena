from athena.users.models import User
from django.shortcuts import redirect

def must_be_student(func):
    def f(request, *args, **kwargs):
        if request.user == None:
            return redirect('/')
        if request.user.status != 0:
            return redirect('/')

        return func(request, *args, **kwargs)
    return f

def must_be_logged(func):
    def f(request, *args, **kwargs):
        if request.user == None:
            return redirect('/')

        return func(request, *args, **kwargs)
    return f    
    
def must_not_be_logged(func):
    def f(request, *args, **kwargs):
        if request.user != None:
            return redirect('/')

        return func(request, *args, **kwargs)
    return f      

def must_be_demo_student(func):
    def f(request, *args, **kwargs):
        if request.user == None:
            return redirect('/')
        if request.user.status != 0:
            return redirect('/')
        if not request.user.is_demo():
            return redirect('/')            

        return func(request, *args, **kwargs)
    return f

def must_be_teacher(func):
    def f(request, *args, **kwargs):
        if request.user == None:
            return redirect('/')
        if request.user.status != 1:
            return redirect('/')

        return func(request, *args, **kwargs)
    return f    

def must_be_admin(func):
    def f(request, *args, **kwargs):
        if request.user == None:
            return redirect('/')
        if request.user.status != 2:
            return redirect('/')

        return func(request, *args, **kwargs)
    return f    