from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField


class AddMoneyForm(FlaskForm):
    email = StringField("Email пользователя")
    money = IntegerField("Кол-во денег для прибавления пользователю")
    submit = SubmitField("Подтвердить")