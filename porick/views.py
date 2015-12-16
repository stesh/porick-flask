from porick import app, model

@app.route('/')
def root():
    return "There are {} quotes and {} tags".format(model.Quote.query.count(), model.Tag.query.count())

