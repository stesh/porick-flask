from flask import render_template, g

from porick import app


@app.route('/')
def landing_page():
    return render_template('/index.html')


@app.route('/browse')
@app.route('/browse/<int:quote_id>')
@app.route('/browse/<area>')
@app.route('/browse/<area>/page/<page>')
def browse(area=None, page=None):
    raise NotImplementedError()


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
