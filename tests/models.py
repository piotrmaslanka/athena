# coding=UTF-8
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import pre_delete
from django.core.exceptions import ValidationError
from athena.settings import ATH_ATTACHMENT_STORAGE_PATH, ATH_ATTACHMENT_SERVING_PATH
from athena.users.models import User
import decimal
import random

class Answer(models.Model):
    """
    An answer for a question
    """
    content = models.TextField()
    is_right = models.BooleanField()    # whether this is a 'good' answer
    question = models.ForeignKey('Question')


class Attachment(models.Model):
    """
    An attachment for a question. May be an attachment, a graphic file, etc.
    """
    description = models.TextField() # Textual description (alt text?)
    filetype = models.TextField() # so far 'png', 'jpg' - file extension
    question = models.ForeignKey('Question')

    def get_url(self):
        return '%s%s.%s' % (ATH_ATTACHMENT_SERVING_PATH, self.id, self.filetype)

    def _get_path(self):
        """Gets on-disk path to attachment"""
        return '%s%s.%s' % (ATH_ATTACHMENT_STORAGE_PATH, self.id, self.filetype)

@receiver(pre_delete, sender=Attachment)
def pre_delete_attachment(sender, **kwargs):
    """Takes care of deleting attachment file from disk"""
    instance, using = kwargs['instance'], kwargs['using']
    import os
    os.unlink(instance._get_path())


class Question(models.Model):
    """
    A single question. Basic settable unit on the exam
    """
    content = models.TextField(verbose_name=u'Treść pytania')
    points = models.FloatField(verbose_name=u'Punktów')
    time = models.IntegerField(null=True, verbose_name=u'Czas w sekundach')  #: Time to answer in seconds, None if not specified
    category = models.ForeignKey('Category')

    def is_valid(self):
        """@return bool, True if this question can be answered with a proper answer"""
        for answer in self.answer_set.all():
            if answer.is_right:
                return True
        return False

    def get_attachment_or_None(self):
        """Usable only when Athena is written to support only one attachment"""
        try:
            return self.attachment_set.all()[0]
        except IndexError:
            return None

    def get_permuted_answers(self):
        x = list(self.answer_set.all())
        from random import shuffle
        shuffle(x)
        return x

class Category(models.Model):
    """
    A question category
    """
    test = models.ForeignKey('Test')
    name = models.TextField()       # name of the category
    question_amount = models.IntegerField(default=0)    # number of questions to draw from this category

    def get_valid_questions(self):
        """Returns a list of valid questions for this category"""
        return [q for q in self.question_set.all() if q.is_valid()]

    def is_valid(self):
        """Check whether a question list can be composed out of this category's questions"""
        if self.question_amount == 0: return False
        return len(self.get_valid_questions()) >= self.question_amount

    def get_random_test_questions(self):
        """Get a proper number of questions for this test. Throws Exception if impossible"""
        vq = self.get_valid_questions()
        if len(vq) < self.question_amount:
            raise ValueError, 'Cannot create: not enough valid questions'
        return random.sample(vq, self.question_amount)

