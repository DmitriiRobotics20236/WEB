from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email, Length
from wtforms import (StringField, PasswordField, BooleanField,
                     SubmitField, EmailField, TextAreaField)


class RegisterForm(FlaskForm):
    email = EmailField('Почта:', validators=[
        DataRequired('Введите корректный E-mail'),
        Email('E-mail некорректен')])
    password = PasswordField(
        'Пароль:',
        validators=[DataRequired('Пароль обязателен'),
                    Length(min=3,
                           message='Пароль слишком короткий')])
    password_again = PasswordField(
        'Повторите пароль:',
        validators=[DataRequired('Повторите пароль'),
                    Length(min=3,
                           message='Пароль слишком короткий')])
    name = StringField('Имя пользователя:',
                       validators=[DataRequired('Введите своё имя')])
    about = TextAreaField('Немного о себе:')
    submit = SubmitField('Регистрация')