import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class CartItem(SqlAlchemyBase):
    __tablename__ = 'cart_items'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id", ondelete="CASCADE"))
    product_id = sqlalchemy.Column(sqlalchemy.Integer,
                                   sqlalchemy.ForeignKey("products.id", ondelete="CASCADE"))
    quantity = sqlalchemy.Column(sqlalchemy.Integer, default=1)

    user = orm.relationship('User', back_populates='cart_items')
    product = orm.relationship('Product')

    # Модель корзины (связь user+product)