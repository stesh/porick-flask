import bcrypt

from flask import request

from models import User
from settings import PASSWORD_SALT

def current_page(default=1):
    try:
        return int(request.args.get('page', default))
    except ValueError:
        return default


def authenticate(username, password):
    user = User.query.filter(User.username == username).first()
    if not user:
        return False
    elif bcrypt.hashpw(password, PASSWORD_SALT) == user.password:
        return user
    else:
        return False
