from athena.users import must_be_teacher
from athena.core import render_to_response

@must_be_teacher
def index(request):
    return render_to_response('rteacher/index.html', request)