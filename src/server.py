from flask import Flask, redirect, url_for, render_template, request, session, flash
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
import MySQLdb.cursors
import re
import os
# import magic
import urllib.request
from datetime import datetime

app = Flask(__name__)

app.secret_key = 'your secret key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flask'

mysql = MySQL(app)

basedir = os.path.abspath(os.path.dirname(__file__))
directory = os.path.join(basedir, 'static\\uploads')
if not os.path.exists(directory):
    os.makedirs(directory)

UPLOAD_FOLDER = 'static\\uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/admin')
def admin():
    return redirect(url_for("mainmenu"))


@app.route('/login', methods=['POST', 'GET'])
def login():
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = % s AND password = % s', (email, password))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['name'] = account['name']
            msg = 'Logged in successfully !'
            return render_template('mainmenu.html', msg=msg)
        else:
            msg = 'Incorrect name / password !'
    return render_template('login.html', msg=msg)


@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        name = request.form['name']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE name = % s', (name))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z]+', name):
            msg = 'Name must contain only characters!'
        elif not name or not password or not email:
            msg = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO users (name, email, password) VALUES (% s, % s, % s)', (name, email, password))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg=msg)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('name', None)
    return redirect(url_for('login'))


@app.route('/missinglist')
def missinglist():
    return render_template("missinglist.html")


@app.route('/mainmenu')
def mainmenu():
    return render_template("mainmenu.html")


@app.route('/map')
def map():
    return render_template("map.html")


@app.route('/rqstform')
def rqstform():
    return render_template("rqstform.html")


@app.route('/sightform')
def sightform():
    return render_template("sightform.html")


@app.route('/upload', methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        mName = request.form['mName']
        mDate = request.form['mDate']
        mAge = request.form['mAge']
        mGender = request.form['mGender']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        now = datetime.now()

        files = request.files.getlist('files[]')
        # print(files)
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(basedir, app.config['UPLOAD_FOLDER'], filename))
                cursor.execute(
                    "INSERT INTO rqstforms (mName, mDate, mAge, mGender, mImages, uploadedDate) VALUES (% s, % s, % s, % s, %s, %s)",
                    (mName, mDate, mAge, mGender, filename, now))
            print(file)
        cursor.close()
        flash('File(s) successfully uploaded')

        mysql.connection.commit()

    return render_template("rqstform.html")


@app.route('/aboutus')
def aboutus():
    return render_template("aboutus.html")


@app.route('/profile')
def profile():
    return render_template("profile.html")


if __name__ == "__main__":
    app.run(debug=True)
