from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class AddBookForm(FlaskForm):
    title = StringField('Название книги', validators=[DataRequired()])
    content = StringField('Обложка книги', validators=[DataRequired()])
    submit = SubmitField('Add')
