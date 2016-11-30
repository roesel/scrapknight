from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, TextAreaField
from wtforms.validators import DataRequired


class InputForm(FlaskForm):
    #openid = StringField('openid', validators=[DataRequired()])
    #remember_me = BooleanField('remember_me', default=False)
    text = TextAreaField('input', default='')
