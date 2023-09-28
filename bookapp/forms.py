from flask_wtf import FlaskForm
from flask_wtf.file import FileField,FileRequired,FileAllowed
from wtforms import StringField,SubmitField,TextAreaField,PasswordField,SelectField,IntegerField
from wtforms.validators import Email,DataRequired,EqualTo,Length

class RegForm(FlaskForm):
    fullname = StringField("Fullname",validators=[DataRequired(message="FirstName is too short")])
    usermail = StringField("Email",validators=[Email(message="Invalid Email"), DataRequired(message="Email must be supplied")])
    pwd = PasswordField("Enter Password",validators=[DataRequired()])
    cpwd = PasswordField("Confirm Password",validators=[EqualTo('pwd',message="The two passwords must match")])
    btnsubmit = SubmitField("Register!")
    

class DpForm(FlaskForm):
    dp = FileField( "Uploas a Profile Picture", validators=[FileRequired(),FileAllowed(['jpg','png','jpeg'])])
    btnupload = SubmitField("Upload Picture")


class ProfileForm(FlaskForm):
    fullname = StringField("Fullname",validators=[DataRequired(message="FirstName is a must")])
    btnupload = SubmitField("Submit")


class ContactForm(FlaskForm):
    email = StringField("Fullname",validators=[DataRequired(message="FirstName is a must")])
    btnsubmit = SubmitField("Submit")


class DonationForm(FlaskForm):
    fullname = StringField("Fullname",validators=[DataRequired(message="FirstName is too short")])
    email = StringField("Email",validators=[Email(message="Invalid Email"), DataRequired(message="Email must be supplied")])
    amount = StringField("Amount",validators=[ DataRequired(message="amount must be supplied")])
    btnsubmit = SubmitField("Continue!")