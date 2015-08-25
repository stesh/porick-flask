from porick import app
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], convert_unicode=True)
Session = scoped_session(sessionmaker(bind=engine))

Base = declarative_base()
Base.query = Session.query_property()
