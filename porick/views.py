from flask import render_template, g, abort

from porick import app
from porick.model import db, Quote, AREA_ORDER_MAP, DEFAULT_ORDER, QSTATUS


@app.route('/')
def landing_page():
    return render_template('/index.html')


@app.route('/browse')
@app.route('/browse/<int:quote_id>')
@app.route('/browse/<area>')
@app.route('/browse/<area>/page/<page>')
def browse(area=None, quote_id=None, page=None):
    g.page = area or 'browse'
    quotes = db.query(Quote)
    if quote_id is not None:
        quote = quotes.filter(Quote.id == quote_id).first()
        if not quote or quote.status != QSTATUS['approved']:
            abort(404)
        quotes = [quote]
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
        else:
            quotes = quotes.all()
    return render_template('/browse.html', quotes=quotes)


@app.route('/browse/tags')
@app.route('/browse/tags/<tag>')
@app.route('/browse/tags/<tag>/page/<page>')
def browse_by_tags(tag=None, page=None):
    raise NotImplementedError()


@app.route('/search')
@app.route('/search/<term>')
@app.route('/search/<term>/page/<page>')
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
