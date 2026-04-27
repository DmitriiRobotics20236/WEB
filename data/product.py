import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Product(SqlAlchemyBase):
    __tablename__ = 'products'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    price = sqlalchemy.Column(sqlalchemy.DECIMAL, nullable=False)
    old_price = sqlalchemy.Column(sqlalchemy.DECIMAL, nullable=True)
    category = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    stock = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    is_on_sale = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id", ondelete="CASCADE"))
    user = orm.relationship("User")
    image = orm.relationship("ProductImages", cascade="all, delete")
    favorites = orm.relationship("Favorite", back_populates="product")


    def __repr__(self):
        return f'<Product> {self.name} - {self.price}₽'


class ProductImages(SqlAlchemyBase):
    __tablename__ = "ProductImages"
    product_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("products.id", ondelete="CASCADE"),
                           primary_key=True)
    image = sqlalchemy.Column(sqlalchemy.LargeBinary, nullable=False)