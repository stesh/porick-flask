from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('porick.settings')
db = SQLAlchemy(app)

from porick import api
from porick import views
from porick import models
