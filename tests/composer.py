import random
from collections import defaultdict
from athena.tests.models import Question, Answer
from time import time
from datetime import datetime

class RawTest(object):
    """An object encapsulating possible variations of tests"""
    class NotAllowed(Exception):
        """Operation not allowed at all"""
    class NotAllowedDueToCharacteristic(NotAllowed):
        """Not allowed due to how test was set up"""
    class NotAllowedDueToTime(NotAllowed):
        """Not allowed due to time expiration"""
    class TestFinished(Exception):
        """Test has been finished, this method performed successfully"""

    def __init__(self, test):
        """@type test: tests.models.Test
        Create this object only upon test starting"""
        if not test.is_valid(): raise RawTest.NotAllowed, 'Test invalid'
        q = test.get_questions()

        self.test = test
        self.current_question = 0
        self.questions = q
        self.answers = dict(((x, x.get_permuted_answers()) for x in self.questions))
        self.time_of_question_presentation = None
        self.answers_values = dict((
            (x, [False] * len(self.answers[x]))
            for x in self.questions
        ))

        self.time_remaining_for = dict(((x, x.time or float('inf')) for x in self.questions))

        self.deadline = None

    # Interface hooks
    def on_question_presented(self):
        q = self.questions[self.current_question]
        if not self.time_of_question_presentation:
            self.time_of_question_presentation = time()

        if self.deadline == None:
            if self.test.time != None:
                self.deadline = time() + self.test.time

    def _elect_new_question(self):
        """Advances to next question. Throws RawTest.TestFinished if need be"""
        
        limit_cntr = 0
        while True:
            if (not self.test.can_go_back) and (self.current_question == len(self.questions)-1):
                # We have (not) answered the last question and this is a no-back test
                raise RawTest.TestFinished, 'Answered (not) all questions'

            self.current_question = (self.current_question + 1) % len(self.questions)
            if self.time_remaining_for[self.questions[self.current_question]] > 0:
                break

            limit_cntr += 1
            
            if limit_cntr > len(self.questions):
                raise RawTest.TestFinished, 'Ran out of questions'
            
        self.time_of_question_presentation = None                

    def on_switchto(self, qid):
        """Switches to a question no qid (zero-based numeration)"""
        q = self.questions[self.current_question]
        
        if not self.test.can_go_back: return
        
        if self.deadline:
            if time() > self.deadline:
                raise RawTest.TestFinished, 'Past deadline'
            
        if (qid >= len(self.questions)) or (qid < 0):
            raise Exception, 'Invalid QID %s' % (len(self.questions, ))
            
        if self.time_remaining_for[self.questions[qid]] == 0:
            # Cannot switch to this one!
            return 

        if self.time_of_question_presentation:
            sofar = time() - self.time_of_question_presentation
            self.time_remaining_for[q] -= sofar # decrement remaining time            
        
        self.time_of_question_presentation = None
        self.current_question = qid
                
    def on_heartbeat(self):
        q = self.questions[self.current_question]

        if self.deadline:
            if time() > self.deadline:
                raise RawTest.TestFinished, 'Past deadline'

        if self.time_of_question_presentation:
            sofar = time() - self.time_of_question_presentation
            if sofar > self.time_remaining_for[q]:
                self.time_remaining_for[q] = 0
                # Time for this question expired! Forcing new question
                self._elect_new_question()    

    def on_question_answered(self, *answers):
        """answers is a list of booleans - True or False - which constitute a response
        to answers that are in self.answers in that particular order.

        Throws stuff"""
        
        if self.deadline:
            if time() > self.deadline:
                raise RawTest.TestFinished, 'Past deadline'

        q = self.questions[self.current_question]

        assert self.time_of_question_presentation != None
        
        # Can I answer it due to time constraints?
        sofar = time() - self.time_of_question_presentation
        if sofar > self.time_remaining_for[q]:
            self.time_remaining_for[q] = 0
            self._elect_new_question()
            raise RawTest.NotAllowedDueToTime, 'Answer too late'

        self.time_remaining_for[q] -= sofar # decrement remaining time

        self.answers_values[q] = answers
        # There may be a need to present a new possible answer

        self._elect_new_question()

