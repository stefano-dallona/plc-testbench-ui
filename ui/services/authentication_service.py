from functools import wraps
from flask import request, abort
from google.auth import jwt
from google.auth.exceptions import *
import requests
import os

from ..models.user import User

class MissingTokenException(Exception):
    pass

class TokenDecodingException(Exception):
    pass

class TokenExpiredException(Exception):
    pass

def get_google_certs():
    headers = {'Accept': 'application/json'}
    r = requests.get(os.environ.get("GOOGLE_OAUTH_CERTS"), headers=headers)
    certs = r.json()
    return certs

def get_user_from_jwt_token(token) -> User:
    security_enabled = eval(os.environ.get("SECURITY_ENABLED")) if "SECURITY_ENABLED" in os.environ.keys() else False
    
    if not security_enabled:
        return User(id_=None, name="anonymus", email="anonymus@plctestbench.com")
    
    if not token:
        raise MissingTokenException()
    try:
        data = jwt.decode(token, get_google_certs())
        current_user = User.get(data["email"])
        return current_user
    except Exception as e:
        if type(e) == InvalidValue and str(e).startswith("Token expired"):
            raise TokenExpiredException(e)
        else:
            raise TokenDecodingException(e)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            token = None
            if "Authorization" in request.headers:
                token = request.headers["Authorization"]
            current_user = get_user_from_jwt_token(token)
            if current_user is None:
                return {
                "message": "Invalid Authentication token!",
                "data": None,
                "error": "Unauthorized"
            }, 401
        except MissingTokenException as ex:
            return {
                "message": "Authentication Token is missing!",
                "data": None,
                "error": "Unauthorized"
            }, 401
        except TokenExpiredException as ex:
            return {
                "message": "Authentication Token is expired!",
                "data": None,
                "error": "Unauthorized"
            }, 401
        except TokenDecodingException as ex:
            return {
                "message": "Something went wrong",
                "data": None,
                "error": str(ex)
            }, 500

        return f(*args, **dict(kwargs, user=current_user))

    return decorated