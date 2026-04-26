from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, Email, Optional


class ProfileForm(FlaskForm):
    name = StringField('Имя пользователя:', validators=[
        DataRequired('Введите своё имя'),
        Length(min=2, max=50)])
    email = StringField('Email:', validators=[
        DataRequired('Введите email'),
        Email('Некорректный email')])
    about = TextAreaField('О себе:')
    submit = SubmitField('Сохранить изменения')


class PasswordChangeForm(FlaskForm):
    old_password = PasswordField('Текущий пароль:', validators=[DataRequired()])
    new_password = PasswordField('Новый пароль:', validators=[
        DataRequired(),
        Length(min=3, message='Пароль слишком короткий')])
    new_password_again = PasswordField('Повторите новый пароль:', validators=[DataRequired()])
    submit_password = SubmitField('Изменить пароль')
