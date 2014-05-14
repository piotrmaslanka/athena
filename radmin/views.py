from athena.users import must_be_admin
from athena.core import render_to_response

@must_be_admin
def index(request):
    return render_to_response('radmin/index.html', request)