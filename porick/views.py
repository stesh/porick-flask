import hashlib

from flask import (
    abort, render_template, flash, g, request, redirect, make_response, url_for)

from . import app
from .lib import current_page, authenticate
from .models import Quote, User, AREA_ORDER_MAP, DEFAULT_ORDER, QSTATUS


@app.before_request
def before_request():
    g.current_page = current_page()
    g.user = None
    auth = request.cookies.get('auth')
    username = request.cookies.get('username')
    level = request.cookies.get('level')
    if auth:
        value = '{}:{}:{}'.format(app.config['COOKIE_SECRET'], username, level)
        if auth == hashlib.md5(value).hexdigest():
            user = User.query.filter(User.username == username).first()
            if user:
                g.user = user


@app.route('/')
def landing_page():
    return render_template('/index.html')


@app.route('/browse')
@app.route('/browse/<int:quote_id>')
@app.route('/browse/<area>')
def browse(area=None, quote_id=None):
    g.page = area or 'browse'
    if g.page in ['favourites', 'disapproved'] and not g.user:
        abort(404)
    if g.page in ['unapproved', 'reported', 'deleted'] and not g.user.is_admin():
        abort(404)
    quotes = Quote.query
    if quote_id is not None:
        quotes = quotes.filter(Quote.id == quote_id).first()
        if not quotes or quotes.status != QSTATUS['approved']:
            abort(404)
    else:
        try:
            quotes = quotes.filter(Quote.status == QSTATUS[area])
        except KeyError:
            # This is the default case, for areas like "best" and "worst", that
            # don't have a specific filter.
            quotes = quotes.filter(Quote.status == QSTATUS['approved'])
        quotes = quotes.order_by(AREA_ORDER_MAP.get(area, DEFAULT_ORDER))
        if area == 'random':
            quotes = quotes.first()
    pagination = quotes.paginate(
        g.current_page, app.config['QUOTES_PER_PAGE'], error_out=True)
    return render_template('/browse.html', pagination=pagination)


@app.route('/browse/tags')
@app.route('/browse/tags/<tag>')
def browse_by_tags(tag=None, page=None):
    raise NotImplementedError()


@app.route('/search')
@app.route('/search/<term>')
def search(term=None, page=None):
    raise NotImplementedError()

@app.route('/create')
def new_quote():
    raise NotImplementedError()


@app.route('/signup')
def create_account():
    raise NotImplementedError()


@app.route('/login', methods=['GET', 'POST'])
def login():
    g.page = 'log in'
    if request.method == 'GET':
        return render_template('/login.html')
    user = authenticate(request.form['username'], request.form['password'])
    if not user:
        flash('Incorrect username / password', 'error')
        return render_template('/login.html')
    cleartext_value = '{}:{}:{}'.format(
        app.config['COOKIE_SECRET'], user.username, user.level)
    auth = hashlib.md5(cleartext_value).hexdigest()
    if request.args.get('redirect_url') not in [None, '/signup', '/logout', '/reset_password']:
        response = make_response(redirect(request.args.get('redirect_url')))
    else:
        response = make_response(redirect(url_for('browse')))
    response.set_cookie('auth', auth, max_age=2592000)
    response.set_cookie('username', user.username, max_age=2592000)
    response.set_cookie('level', str(user.level), max_age=2592000)
    return response


@app.route('/logout')
def logout():
    raise NotImplementedError()


@app.route('/reset_password')
def reset_password():
    raise NotImplementedError()
