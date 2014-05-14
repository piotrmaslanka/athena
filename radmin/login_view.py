# coding=UTF-8
from django import forms
from athena.users.models import User
from django.contrib import messages
from django.shortcuts import redirect
from athena.core import render_to_response

def login(request):
    """Handles logging in
    Required by the client. Will only allow teachers and admins to log in"""

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

            if usr.status == 0:
                raise forms.ValidationError(u'Logowanie zabronione')

            return cleaned_data


    if request.method == 'POST':
        rf = LoginForm(request.POST)

        if rf.is_valid():
            request.login(rf.cleaned_data['login'])      # Log in the user

            messages.add_message(request, messages.INFO, u'Zalogowano.')
            return redirect('/')
    else:
        rf = LoginForm()

    return render_to_response('front/login_radmin.html', request, form=rf)    