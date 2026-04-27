from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from wtforms import StringField, FileField, FloatField, BooleanField, SubmitField, TextAreaField, IntegerField, \
    DecimalField
from wtforms.validators import DataRequired, NumberRange, Optional, InputRequired


class ProductForm(FlaskForm):
    name = StringField('Название товара:',
                       validators=[DataRequired('Введите название')])
    description = TextAreaField('Описание:')
    price = DecimalField('Цена:',
                       validators=[InputRequired('Введите цену'),
                                   NumberRange(min=1)])
    old_price = DecimalField('Старая цена (для скидки):',
                           validators=[InputRequired('Введите цену'), NumberRange(min=1)])
    category = StringField('Категория:')
    stock = IntegerField('Количество на складе:',
                         validators=[InputRequired('Введите кол-во'),
                                     NumberRange(min=1)])
    is_on_sale = BooleanField('Товар со скидкой')
    image = FileField("Загрузить изображение(конвертируется в 400x400)(jpg/jpeg/png/gif)",
                      validators=[FileRequired(message="Загрузите изображение"),
                                                                    FileAllowed(["jpg", "jpeg", "png", "gif"],
                                        message="Выберите изображение с поддерживаемым форматом(jpg/jpeg/png/gif)")])
    submit = SubmitField('Добавить товар')