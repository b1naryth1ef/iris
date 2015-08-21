import functools

from flask import *

class Controller(object):
    BASE_PATH = ""

    def __init__(self, parent):
        self.parent = parent
        self.daemon = self.parent.daemon
        self.bp = Blueprint(self.__class__.__name__, __name__, url_prefix=self.BASE_PATH)

class APIBase(Exception):
    pass

class APIResponse(APIBase):
    def __init__(self, data={}):
        self.data = data
        self.data['success'] = True

class APIError(APIBase):
    def __init__(self, msg, code=None):
        self.data = {
            'success': False,
            'msg': msg
        }

        if code:
            self.data['code'] = code

def require(obj, *fields, **typed_fields):
    # First, check untyped fields
    missing = set(fields + tuple(typed_fields.keys())) - set(list(obj.keys()))
    if len(missing):
        raise APIError("Missing required fields: {}".format(', '.join(missing)))

    result = {k: v for k, v in obj.items() if k in (fields + tuple(typed_fields.keys()))}

    for name, typ in typed_fields.items():
        if not isinstance(obj[name], typ):
            try:
                result[name] = typ(obj[name])
            except:
                raise APIError("Invalid type for field {} (is {}, should be {})".format(
                    name, type(obj[name]), typ
                ))
    return result

def with_object(obj):
    def deco(f):
        @functools.wraps(f)
        def _f(self, *args, **kwargs):
            try:
                a = obj.get(obj.id == kwargs['id'])
            except obj.DoesNotExist:
                raise APIError("Invalid {} ID".format(obj.__name__))
            del kwargs['id']
            return f(self, a, *args, **kwargs)
        return _f
    return deco
