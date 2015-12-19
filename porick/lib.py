import bcrypt
from datetime import datetime, timedelta
from functools import wraps
import re

from flask import request, g, abort
from sqlalchemy import or_

from models import ReportedQuotes, Quote, QSTATUS, User
from porick import db
from settings import PASSWORD_SALT, USER_REPORT_LIMIT

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


def admin_endpoint(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user or not g.user.is_admin:
            abort(401)
        return f(*args, **kwargs)
    return decorated_function


def authenticated_endpoint(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user:
            abort(401)
        return f(*args, **kwargs)
    return decorated_function


def has_made_too_many_reports():
    # TODO:
    # This filtering / counting should be done by SQLAlchemy.
    #
    # This is a quick hack to get around problems with between() and filter/filter_by,
    # possibly caused by the fact that ReportedQuotes is a Table() obj and not a class
    #
    reports = db.session.query(ReportedQuotes).filter_by(user_id=g.user.id).all()
    limit = USER_REPORT_LIMIT
    limit_time = datetime.utcnow() - timedelta(hours=1)
    found = []
    for idx, report in enumerate(reports):
        if limit_time < report.time:
            found.append(report)
        if idx == limit:
            break
    return len(found) >= limit


def quote_belongs_to_user(quote_id):
    quote = Quote.query.filter(Quote.id == quote_id).first()
    if not quote:
        return {'msg': 'Invalid quote ID.',
                'status': 'error'}
    if (quote.submitted_by == g.user or g.user.level == 1) and quote.status != QSTATUS['deleted']:
        return {'status': 'success', 'quote': quote}
    else:
        return {'msg': 'You do not have permission to delete this quote.',
                'status': 'error'}
