from functools import wraps
from flask import request, abort
from google.auth import jwt
import requests
import os

from ..models.user import User


def get_google_certs():
    headers = {'Accept': 'application/json'}
    r = requests.get(os.environ.get("GOOGLE_OAUTH_CERTS"), headers=headers)
    certs = r.json()
    return certs

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            token = request.headers["Authorization"]
        if not token:
            return {
                "message": "Authentication Token is missing!",
                "data": None,
                "error": "Unauthorized"
            }, 401
        try:
            data = jwt.decode(token, get_google_certs())
            current_user = User.get(data["email"])
            if current_user is None:
                return {
                "message": "Invalid Authentication token!",
                "data": None,
                "error": "Unauthorized"
            }, 401
            #if not current_user["active"]:
            #    abort(403)
        except Exception as e:
            return {
                "message": "Something went wrong",
                "data": None,
                "error": str(e)
            }, 500

        return f(*args, **kwargs)

    return decorated