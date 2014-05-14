# coding=UTF-8
from athena.users import must_be_student
from athena.core import render_to_response
from athena.tests.models import TestResult
from django.contrib import messages
from django.shortcuts import redirect

@must_be_student
def index(request, protocol_id=None):
    """@param protocol_id: TestResult.id or None"""
    
    # prepare test results
    tres = TestResult.objects.filter(written_by=request.user).order_by('-time_of_end')
    
    if protocol_id != None:
        protocol = TestResult.objects.get(id=int(protocol_id))
        if protocol.written_by != request.user: raise Exception
        if not protocol.term.exam.test.can_review_mistakes: raise Exception
            
        proto_e = protocol.get_protocol()
        if proto_e != None:
            percentage = float(proto_e['score']) / float(proto_e['max_score']) * 100.0
        else:
            percentage = None
        exam = protocol.term.exam

        return render_to_response('rstudent/protocol.html', request,
                        results=tres,
                        exam=exam,
                        percentage=percentage,
                        testresult=protocol,
                        protocol=proto_e)
        
    else:
        return render_to_response('rstudent/proto_list.html', request,
                        results=tres)
