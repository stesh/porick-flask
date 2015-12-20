import datetime
import hashlib
import math

from collections import defaultdict

from flask import (
    abort, render_template, flash, g, request, redirect, make_response, url_for)

from . import app
from .lib import (current_page, authenticate, authenticated_endpoint,
                  validate_signup, create_user)
from .models import (
    AREA_ORDER_MAP,
    db,
    DEFAULT_ORDER,
    QSTATUS,
    Quote,
    QuoteToTag,
    Tag,
    User,
)

MEMBER_AREAS = ['favourites', 'disapproved']
ADMIN_AREAS = ['unapproved', 'reported', 'deleted']

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
    if area in MEMBER_AREAS and not g.user:
        flash('You must be logged in to view that page.', 'info')
        return redirect(url_for('login', redirect_url=request.path))
    if area in ADMIN_AREAS and not g.user.is_admin:
        abort(404)
    g.page = area or 'browse'
    quotes = Quote.query
    if quote_id is not None:
        quotes = quotes.filter(Quote.id == quote_id)
        if not quotes or quotes[0].status != QSTATUS['approved']:
            abort(404)
    else:
        try:
            quotes = quotes.filter(Quote.status == QSTATUS[area])
        except KeyError:
            # This is the default case, for areas like "best" and "worst", that
            # don't have a specific filter.
            quotes = quotes.filter(Quote.status == QSTATUS['approved'])
        quotes = quotes.order_by(AREA_ORDER_MAP.get(area, DEFAULT_ORDER))
    pagination = quotes.paginate(
        g.current_page, app.config['QUOTES_PER_PAGE'], error_out=True)
    if quote_id or area == 'random':
        pagination.items = pagination.items[:1]
    return render_template('/browse.html', pagination=pagination)

def _generate_tagcloud(tags):
    counts = defaultdict(int)
    quote_to_tag = db.session.query(QuoteToTag).all()
    tags = {t.id: t.tag for t in Tag.query.all()}

    for quote_id, tag_id in quote_to_tag:
        counts[tag_id] += 1

    cloud = {}
    for tag_id, count in counts.iteritems():
        tag = tags.get(tag_id)
        if tag:
            cloud[tag] = math.log(count, math.e/2)

    return cloud

@app.route('/browse/tags')
@app.route('/browse/tags/<tag>')
def browse_by_tags(tag=None, page=None):
    if not tag:
        tags = Tag.query.all()
        return render_template('tagcloud.html', tagcloud=_generate_tagcloud(tags))

    else:
        tag = Tag.query.filter(Tag.tag == tag).one()
        q = Quote.query
        q = q.filter(Quote.tags.contains(tag))
        q = q.filter(Quote.status == QSTATUS['approved'])
        q = q.order_by(Quote.submitted.desc())

        pagination = q.paginate(
            g.current_page,
            app.config['QUOTES_PER_PAGE'],
            error_out=True
        )
        return render_template('/browse.html', pagination=pagination)

@app.route('/search', methods=['POST'])
def search():
    term = request.form['term']
    return redirect(url_for('display_search_results', term=term))


@app.route('/search/<term>')
def display_search_results(term=None, page=None):
    quotes = Quote.query.filter(Quote.body.like('%' + term + '%')).filter(
        Quote.status == QSTATUS['approved']).order_by(Quote.submitted.desc())
    pagination = quotes.paginate(
        g.current_page, app.config['QUOTES_PER_PAGE'], error_out=True)
    g.page = 'search: %s' % term
    return render_template('/browse.html', pagination=pagination)


@app.route('/create', methods=['GET', 'POST'])
@authenticated_endpoint
def new_quote():
    if request.method == 'GET':
        g.page = 'new quote'
        return render_template('/create_quote.html')
    else:
        quote_body = request.form.get('quote_body')
        if not quote_body:
            abort(400)
        notes = request.form.get('notes', '')
        tags = filter(None, request.form.get('tags', '').replace(',', ' ').split(' '))

        quote = Quote()
        quote.body = quote_body
        quote.notes = notes

        quote.tags = []
        for tagname in tags:
            tag = Tag.query.filter(Tag.tag == tagname).first()
            if not tag:
                tag = Tag()
                tag.tag = tagname
                db.session.add(tag)
            quote.tags.append(tag)
        quote.submitted_by = g.user
        db.session.add(quote)
        db.session.commit()
        return render_template('/create_quote_success.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    g.page = 'sign up'
    if request.method == 'GET':
        return render_template('/signup.html')
    username = request.form['username']
    password = request.form['password']
    password_confirm = request.form['password_confirm']
    email = request.form['email']

    validity = validate_signup(username, password, password_confirm, email)
    if not validity['status']:
        flash(validity['msg'], 'error')
        return render_template('/signup.html')
    try:
        create_user(username, password, email)
        authenticate(username, password)
        g.user = User.query.filter(User.username == username).first()
        return render_template('/signup_success.mako')
    except NameError, e:
        flash(e.__str__(), 'error')
        return render_template('/signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    g.page = 'log in'
    if request.method == 'GET':
        return render_template('/login.html', redirect_url=request.args.get('redirect_url', ''))
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
    expiry = datetime.datetime.now() + datetime.timedelta(
        days=app.config['COOKIE_LIFETIME'])
    response.set_cookie('auth', auth, expires=expiry)
    response.set_cookie('username', user.username, expires=expiry)
    response.set_cookie('level', str(user.level), expires=expiry)
    return response


@app.route('/logout')
def logout():
    g.page = 'logout'
    response = make_response(redirect(url_for('landing_page')))
    response.set_cookie('auth', '', expires=0)
    response.set_cookie('username', '', expires=0)
    response.set_cookie('level', '', expires=0)
    g.user = None
    flash('Logged out successfully!', 'info')
    return response


@app.route('/reset_password')
def reset_password():
    raise NotImplementedError()
