from flask_wtf import FlaskForm
from wtforms.fields.simple import SubmitField, HiddenField


class CatalogDelProdForm(FlaskForm):
    product_id = HiddenField()
    submit = SubmitField("Удалить товар")