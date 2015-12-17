from flask import render_template, g, abort

from . import app
from .lib import current_page
from .models import Quote, AREA_ORDER_MAP, DEFAULT_ORDER, QSTATUS


@app.before_request
def before_request():
    g.current_page = current_page()
    # TODO  - AUTHENTICATION
    from mock import MagicMock
    g.user = MagicMock()


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


@app.route('/login')
def login():
    raise NotImplementedError()


@app.route('/logout')
def logout():
    raise NotImplementedError()


@app.route('/reset_password')
def reset_password():
    raise NotImplementedError()
