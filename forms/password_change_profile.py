from flask_wtf import FlaskForm
from wtforms import PasswordField
from wtforms.fields.simple import SubmitField
from wtforms.validators import DataRequired, Length


class PasswordChangeForm(FlaskForm):
    old_password = PasswordField('Текущий пароль:', validators=[DataRequired()])
    new_password = PasswordField('Новый пароль:', validators=[
        DataRequired(),
        Length(min=3, message='Пароль слишком короткий')])
    new_password_again = PasswordField('Повторите новый пароль:', validators=[DataRequired()])
    submit = SubmitField('Изменить пароль')