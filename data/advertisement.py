import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase


class Advertisement(SqlAlchemyBase):
    __tablename__ = 'advertisements'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    text = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    link = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    badge = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    is_active = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
