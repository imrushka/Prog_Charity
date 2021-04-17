from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, BooleanField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
class RegisterForm(FlaskForm):
    email = EmailField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    password_again = PasswordField('repeat password', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    country = StringField('Country', validators=[DataRequired()])
    city = StringField('city', validators=[DataRequired()])
    district = StringField('district', validators=[DataRequired()])
    building = StringField('building', validators=[DataRequired()])
    about = TextAreaField("A bit about yourself")
    submit = SubmitField('Log in')
class LoginForm(FlaskForm):
    email = EmailField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    remember_me = BooleanField('remember me')
    submit = SubmitField('Log in')
