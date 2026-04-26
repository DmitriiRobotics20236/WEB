import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Order(SqlAlchemyBase):
    __tablename__ = 'orders'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    status = sqlalchemy.Column(sqlalchemy.String, default='pending')
    total_amount = sqlalchemy.Column(sqlalchemy.Float, default=0.0)
    delivery_cost = sqlalchemy.Column(sqlalchemy.Float, default=0.0)

    user = orm.relationship('User', back_populates='orders', foreign_keys=[user_id])
    items = orm.relationship('OrderItem', back_populates='order')


class OrderItem(SqlAlchemyBase):
    __tablename__ = 'order_items'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    order_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('orders.id'))
    product_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('products.id'))
    quantity = sqlalchemy.Column(sqlalchemy.Integer, default=1)
    price = sqlalchemy.Column(sqlalchemy.Float, nullable=False)

    order = orm.relationship('Order', back_populates='items')
    product = orm.relationship('Product')
