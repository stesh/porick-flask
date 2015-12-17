import bcrypt
import re

from flask import request
from sqlalchemy import or_

from models import User
from porick import db
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
    elif bcrypt.hashpw(password.encode('utf-8'), PASSWORD_SALT) == user.password:
        return user
    else:
        return False


def validate_signup(username, password, password_confirm, email):
    valid_password = validate_password(password, password_confirm)
    if not valid_password['status']:
        return valid_password

    if not (username and password and password_confirm and email):
        return {'status': False,
                'msg': 'Please fill in all the required fields.'}

    email_regex = re.compile('''[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%'''
                             '''&'*+/=?^_`{|}~-]+)*@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*'''
                             '''[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?''')
    if not email_regex.match(email):
        return {'status': False,
                'msg': 'Please enter a valid email address.'}

    username_regex = re.compile('''^[a-zA-Z0-9_]*$''')
    if not username_regex.match(username):
        return {'status': False,
                'msg': 'Your username may consist only of'
                       ' alphanumeric characters and underscores.'}

    return {'status': True}


def validate_password(password, password_confirm):
    if not len(password) >= 8:
        return {'status': False,
                'msg': 'Your password must be at least 8 characters long.'}

    if not password == password_confirm:
        return {'status': False,
                'msg': 'Your password did not match in both fields.'}
    return {'status': True}


def create_user(username, password, email):
    conflicts = User.query.filter(or_(User.email == email,
                                      User.username == username)).first()
    if conflicts:
        if conflicts.email == email:
            raise NameError('Sorry! That email already exists in the system.')
        elif conflicts.username == username:
            raise NameError('Sorry! That username is already taken.')

    hashed_pass = bcrypt.hashpw(password.encode('utf-8'), PASSWORD_SALT)
    new_user = User()
    new_user.username = username
    new_user.password = hashed_pass
    new_user.email = email

    db.session.add(new_user)
    db.session.commit()
    return True
