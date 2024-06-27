from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, DateField, SelectField
from wtforms.validators import DataRequired


# Create a form to register new users
class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")


# Create a form to login existing users
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")


# Create a form to add todos
class CreateTodoForm(FlaskForm):
    category = SelectField("Category", choices=[('1', 'Work'), ('2', 'Personal'), ('3', 'Other')], coerce=int,
                           validators=[DataRequired()])
    task = StringField("Task", validators=[DataRequired()])
    due_date = DateField("Due date", format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField("Submit")
