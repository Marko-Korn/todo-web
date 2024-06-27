from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from forms import RegisterForm, LoginForm, CreateTodoForm
from sqlalchemy import Integer, String
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.environ["SECRET_KEY"]
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']

ckeditor = CKEditor(app)
Bootstrap5(app)

# Configure DB
db = SQLAlchemy()
db.init_app(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


# CREATE DATABASE
class Base(DeclarativeBase):
    pass


# CONFIGURE TABLES
class Todo(db.Model):
    __tablename__ = "todo_lists"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    # Create reference to the User object. The "posts" refers to the posts property in the User class.
    author = relationship("User", back_populates="lists")
    task: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    due_date: Mapped[str] = mapped_column(String(250), nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("categories.id"))
    category = relationship("Category", back_populates="tasks_list")


def check_due_date_status(due_date_str):
    today = datetime.today().date()
    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()

    if due_date < today:
        return "Past due", "#ff4d5a"
    elif due_date == today:
        return "Due today", "yellow"
    else:
        return "On time", "gray"


# Create a User table for all registered users
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    lists = relationship("Todo", back_populates="author")


class Category(db.Model):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    tasks_list = relationship('Todo', back_populates='category', lazy=True)


def initialize_categories():
    initial_categories = ['Work', 'Personal', 'Other']
    for category_name in initial_categories:
        category = Category.query.filter_by(name=category_name).first()
        if not category:
            category = Category(name=category_name)
            db.session.add(category)
    db.session.commit()


with app.app_context():
    db.create_all()
    initialize_categories()


# Register new users into the User database
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if user email is already present in the database.
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        # This line will authenticate the user with Flask-Login
        login_user(new_user)
        return redirect(url_for("home"))
    return render_template("register.html", form=form, current_user=current_user)


# Login the user
@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))

    return render_template("login.html", form=form, current_user=current_user)


# Logout the user
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


# Home route
@app.route("/", methods=["GET", "POST"])
def home():
    if current_user.is_authenticated:
        categories = Category.query.all()
        tasks_by_category = {}
        for category in categories:
            tasks = Todo.query.filter_by(category_id=category.id, author_id=current_user.id).order_by(Todo.due_date).all()
            tasks_with_status = []
            for task in tasks:
                status, color = check_due_date_status(task.due_date)
                tasks_with_status.append((task, status, color))
            tasks_by_category[category.name] = tasks_with_status

        form = CreateTodoForm()
        if form.validate_on_submit():
            category_id = form.category.data
            new_task = Todo(
                author=current_user,
                task=form.task.data,
                due_date=form.due_date.data,
                category_id=category_id
            )
            db.session.add(new_task)
            db.session.commit()
            return redirect(url_for("home"))
        return render_template("index.html", form=form, current_user=current_user, tasks_by_category=tasks_by_category)
    else:
        return render_template("index.html")


# Delete task
@app.route("/delete/<int:task_id>", methods=["GET", "POST"])
def delete_task(task_id):
    if current_user.is_authenticated:
        task_to_delete = db.get_or_404(Todo, task_id)
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True, port=5001)