from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Email


class ProfileForm(FlaskForm):
    name = StringField('Имя пользователя:',
                       validators=[DataRequired('Введите своё имя'),
                                   Length(min=2, max=50, message="Длина должна быть от 2 до 50 символов")])
    email = StringField('Email:',
                        validators=[DataRequired('Введите email'),
                                    Email('Некорректный email')])
    about = TextAreaField('О себе:')
    submit = SubmitField('Сохранить изменения')