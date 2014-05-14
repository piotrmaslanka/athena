from athena.users.models import User
from hashlib import sha1
import types    # for monkeypatching request

def login(self, login, password=None):
    """
    @param self: request
    Returns True if login succeeded.
    If password is None, it is not checked
    """
    try:
        usr = User.objects.get(login=login)
    except User.DoesNotExist:
        return False

    if password != None:
        if not usr.does_password_match(password):
            return False

    self.session['user_id'] = usr.id
    self.user = usr


    self.logout = types.MethodType(logout, self, type(self))

def logout(self):
    """@param self: request"""
    
    if (self.user.is_demo()) and (self.user.status == 0):
        self.user.delete()
    
    self.session.flush()
    self.login = types.MethodType(login, self, type(self))
    self.user = None

class UserMiddleware(object):
    """Middleware that takes care of creating proper
    fields in 'request' object that reflects currently
    logged in user"""

    def process_request(self, request):
        if 'user_id' in request.session:
            # User logged in
            try:
                user = User.objects.get(id=int(request.session['user_id']))
            except:
                logout(request)
            else:
                request.user = user
                request.logout = types.MethodType(logout, request, type(request))
        else:
            # User is logged out
            request.login = types.MethodType(login, request, type(request))
            request.user = None

        return None