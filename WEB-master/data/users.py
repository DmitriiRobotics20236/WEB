import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    about = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String, index=True, unique=True, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    user_type = sqlalchemy.Column(sqlalchemy.String, default='buyer')
    balance = sqlalchemy.Column(sqlalchemy.Float, default=10000.0)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    news = orm.relationship("News", back_populates='user')
    cart_items = orm.relationship("CartItem", back_populates='user')
    favorites = orm.relationship("Favorite", back_populates='user')
    orders = orm.relationship("Order", back_populates='user', foreign_keys='Order.user_id')
    products = orm.relationship("Product", back_populates='seller', foreign_keys='Product.seller_id')

    def __repr__(self):
        return f'<User> {self.name} {self.email}'

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
