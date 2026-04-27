import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    about = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String,
                              index=True, unique=True, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)
    news = orm.relationship("News", back_populates='user', cascade="all, delete")
    cart_items = orm.relationship("CartItem", back_populates='user', cascade="all, delete")
    money = sqlalchemy.Column(sqlalchemy.DECIMAL, nullable=False, default=0)
    products = orm.relationship("Product", back_populates="user", cascade="all, delete")
    favorites = orm.relationship("Favorite", back_populates='user')
    orders = orm.relationship("Order", back_populates='user')
    is_seller = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False)

    def __repr__(self):
        return f'<User> {self.name} {self.email}'

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    # Модель пользователя (имя, email, пароль)