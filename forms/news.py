from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length


class NewsForm(FlaskForm):
    title = StringField('Заголовок:',
                        validators=[
                            DataRequired('Введите заголовок'),
                            Length(min=3, max=50,
                                   message='Заголовок должен быть не менее 3 и не более 50 символов ')])
    content = TextAreaField('Содержание:',
                          validators=[
                              DataRequired('Введите текст новости'),
                              Length(min=3, max=250,
                                     message='Текст новости должен быть не менее 3 и не более 250 символов ')])
    is_private = BooleanField('Личное')
    submit = SubmitField('Применить')