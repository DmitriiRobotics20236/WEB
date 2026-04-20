from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, BooleanField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, NumberRange, Optional

class SubmitBuyForm(FlaskForm):
    submit = SubmitField("Оформить заказ")