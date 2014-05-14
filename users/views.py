# coding=UTF-8
from django import forms
from athena.users.models import User
from athena.rteacher.models import Group
from django.contrib import messages
from django.shortcuts import redirect
from athena.core import render_to_response
from athena.users import must_be_logged, must_not_be_logged
from datetime import datetime, timedelta
from random import randint

@must_be_logged
def profile(request):
    
    class ProfileForm(forms.ModelForm):
        class Meta:
            model = User
            
    class ChangePasswordForm(forms.Form):
        current_pwd = forms.CharField(widget=forms.PasswordInput, label=u'Aktualne hasło')
        new_pwd = forms.CharField(widget=forms.PasswordInput, label=u'Nowe hasło')
        new_pwd2 = forms.CharField(widget=forms.PasswordInput, label=u'Potwierdź nowe')
    
        def __init__(self, request, *args, **kwargs):
            super(ChangePasswordForm, self).__init__(*args, **kwargs)
            self.user = request.user
    
        def clean(self):
            cleaned_data = super(ChangePasswordForm, self).clean()
            if not self.user.does_password_match(cleaned_data['current_pwd']):
                raise forms.ValidationError(u'Błędne hasło aktualne')
            
            if cleaned_data['new_pwd'] != cleaned_data['new_pwd2']:
                raise forms.ValidationError(u'Hasła nie zgadzają się!')
                
            return cleaned_data

    if request.method == 'POST':
        cpf = ChangePasswordForm(request, request.POST)
        if cpf.is_valid():
            request.user.set_password(cpf.cleaned_data['new_pwd'])
            messages.add_message(request, messages.SUCCESS, u'Hasło zmienione.')
    else:
        cpf = ChangePasswordForm(request)
    
    return render_to_response('profile.html', request, cpf=cpf)

@must_not_be_logged
def demo(request):
    """Logs in a demo user"""
    # Check if it's possible to login
    if User.objects.filter(login__endswith='@demo.athena').count() > 1000:
        
        # Attempt to remove superficial accounts
        k = User.objects.filter(status=1, login__endswith='@demo.athena') \
                        .filter(created_on__lt=datetime.now() - timedelta(1))
        for x in k: x.delete()
            
        if User.objects.filter(login__endswith='@demo.athena').count() > 1000:
            messages.add_message(request, messages.ERROR, u'Błąd: przeciążenie systemu')
            return redirect('/')
    
    target_login = '%s@demo.athena' % (randint(0, 10000000))
        
    su = User(name='Tymczasowe konto DEMO', surname='', login=target_login, number=0)
    su.save()
    Group.get_demo_group().students.add(su)

    request.login(target_login)
    
    messages.add_message(request, messages.INFO, u'Zalogowano demonstracyjnie.')

    return redirect('/')
    
@must_not_be_logged    
def login(request):
    """Handles logging in"""

    class LoginForm(forms.Form):

        login = forms.EmailField(max_length=254, label=u'Email')
        password = forms.CharField(widget=forms.PasswordInput, label=u'Hasło', required=True)

        def clean(self):
            cleaned_data = super(LoginForm, self).clean()

            login, password = cleaned_data.get('login'), cleaned_data.get('password')

            if not login: return cleaned_data
            if not password: return cleaned_data

            try:
                usr = User.objects.get(login=login)
            except User.DoesNotExist:
                raise forms.ValidationError(u'Nie ma takiego użytkownika')

            if not usr.does_password_match(password):
                raise forms.ValidationError(u'Błędne hasło')

            if usr.status > 0:
                raise forms.ValidationError(u'Logowanie zabronione')

            return cleaned_data

    if request.method == 'POST':
        rf = LoginForm(request.POST)

        if rf.is_valid():
            request.login(rf.cleaned_data['login'])      # Log in the user

            messages.add_message(request, messages.SUCCESS, u'Zalogowano.')
            return redirect('/')
    else:
        rf = LoginForm()

    return render_to_response('front/login.html', request, form=rf)    

#=======================================================================================
@must_not_be_logged
def register(request):
    """Handles registering new students only"""

    class RegisterForm(forms.Form):

        name = forms.CharField(label=u'Imię')
        surname = forms.CharField(label=u'Nazwisko')

        login = forms.EmailField(max_length=254, label=u'Email')

        album = forms.IntegerField(label=u'Nr albumu')

        password = forms.CharField(widget=forms.PasswordInput, label=u'Hasło', required=True)
        password2 = forms.CharField(widget=forms.PasswordInput, label=u'Powtórz hasło', required=True)


        def clean_login(self):
            """Assure login is unique"""
            lgn = self.cleaned_data['login']
            try:
                usr = User.objects.get(login=lgn)
            except User.DoesNotExist:
                return lgn
            raise forms.ValidationError(u'Taki e-mail jest już używany!')

        def clean(self):
            """Assure passwords match"""
            cleaned_data = super(RegisterForm, self).clean()

            pwd1 = cleaned_data.get('password')
            pwd2 = cleaned_data.get('password2')

            if pwd1 != pwd2:
                self._errors['password'] = self.error_class(['Niezgodne hasła'])
                self._errors['password2'] = self.error_class(['Niezgodne hasła'])

                del cleaned_data['password']
                del cleaned_data['password2']

            return cleaned_data


    if request.method == 'POST':
        rf = RegisterForm(request.POST)

        if rf.is_valid():

            # Create an account
            u = User(name=rf.cleaned_data['name'],
                     surname=rf.cleaned_data['surname'],
                     login=rf.cleaned_data['login'],
                     number=rf.cleaned_data['album'])
            u.save()
            u.set_password(rf.cleaned_data['password'])

            request.login(u.login)      # Log in the user

            messages.add_message(request, messages.INFO, u'Utworzono nowe konto. Zostałeś zalogowany.')
            return redirect('/')
    else:
        rf = RegisterForm()

    return render_to_response('front/register.html', request, form=rf)

#=======================================================================================
@must_be_logged
def logout(request):
    """Handles logging out"""
    if request.user:
        request.logout()
        messages.add_message(request, messages.INFO, u'Wylogowano.')
    
    return redirect('/')