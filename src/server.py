from flask import Flask, redirect, url_for, render_template, request, session, flash
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
import MySQLdb.cursors
import re
import os
from datetime import datetime

app = Flask(__name__)

app.secret_key = 'your secret key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flask'

mysql = MySQL(app)

# local filepath
basedir = os.path.abspath(os.path.dirname(__file__))
directory = os.path.join(basedir, 'static\\uploads')
if not os.path.exists(directory):
    os.makedirs(directory)

UPLOAD_FOLDER = 'static\\uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# admin side

@app.route('/admin', methods=['POST', 'GET'])
def admin():
    msg = ''
    if request.method == 'POST' and 'adminEmail' in request.form and 'adminPassword' in request.form:
        adminEmail = request.form['adminEmail']
        adminPassword = request.form['adminPassword']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM admins WHERE adminEmail = % s AND adminPassword = % s',
                       (adminEmail, adminPassword))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['adminName'] = account['adminName']
            msg = 'Logged in successfully !'

            query = "SELECT rqstforms.*, images.mImages FROM rqstforms LEFT JOIN images ON rqstforms.rqstId = images.rqstId WHERE status ='1' AND numOfImg = '0'"
            cursor.execute(query)
            row = cursor.fetchall()
            return render_template('adminmenu.html', msg=msg, row=row)
        else:
            msg = 'Incorrect name / password !'
    return render_template('admin.html', msg=msg)


@app.route('/adminmenu', methods=['POST', 'GET'])
def adminmenu():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    query = "SELECT rqstforms.*, images.mImages FROM rqstforms LEFT JOIN images ON rqstforms.rqstId = images.rqstId WHERE status ='1' AND numOfImg = '0'"
    cursor.execute(query)
    row = cursor.fetchall()
    return render_template("adminmenu.html", row=row)


@app.route('/approvedlist', methods=['POST', 'GET'])
def approvedlist():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    query = "SELECT rqstforms.*, images.mImages FROM rqstforms LEFT JOIN images ON rqstforms.rqstId = images.rqstId WHERE status ='2' AND numOfImg = '0'"
    cursor.execute(query)
    row = cursor.fetchall()
    return render_template("approvedlist.html", row=row)


@app.route('/adminmap')
def adminmap():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    query = "SELECT * FROM rqstforms WHERE status ='2'"
    cursor.execute(query)
    row = cursor.fetchall()
    return render_template("adminmap.html", row=row)


# status: 0 = Rejected, 1 = Pending Approval, 2 = Approved, 3 = Found, 4 = Missing

@app.route('/approve', methods=['POST', 'GET'])
def approve():
    if request.method == 'POST':
        newID = request.form['test']
        if request.form.get('approve') == 'approve':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            query = "UPDATE rqstforms SET status = '2' WHERE rqstId = %s"
            cursor.execute(query, [newID])
            mysql.connection.commit()

        elif request.form.get('delete') == 'delete':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            query = "UPDATE rqstforms SET status = '0' WHERE rqstId = %s"
            cursor.execute(query, [newID])
            mysql.connection.commit()

    return redirect(url_for('adminmenu'))


# client side

@app.route('/', methods=['POST', 'GET'])
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
            session['email'] = account['email']
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
        cursor.execute('SELECT * FROM users WHERE name = % s', [name])
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


@app.route('/missinglist', methods=['GET', 'POST'])
def missinglist():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # query = "SELECT rqstforms.*, images.mImages FROM rqstforms LEFT JOIN images ON rqstforms.rqstId = images.rqstId WHERE status ='2' AND numOfImg = '0'"
    # cursor.execute(query)

    query = "SELECT rqstforms.*, images.mImages, sightforms.sDate, sightforms.sAddress FROM rqstforms INNER JOIN images ON images.rqstId = rqstforms.rqstId " \
            "LEFT JOIN sightforms ON sightforms.rqstId = rqstforms.rqstId WHERE status ='2' AND numOfImg = '0'"
    cursor.execute(query)

    row = cursor.fetchall()

    return render_template("missinglist.html", row=row)


@app.route('/mainmenu')
def mainmenu():
    return render_template("mainmenu.html")


@app.route('/map')
def map():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    query = "SELECT rqstforms.*, images.mImages FROM rqstforms LEFT JOIN images ON rqstforms.rqstId = images.rqstId WHERE status ='2' AND numOfImg = '0'"
    cursor.execute(query)
    row = cursor.fetchall()
    return render_template("map.html", row=row)


@app.route('/rqstform')
def rqstform():
    return render_template("rqstform.html")


@app.route('/sightform')
def sightform():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    query = "SELECT * FROM rqstforms WHERE status ='2'"
    cursor.execute(query)
    row = cursor.fetchall()
    return render_template("sightform.html", row=row)


@app.route('/upload', methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        mName = request.form['mName']
        mDate = request.form['mDate']
        mAge = request.form['mAge']
        mGender = request.form['mGender']
        mLong = request.form['lat']
        mLat = request.form['long']
        address = request.form['address']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        now = datetime.now().date()

        files = request.files.getlist('files[]')

        # submit into db for request
        cursor.execute(
            "INSERT INTO rqstforms (mName, mDate, mAge, mGender, mLong, mLat, location, uploadedDate) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (mName, mDate, mAge, mGender, mLong, mLat, address, now))

        # get id from rqstfrom
        userid = cursor.lastrowid

        # print(files)
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(basedir, app.config['UPLOAD_FOLDER'], filename))
                cursor.execute(
                    'INSERT INTO images (mImages, rqstId, numOfImg) VALUES (%s, %s, %s)',
                    (filename, userid, files.index(file)))

        cursor.close()
        flash('File(s) successfully uploaded')

        mysql.connection.commit()

    return render_template("rqstform.html")


@app.route('/sight', methods=['POST', 'GET'])
def sight():
    if request.method == 'POST':
        rqstId = request.form['rqstId']
        sDate = request.form['sDate']
        sTime = request.form['sTime']
        sAddress = request.form['sAddress']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # get id from rqstfrom
        print(rqstId)
        try:
            query = "UPDATE sightforms SET sDate = %s, sTime = %s, sAddress = %s WHERE rqstId = %s"
            cursor.execute(query, (sDate, sTime, sAddress, rqstId))
            cursor.close()

        except:
            cursor.execute(
                "INSERT INTO sightforms (sDate, sTime, sAddress, rqstId) VALUES (%s, %s, %s, %s)",
                (sDate, sTime, sAddress, rqstId))
            cursor.close()
        flash('File(s) successfully uploaded')

        mysql.connection.commit()

    return render_template("sightform.html")


@app.route('/aboutus')
def aboutus():
    return render_template("aboutus.html")


@app.route('/profile')
def profile():
    return render_template("profile.html")


if __name__ == "__main__":
    app.run(debug=True)
