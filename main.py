import os

from flask import Flask
from flask import flash
from flask import render_template
from flask import request
from flask import redirect
import sqlite3
from flask import send_from_directory
from flask import session
from flask import url_for
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
from wtforms import StringField, SubmitField, PasswordField, BooleanField, FileField
from wtforms.validators import DataRequired


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
            cursor.execute("SELECT * FROM books")
        rows = cursor.fetchall()
        return rows

    def delete(self, books_id):
        cursor = self.connection.cursor()
        cursor.execute('''DELETE FROM books WHERE id = ?''', (str(books_id),))
        cursor.close()
        self.connection.commit()


class AddBookForm(FlaskForm):
    title = StringField('Название книги', validators=[DataRequired()])
    image = StringField('Обложка книги', validators=[DataRequired()])
    submit = SubmitField('Добавить')


class File(FlaskForm):
    title = StringField('Title of the book', validators=[DataRequired()])
    file = FileField()


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class SignUpForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    admit = BooleanField('Условия')
    submit = SubmitField('Зарегистрироваться')


database_users = DB_users()
usersmodel = UsersModel(database_users.get_connection())

database_books = DB_books()
booksmodel = BooksModel(database_books.get_connection())

booksmodel.init_table()
usersmodel.init_table()

usersmodel.insert('username', 'password')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

UPLOAD_FOLDER = '/static/books'
ALLOWED_EXTENSIONS = set(['pdf'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
    form = LoginForm()
    if form.validate_on_submit():
        user_name = form.username.data
        password = form.password.data
        usersmodel = UsersModel(database_users.get_connection())
        exists = usersmodel.exists(user_name, password)
        if (exists[0]):
            session['username'] = user_name
            session['user_id'] = exists[1]
        return redirect('/account')
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
def logout():
    session.pop('username', 0)
    session.pop('user_id', 0)
    return redirect('/menu')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        user_name = form.username.data
        password = form.password.data
        usersmodel = UsersModel(database_users.get_connection())
        usersmodel.insert(user_name, password)
        return redirect('/login')

    return render_template('signup.html', form=form)


@app.route('/contacts', methods=['GET', 'POST'])
def contacts():
    return render_template('contacts.html')


@app.route('/account', methods=['GET', 'POST'])
def account():
    if request.method == 'GET':
        return render_template('account.html', username=session['username'])

    elif request.method == 'POST':
        if request.form['allbooks']:
            return redirect('/allbooks')
        elif request.form['mybooks']:
            return redirect('/mybooks')


@app.route('/allbooks', methods=['GET', 'POST'])
def allbooks():
    if 'username' not in session:
        return redirect('/login')
    books = BooksModel(database_books.get_connection()).get_all()

    return render_template('allbooks.html', username=session['username'], books=books)


@app.route('/mybooks', methods=['GET', 'POST'])
def mybooks():
    if 'username' not in session:
        return redirect('/login')
    books = BooksModel(database_books.get_connection()).get_all(session['user_id'])

    return render_template('mybooks.html', username=session['username'], books=books)


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'username' not in session:
        return redirect('/login')
    form = AddBookForm()
    if form.validate_on_submit():
        title = form.title.data
        image = form.image.data
        booksmodel = BooksModel(database_books.get_connection())
        booksmodel.insert(title, image, session['user_id'])
        return redirect('/mybooks')

    return render_template('add_book.html', form=form, username=session['username'])


@app.route('/delete_book/<int:books_id>', methods=['GET'])
def delete_books(books_id):
    if 'username' not in session:
        return redirect('/login')
    nm = BooksModel(database_books.get_connection())
    nm.delete(books_id)
    return redirect("/mybooks")


@app.route('/addbook', methods=['GET', 'POST'])
def addbook():
    form = File()
    if form.validate_on_submit():
        title = form.title.data
        file = form.file.data
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))

        booksmodel = BooksModel(database_books.get_connection())
        booksmodel.insert(title, (os.path.join(app.config['UPLOAD_FOLDER'], file)), session['user_id'])
        return redirect('/mybooks')

    return render_template('addbook.html', form=form)


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
