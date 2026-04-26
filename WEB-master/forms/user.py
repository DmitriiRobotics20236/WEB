from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email, Length
from wtforms import StringField, PasswordField, SubmitField, EmailField, TextAreaField, SelectField


class RegisterForm(FlaskForm):
    email = EmailField('Почта:', validators=[
        DataRequired('Введите корректный E-mail'),
        Email('E-mail некорректен')])
    password = PasswordField('Пароль:', validators=[
        DataRequired('Пароль обязателен'),
        Length(min=3, message='Пароль слишком короткий')])
    password_again = PasswordField('Повторите пароль:', validators=[
        DataRequired('Повторите пароль'),
        Length(min=3, message='Пароль слишком короткий')])
    name = StringField('Имя пользователя:', validators=[DataRequired('Введите своё имя')])
    user_type = SelectField('Тип аккаунта:', choices=[
        ('buyer', '🛒 Покупатель'),
        ('seller', '🏪 Продавец')
    ])
    about = TextAreaField('Немного о себе:')
    submit = SubmitField('Зарегистрироваться')
