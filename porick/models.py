import datetime
import uuid

from sqlalchemy import (
    Column, Index, String, Text, DateTime, Integer, ForeignKey, Table, func)
from sqlalchemy.orm import relationship

from porick import app, db


QSTATUS = {'unapproved': 0,
           'approved': 1,
           'disapproved': 2,
           'reported': 3,
           'deleted': 4}


def now():
    return datetime.datetime.utcnow()


class Tag(db.Model):
    __tablename__  = 'tags'
    __table_args__ = {'sqlite_autoincrement': True}
    id = Column(Integer, nullable=False, primary_key=True)
    tag = Column(String(255), nullable=False, primary_key=True)


QuoteToTag = Table('quote_to_tag', db.Model.metadata,
    Column('quote_id', Integer, ForeignKey('quotes.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

Favourites = Table('favourites', db.Model.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('quote_id', Integer, ForeignKey('quotes.id'))
)

ReportedQuotes = Table('reported_quotes', db.Model.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('quote_id', Integer, ForeignKey('quotes.id')),
    Column('time', DateTime, nullable=False, default=now)
)

DeletedQuotes = Table('deleted_quotes', db.Model.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('quote_id', Integer, ForeignKey('quotes.id')),
    Column('time', DateTime, nullable=False, default=now)
)


class User(db.Model):
    __tablename__  = 'users'
    __table_args__ = {'sqlite_autoincrement': True}
    id = Column(Integer, nullable=False, primary_key=True)
    username = Column(String(32), nullable=False, unique=True)
    password = Column(String(60), nullable=False)
    level = Column(Integer, nullable=False, default=0)
    email = Column(String(64), nullable=False)
    favourites = relationship("Quote", secondary=Favourites)
    reported_quotes = relationship("Quote", secondary=ReportedQuotes)
    deleted_quotes = relationship("Quote", secondary=DeletedQuotes)

    @property
    def is_admin(self):
        return self.level == 1


QuoteToUser = Table('quote_to_user', db.Model.metadata,
    Column('quote_id', Integer, ForeignKey('quotes.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)


class VoteToUser(db.Model):
    __tablename__  = 'vote_to_user'
    quote_id = Column(Integer, ForeignKey('quotes.id'), primary_key=True)
    user_id  = Column(Integer, ForeignKey('users.id'), primary_key=True)
    direction = Column(String(4), nullable=False)
    user = relationship("User")


class PasswordReset(db.Model):
    __tablename__  = 'password_resets'
    user_id  = Column(Integer, ForeignKey('users.id'), primary_key=True)
    key = Column(String(36), nullable=False, default=uuid.uuid4)
    created = Column(DateTime, nullable=False, default=now)
    user = relationship("User")

    @property
    def is_valid(self):
        expiry = datetime.timedelta(hours=app.config['PASSWORD_RESET_REQUEST_EXPIRY'])
        return now() < self.created + expiry


class Quote(db.Model):
    __tablename__  = 'quotes'
    __table_args__ = {'sqlite_autoincrement': True}
    id           = Column(Integer, nullable=False, primary_key=True)
    body         = Column(Text, nullable=False)
    notes        = Column(Text, nullable=True)
    rating       = Column(Integer, nullable=False, default=0)
    votes        = Column(Integer, nullable=False, default=0)
    submitted    = Column(DateTime, nullable=False, default=now)
    status       = Column(Integer, nullable=False, default=0)
    score        = Column(Integer, nullable=False, default=1)
    tags         = relationship("Tag", secondary=QuoteToTag)
    submitted_by = relationship("User", secondary=QuoteToUser, uselist=False)
    voters       = relationship("VoteToUser")

    @property
    def upvotes(self):
        return len([v for v in self.voters if v.direction == 'up'])

    @property
    def downvotes(self):
        return len([v for v in self.voters if v.direction == 'down'])


AREA_ORDER_MAP = {
    'best': [Quote.rating.desc()],
    'worst': [Quote.rating],
    'random': [func.rand()],
    'controversial': [Quote.votes, Quote.rating/Quote.votes]
}
DEFAULT_ORDER = [Quote.submitted.desc()]
