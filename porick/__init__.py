from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('porick.settings')
db = SQLAlchemy(app)

from . import api, views, models
