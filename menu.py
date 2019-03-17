from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask_wtf import Form
from flask import Flask, flash, redirect, render_template, request, session, abort
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
import sqlite3
from flask_sqlalchemy import SQLAlchemy
from forms import SignupForm
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from werkzeug import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, SubmitField


app = Flask(__name__)
csrf = CSRFProtect(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://localhost/users'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.secret_key = "development-key"

db.init_app(app)


class User(db.Model):
    __tablename__ = 'users'
    uid = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(100))
    lastname = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    pwdhash = db.Column(db.String(54))

    def __init__(self, firstname, lastname, email, password):
        self.firstname = firstname.title()
        self.lastname = lastname.title()
        self.email = email.lower()
        self.set_password(password)

    def set_password(self, password):
        self.pwdhash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pwdhash, password)



class SignupForm(Form):
    first_name = StringField('First name')
    last_name = StringField('Last name')
    password = PasswordField('Password')
    submit = SubmitField('Sign up')

class DB_users:
    def __init__(self):
        conn = sqlite3.connect('users.db', check_same_thread=False)
        self.conn = conn

    def get_connection(self):
        return self.conn

    def __del__(self):
        self.conn.close()


class DB_books:
    def __init__(self):
        conn = sqlite3.connect('books.db', check_same_thread=False)
        self.conn = conn

    def get_connection(self):
        return self.conn

    def __del__(self):
        self.conn.close()


class UsersModel:
    def __init__(self, connection):
        self.connection = connection

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             user_name VARCHAR(50),
                             password_hash VARCHAR(128)
                             )''')
        cursor.close()
        self.connection.commit()

    def insert(self, user_name, password_hash):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO users
                          (user_name, password_hash)
                          VALUES (?,?)''', (user_name, password_hash))
        cursor.close()
        self.connection.commit()

    def get(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (str(user_id),))
        row = cursor.fetchone()
        return row

    def get_all(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        return rows

    def exists(self, user_name, password_hash):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE user_name = ? AND password_hash = ?",
                       (user_name, password_hash))
        row = cursor.fetchone()
        return (True, row[0]) if row else (False,)


class BooksModel:
    def __init__(self, connection):
        self.connection = connection

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS books
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             title VARCHAR(100),
                             image VARCHAR(100),
                             user_id INTEGER
                             )''')
        cursor.close()
        self.connection.commit()

    def insert(self, title, image, user_id):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO books
                          (title, image, user_id)
                          VALUES (?,?,?)''', (title, image, str(user_id)))
        cursor.close()
        self.connection.commit()

    def get(self, books_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM books WHERE id = ?", (str(books_id),))
        row = cursor.fetchone()
        return row

    def get_all(self, books_id=None):
        cursor = self.connection.cursor()
        if books_id:
            cursor.execute("SELECT * FROM books WHERE user_id = ?",
                           (str(books_id),))
        else:
            cursor.execute("SELECT * FROM news")
        rows = cursor.fetchall()
        return rows

    def delete(self, books_id):
        cursor = self.connection.cursor()
        cursor.execute('''DELETE FROM books WHERE id = ?''', (str(books_id),))
        cursor.close()
        self.connection.commit()

class LoginForm:
    username = StringField("Введите логин", validators=[DataRequired()])
    password = TextAreaField('Введите пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')



database_users = DB_users()
usersmodel = UsersModel(database_users.get_connection())

database_books = DB_books()
booksmodel = BooksModel(database_books.get_connection())

app = Flask(__name__)
form = LoginForm()

@app.route('/')
@app.route('/menu', methods=['GET', 'POST'])
def menu():
    if request.method == 'GET':
        return render_template('menu.html')

    elif request.method == 'POST':
        if request.form['login']:
            return redirect('/login')
        elif request.form['signup']:
            return redirect('/signup')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == 'password' and request.form['username'] == 'admin':
            session['logged_in'] = True
        user_name = form.username.data
        password = form.password.data
        user_model = UsersModel(DB_users.get_connection())
        exists = user_model.exists(user_name, password)
        if (exists[0]):
            session['username'] = user_name
            session['user_id'] = exists[1]
    return render_template('login.html')


    if user_model.exists(request.form['email'], request.form['pswd']):
        username = user_model.get_username(request.form['email'])
        session['username'] = username
    return redirect('/login')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm(request.form)
    if request.method == 'POST':
        return "Success!"
    elif request.method == 'GET':
        return render_template("signup.html", form=form)


@app.route('/account', methods=['GET', 'POST'])
def account():
    if request.method == 'GET':
        return render_template('account.html')

    elif request.method == 'POST':
        if request.form['allbooks']:
            return redirect('/allbooks')
        elif request.form['mybooks']:
            return redirect('/mybooks')


@app.route('/allbooks', methods=['GET', 'POST'])
def allbooks():
    if request.method == 'GET':
        return render_template('allbooks.html')

    # elif request.method == 'POST':
        # back button


@app.route('/mybooks', methods=['GET', 'POST'])
def mybooks():
    if request.method == 'GET':
        return render_template('mybooks.html')

    # elif request.method == 'POST':
        # back button


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'GET':
        return render_template('add_book.html')


if __name__ == '__main__':
    app.debug = True
    app.run(port=8080, host='127.0.0.1')
