from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email, Length
from wtforms import StringField, PasswordField, BooleanField, SubmitField


class LoginForm(FlaskForm):
    email = StringField('Электронная почта:', validators=[
        DataRequired('Заполните email'),
        Email('Некорректный E-mail')])
    password = PasswordField('Пароль:', validators=[
        DataRequired('Пароль обязателен'),
        Length(min=3, message='Пароль слишком короткий')])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')
