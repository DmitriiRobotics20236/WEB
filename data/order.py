import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Order(SqlAlchemyBase):
    __tablename__ = 'orders'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id', ondelete="CASCADE"))
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    delivery_cost = sqlalchemy.Column(sqlalchemy.DECIMAL, nullable=False)
    user = orm.relationship('User', back_populates='orders', foreign_keys=[user_id])
    items = orm.relationship('OrderItem', back_populates='order', cascade="all, delete")

    @property
    def total_amount(self):
        summ = 0
        for el in self.items:
            summ += el.price
        return summ

class OrderItem(SqlAlchemyBase):
    __tablename__ = 'order_items'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    order_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('orders.id', ondelete="CASCADE"))
    product_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('products.id', ondelete="CASCADE"))
    quantity = sqlalchemy.Column(sqlalchemy.Integer, default=1)
    price = sqlalchemy.Column(sqlalchemy.DECIMAL, nullable=False)
    order = orm.relationship('Order', back_populates='items')
    product = orm.relationship('Product')
