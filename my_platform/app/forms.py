# app/forms.py
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, URL, NumberRange
from app.models import User
from wtforms import TextAreaField, SelectField
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField
# from email_validator import validate_email, EmailNotValidError


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email(message='Invalid email address')])
    password = PasswordField('Password', validators=[DataRequired()])
    password_confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username already taken.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email already in use.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')

class AddContentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    source = StringField('Source URL', validators=[DataRequired(), URL()])
    content_type = SelectField('Content Type', choices=[('video', 'Video'), ('article', 'Article'), ('podcast', 'Podcast'), ('course', 'Online Course')], validators=[DataRequired()])
    difficulty = SelectField('Difficulty', choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')], validators=[DataRequired()])
    submit = SubmitField('Add Content')

class AddContentToPathForm(FlaskForm):
    content = SelectField('Content', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Content to Path')
    
class LearningPreferencesForm(FlaskForm):
    topic_of_study = StringField('Topic of Study', validators=[DataRequired()])
    current_skill_level = IntegerField('Current Skill Level', validators=[DataRequired()])
    target_skill_level = IntegerField('Target Skill Level', validators=[DataRequired()])
    time_frame = IntegerField('Time Frame (in weeks)', validators=[DataRequired()])
    submit = SubmitField('Save Preferences')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    bio = TextAreaField('Bio')
    submit = SubmitField('Update')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('This username is already taken. Please use a different username.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('This email is already taken. Please use a different email address.')

class CreateLearningPathForm(FlaskForm):
    title = StringField('Name', validators=[DataRequired()])
    topic_of_study = StringField('Topic of Study', validators=[DataRequired()])
    current_skill_level = IntegerField('Current Skill Level', validators=[DataRequired(), NumberRange(min=0, max=10)])
    target_skill_level = IntegerField('Target Skill Level', validators=[DataRequired(), NumberRange(min=0, max=10)])
    time_frame = IntegerField('Time Frame (in weeks)', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Create Learning Path')