class TestWritten(object):
    """A complete object containing a test and an interface to it"""

    """This is a test object, to be answered and processed"""
    def __init__(self, test):
        """@type test: athena.tests.models.Test"""

        self.rawtest = RawTest(test)
        self.test_started_on = None         #: public
        self.test_ended_on = None           #: public
        self.is_test_finished = False       #: public
        self.is_test_started = False        #: public
        
    # ----------- AJAX handlers
    def on_heartbeat(self):
        try:
            self.rawtest.on_heartbeat()
        except RawTest.TestFinished:
            self.test_ended_on = datetime.now()
            self.is_test_finished = True
    
    def on_presentation(self):
        self.is_test_started = True
        if self.test_started_on == None:
            self.test_started_on = datetime.now()
        try:
            self.rawtest.on_question_presented()
        except RawTest.TestFinished:
            self.test_ended_on = datetime.now()
            self.is_test_finished = True
    
    def on_answer(self, answers):        
        try:
            self.rawtest.on_question_answered(*answers)
        except RawTest.TestFinished:
            self.test_ended_on = datetime.now()
            self.is_test_finished = True
        
    def on_switchto(self, qid):
        try:
            self.rawtest.on_switchto(qid)
        except RawTest.TestFinished:
            self.test_ended_on = datetime.now()
            self.is_test_finished = True
    
    def on_finish(self):
        self.test_ended_on = datetime.now()
        self.is_test_finished = True
    
    # ----------- protocol maker
    
    def get_total_possible_points(self):
        return reduce(lambda x, y: x+y, [q.points for q in self.rawtest.questions], 0)
    
    def get_points(self):
        """Returns point count. float or int"""
        pts = 0
        for q in self.rawtest.questions:
            # Check answering
            is_right = True
            answer_set = [x.is_right for x in self.rawtest.answers[q]]
            real_answers = self.rawtest.answers_values[q]
            for a, b in zip(answer_set, real_answers):
                is_right = is_right and (a == b)
                
            if is_right:
                pts += q.points
                
        return pts
    
    def get_protocol(self):
        """Returns test protocol. Must be Python-serializable.
        
        Test protocol is a dictionary:
            test_start_on = string::'YYYY-MM-DD HH:MM:SS'
            test_end_on = string::'YYYY-MM-DD HH:MM:SS'
            score = numeric::points gained
            max_score = numeric::maximum points to gain
            questions = array of (
                tuple (
                    unicode::question text,
                    numeric::points to be gained,
                    array of (
                        tuple (
                            bool::student's answer
                            bool::real answer
                            unicode::answer content
                            int::answer id (no one promises it will be up to date upon retrieval)
                        )
                    numeric::points gained
                    int::question id (no one promises it will be up to date upon retrieval)
                    str or null::URL to image or null
                    )
                )                        
            )
        """
        tp = {
              'test_start_on': self.test_started_on.strftime('%Y-%m-%d %H:%M:%S'),
              'test_end_on': self.test_ended_on.strftime('%Y-%m-%d %H:%M:%S'),
              'score': self.get_points(),
              'max_score': self.get_total_possible_points(),
              'questions': []
             }
        
        for q in self.rawtest.questions:
            answerings = []
            all_right = True
            for answer, user_reply in zip(self.rawtest.answers[q], self.rawtest.answers_values[q]):
                answerings.append((user_reply, answer.is_right, answer.content, answer.id))            
                all_right = all_right and (user_reply == answer.is_right)
            
            try:
                atcurl = q.get_attachment_or_None().get_url()
            except:
                atcurl = None
            
            tp['questions'].append((q.content, q.points, answerings, q.points if all_right else 0, q.id, atcurl))
        
        return tp        
    
    # ----------- presentation    
    def get_presentation_info(self):
        """
        Returns info that will be sent to browser as question presentation.

        Browser requires:
            <question content>
            <attachment picture (or none)>
            <time left for this question>
        """

        q = self.rawtest.questions[self.rawtest.current_question]
        qat = q.get_attachment_or_None()

        pi = {
            'question_content': q.content,
            'question_attachment': None if qat == None else qat.get_url(),
            'answers':      # Answers along with 'answered' status
                [
                    (answer.content, is_answered) for answer, is_answered
                        in zip(self.rawtest.answers[q], self.rawtest.answers_values[q])
                ],
            'time_remaining':   # time remaining for this question
                # null if the data is unavailable (means you should report a presentation
                # to receive a value)
                # this is total time remaining for the exam if time is globally determined
                # or remaining time for this question if time is per-question
                None if not self.is_test_started else       # Test not started?
                self.rawtest.deadline - time() if self.rawtest.deadline != None else    # Global time remaining
                self.rawtest.time_remaining_for[q],                     # Time per question       
            'question_id': self.rawtest.current_question,
            'tot_questions': len(self.rawtest.questions),
            'can_go_back': self.rawtest.test.can_go_back,
            'is_multichoice': self.rawtest.test.is_multichoice,
            'testname': self.rawtest.test.name,
            'can_review_mistakes': self.rawtest.test.can_review_mistakes,
            'total_test_time': self.rawtest.test.time,
            'is_deadline_null': self.rawtest.deadline == None
        }
        return pi
