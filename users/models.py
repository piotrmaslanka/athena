# coding=UTF-8
from django.db import models
from hashlib import sha1

USER_STATUS = (
    (0, u'Student'),
    (1, u'Nauczyciel'),
    (2, u'Administrator'),
)

class User(models.Model):
    name = models.TextField(blank=True, verbose_name=u'Imię')
    surname = models.TextField(blank=True, verbose_name=u'Nazwisko')

    login = models.EmailField(max_length=254, db_index=True)        # also an email
    password = models.CharField(max_length=40, default='')  # computed as SHA1(login+password in utf).hexdigest()

    status = models.IntegerField(choices=USER_STATUS, default=0)

    number = models.IntegerField(null=True, blank=True, verbose_name=u'Nr albumu')

    created_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['login']

    def is_demo(self):
        """Returns whether this is a demo student or a 'baseline' account teacher"""
        return self.login.split('@')[1] == 'demo.athena'
    
    def does_password_match(self, pwd):
        """Checks whether supplied password matches this account's password"""
        y = sha1(self.login.encode('utf8')+pwd.encode('utf8')).hexdigest()
        return self.password == y

    def set_password(self, newpwd):
        """Saves this instance"""
        self.password = sha1(self.login.encode('utf8')+newpwd.encode('utf8')).hexdigest()
        self.save()
