from flask_wtf import FlaskForm
from wtforms import SubmitField
from wtforms.fields.choices import SelectField
from wtforms.fields.numeric import IntegerField, DecimalField
from wtforms.validators import DataRequired, Optional, InputRequired, NumberRange


class CatalogSortForm(FlaskForm):
    price = SelectField("Параметры для сортировки товаров", choices=[(">", "Сначала дорогие"),
                                                                     ("<", "Сначала дешёвые")])
    min_price = DecimalField("Минимальная цена", validators=[InputRequired("Введите число"), NumberRange(min=0)])
    max_price = DecimalField("Максимальная цена", validators=[InputRequired("Введите число"), NumberRange(min=0)])
    submit = SubmitField("Применить")