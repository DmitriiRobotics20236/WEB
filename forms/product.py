from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, BooleanField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, NumberRange, Optional


class ProductForm(FlaskForm):
    name = StringField('Название товара:',
                       validators=[DataRequired('Введите название')])
    description = TextAreaField('Описание:')
    price = FloatField('Цена:',
                       validators=[DataRequired('Введите цену'),
                                   NumberRange(min=0)])
    old_price = FloatField('Старая цена (для скидки):',
                           validators=[Optional()])
    category = StringField('Категория:')
    stock = IntegerField('Количество на складе:',
                         validators=[DataRequired(),
                                     NumberRange(min=0)])
    is_on_sale = BooleanField('Товар со скидкой')
    submit = SubmitField('Добавить товар')