class Test(models.Model):
    """
    A single test
    """
    owner = models.ForeignKey(User)

    name = models.TextField()   # name of the test
    time = models.IntegerField(null=True) #: Time in seconds to complete this test.
                                        # None if this 'is_time_per_question'

    def __unicode__(self):
        return self.name

    can_go_back = models.BooleanField() #: whether answers given earlier can be corrected
    is_time_per_question = models.BooleanField()    #: whether time is assigned for each question
    is_multichoice = models.BooleanField()      #: whether test is a multichoice one
    can_review_mistakes = models.BooleanField() #: whether student can review the test later

    is_demo = models.BooleanField() #: available to demo groups    
    
    # Fields for calculating grade
    g3_starts_at = models.IntegerField(default=50, verbose_name=u'3 zaczyna się od')
    g35_starts_at = models.IntegerField(default=60, verbose_name=u'3,5 zaczyna się od')
    g4_starts_at = models.IntegerField(default=70, verbose_name=u'4 zaczyna się od')
    g45_starts_at = models.IntegerField(default=80, verbose_name=u'4,5 zaczyna się od')
    g5_starts_at = models.IntegerField(default=90, verbose_name=u'5 zaczyna się od')
    
    def grade(self, pctage):
        """Return a score based on this instance settings and a score
        @param pctage: percentage of right answers scored
        @return: value in (5.0, 4.5, 4.0, 3.5, 3.0, 2.0)"""
        if pctage >= self.g5_starts_at: return 5.0
        if pctage >= self.g45_starts_at: return 4.5
        if pctage >= self.g4_starts_at: return 4.0
        if pctage >= self.g35_starts_at: return 3.5
        if pctage >= self.g3_starts_at: return 3.0
        return 2.0
    
    def is_valid(self):
        """Whether a session can be composed out of this test"""
        if self.category_set.count() == 0:
            return False

        for category in self.category_set.all():
            if not category.is_valid():
                return False
        return True

    def get_questions(self):
        """Returns a random list of questions, answering which this exam would consist of.
        Return list will be already permuted"""
        from random import shuffle
        x = []
        for cat in self.category_set.all():
            if cat.is_valid():
                x.extend(cat.get_random_test_questions())
        shuffle(x)
        return x

    def get_valid_categories(self):
        return [cat for cat in self.category_set.all() if cat.is_valid()]

    def clean(self):
        if self.g3_starts_at > self.g35_starts_at:
            raise ValidationError(u'Próg 3,5 musi być nie niższy od progu 3')
        if self.g35_starts_at > self.g4_starts_at:
            raise ValidationError(u'Próg 4 musi być nie niższy od progu 3,5')
        if self.g4_starts_at > self.g45_starts_at:
            raise ValidationError(u'Próg 4,5 musi być nie niższy od progu 4')
        if self.g45_starts_at > self.g5_starts_at:
            raise ValidationError(u'Próg 5 musi być nie niższy od progu 4,5')

class TestBeingWritten(models.Model):
    term = models.ForeignKey('rteacher.Term')
    written_by = models.ForeignKey(User)

    # state contains a Python pickled object, BASE64 encoded. It's internal structure
    # is mandated by tests module.
    state = models.TextField(default='')  

    def get_test_written(self):
        """Returns athena.tests.composer.TestWritten object stored in this object"""
        import base64, cPickle
        return cPickle.loads(base64.b64decode(self.state))

    def set_test_written(self, tw):
        """Store a TestWritten back into database. Saves this instance."""
        import base64, cPickle
        self.state = base64.b64encode(cPickle.dumps(tw, -1))
        self.save()

    def transform_to_TestResult(self):
        """Deletes this instance, and returns a TestResult instance created from this one"""    
        # Attempt a grading
        gtw = self.get_test_written()
        
        # get grade in %
        graderatio = decimal.Decimal(gtw.get_points())/decimal.Decimal(gtw.get_total_possible_points())*100
        
        test = self.term.exam.test
                
        tr = TestResult(term=self.term,
                        written_by=self.written_by,                        
                        grade=test.grade(graderatio))
        tr.save()
        tr.set_protocol(gtw.get_protocol())
        self.delete()
        return tr
        
    def kill(self):
        """Deletes this instance and returns a TestResult instance with killed information"""
        tr = TestResult(term=self.term,
                        written_by=self.written_by,
                        grade='2.0',
                        is_killed=True)
        tr.save()
        self.delete()

class TestResult(models.Model):
    term = models.ForeignKey('rteacher.Term')  
    written_by = models.ForeignKey(User)

    time_of_end = models.DateTimeField(auto_now=True)   # When did the student stop writing
    grade = models.DecimalField(max_digits=2, decimal_places=1)

    # Whether the teacher decided to invalidate this test
    is_invalidated = models.BooleanField(default=False)     # UNUSED
    
    # Whether the teacher decided to kill this test during testing
    is_killed = models.BooleanField(default=False)

    # protocol contains detailed information about answers and grading. Contains a 
    # pickled Python object, BASE64 encoded
    # It's internal structure is mandates by tests module.
        # Empty (zero-length) if killed
    protocol = models.TextField()

    def set_protocol(self, proto):
        import base64, cPickle
        self.protocol = base64.b64encode(cPickle.dumps(proto, -1))
        self.save()        

    def get_protocol(self):
        import base64, cPickle
        try:
            return cPickle.loads(base64.b64decode(self.protocol))
        except:
            return None
        
