# coding=UTF-8
from django.db import models
from hashlib import sha1
from athena.users.models import User
from athena.tests.models import Test

class Group(models.Model):
    teacher = models.ForeignKey(User, related_name='groups_owned')
    name = models.CharField(max_length=30, verbose_name=u'Nazwa')
    description = models.TextField(blank=True, verbose_name=u'Opis')
    is_archival = models.BooleanField(verbose_name=u'Archiwalna?', default=False)
    students = models.ManyToManyField(User)

    created_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_on']

    def __unicode__(self):
        return self.name
    
    @staticmethod
    def get_demo_group():
        """All demo accounts belong to this group"""
        return Group.objects.get(id=1)
        

class JoinRequest(models.Model):
    """A request for teacher to add a student to a group"""
    student = models.ForeignKey(User)
    group = models.ForeignKey(Group)

    reason = models.TextField()

    created_on = models.DateTimeField(auto_now=True)

    def execute(self):
        """Joins the target group. Removes this instance"""
        self.group.students.add(self.student)
        self.delete()

class Exam(models.Model):
    test = models.ForeignKey(Test, verbose_name=u'Wzór testu')
    group = models.ForeignKey(Group, verbose_name=u'Grupa')
    name = models.CharField(max_length=50, verbose_name=u'Nazwa')
    created_on = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, verbose_name='Właściciel')

    class Meta:
        ordering = ['-created_on']

    def is_open(self):
        """Returns whether there is at least one open term"""
        terms = self.term_set.all().only('is_closed')
        for term in terms:
            if not term.is_closed:
                return True
        return False

    def get_passing_testresults(self):
        """Returns an list of all testresults objects from all terms"""
        a = []
        for tres in [term.get_passing_testresults() for term in self.term_set.all()]:
            a.extend(list(tres))
        return a

class Term(models.Model):
    exam = models.ForeignKey(Exam)
    name = models.CharField(max_length=50, verbose_name=u'Nazwa')

    term_time = models.DateTimeField(verbose_name=u'Termin')

    is_closed = models.BooleanField(default=False)
    is_progressing = models.BooleanField(default=False)

    class Meta:
        ordering = ['-term_time']

    def get_passing_testresults(self):
        """Returns an iterator of tests.models.TestResult of students
        that have passed this term"""
        return self.testresult_set.filter(grade__gte=3, is_invalidated=False, is_killed=False)