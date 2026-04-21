from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired
from wtforms import StringField, FileField, FloatField, BooleanField, SubmitField, TextAreaField, IntegerField, \
    DecimalField
from wtforms.validators import DataRequired, NumberRange, Optional


class ProductForm(FlaskForm):
    name = StringField('Название товара:',
                       validators=[DataRequired('Введите название')])
    description = TextAreaField('Описание:')
    price = DecimalField('Цена:',
                       validators=[DataRequired('Введите цену'),
                                   NumberRange(min=0)])
    old_price = DecimalField('Старая цена (для скидки):',
                           validators=[Optional()])
    category = StringField('Категория:')
    stock = IntegerField('Количество на складе:',
                         validators=[DataRequired(),
                                     NumberRange(min=0)])
    is_on_sale = BooleanField('Товар со скидкой')
    image = FileField("Загрузить изображение(400x400)", validators=[FileRequired(message="Загрузите изображение")])
    submit = SubmitField('Добавить товар')