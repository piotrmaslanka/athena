"""Common properties and methods"""

from django.shortcuts import render_to_response as X
from django.template import RequestContext
from time import time

def render_to_response(template_path, request, **kwargs):
    kwargs['request'] = request
    kwargs['current_server_timestamp'] = time()

    return X(template_path, kwargs, context_instance=RequestContext(request))