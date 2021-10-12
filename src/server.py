from flask import Flask, redirect, url_for, render_template, request, session, flash
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
import MySQLdb.cursors
import re
import os
from datetime import datetime
import cv2
import numpy as np
import face_recognition

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
            session['phone'] = account['phone']
            msg = 'Logged in successfully !'
            return render_template('mainmenu.html', msg=msg)
        else:
            msg = 'Incorrect name / password !'
    return render_template('login.html', msg=msg)


@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form and 'phone' in request.form:
        name = request.form['name']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = % s', [email])
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z]+', name):
            msg = 'Name must contain only characters!'
        elif not re.match(r'[0-9]+', phone):
            msg = 'Please enter a valid phone number!'
        elif not name or not password or not email or not phone:
            msg = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO users (name, email, password, phone) VALUES (%s, %s, %s, %s)', (name, email, password, phone))
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
    session.pop('email', None)
    return redirect(url_for('login'))


@app.route('/missinglist', methods=['GET', 'POST'])
def missinglist():
    if "email" in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        query = "SELECT rqstforms.*, images.mImages FROM rqstforms INNER JOIN images ON images.rqstId = rqstforms.rqstId WHERE status ='2' AND numOfImg = '0'"
        cursor.execute(query)
        row = cursor.fetchall()

        return render_template("missinglist.html", row=row)
    else:
        return redirect(url_for('login'))


@app.route('/mainmenu')
def mainmenu():
    if "email" in session:
        return render_template("mainmenu.html")
    else:
        return redirect(url_for('login'))


@app.route('/map')
def map():
    if "email" in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        query = "SELECT rqstforms.*, images.mImages FROM rqstforms LEFT JOIN images ON rqstforms.rqstId = images.rqstId WHERE status ='2' AND numOfImg = '0'"
        cursor.execute(query)
        row = cursor.fetchall()
        return render_template("map.html", row=row)
    else:
        return redirect(url_for('login'))


@app.route('/rqstform')
def rqstform():
    if "email" in session:
        return render_template("rqstform.html")
    else:
        return redirect(url_for('login'))


@app.route('/sightform')
def sightform():
    if "email" in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        query = "SELECT * FROM rqstforms WHERE status ='2'"
        cursor.execute(query)
        row = cursor.fetchall()
        return render_template("sightform.html", row=row)
    else:
        return redirect(url_for('login'))


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
        user = session["name"]
        phone = session["phone"]

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        now = datetime.now().date()

        files = request.files.getlist('files[]')

        # submit into db for request
        cursor.execute(
            "INSERT INTO rqstforms (mName, mDate, mAge, mGender, mLong, mLat, location, uploadedDate, user, phone) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (mName, mDate, mAge, mGender, mLong, mLat, address, now, user, phone))

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

    return render_template("completerqst.html")

@app.route('/completerqst')
def completerqst():
    if "email" in session:
        return render_template("completerqst.html")
    else:
        return redirect(url_for('login'))

@app.route('/sight', methods=['POST', 'GET'])
def sight():
    if request.method == 'POST':
        optionId = request.form['optionId']
        sDate = request.form['sDate']
        sTime = request.form['sTime']
        sAddress = request.form['sAddress']
        user = session["name"]

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        files = request.files.getlist('sights[]')

        # submit into db for request
        cursor.execute(
            "INSERT INTO sightforms (sDate, sTime, sAddress, rqstId, user) VALUES (%s, %s, %s, %s, %s)",
            (sDate, sTime, sAddress, optionId, user))

        # get id from sightform
        sightid = cursor.lastrowid

        cursor.execute('SELECT mImages FROM images WHERE rqstId = %s', [optionId])
        dbresult = cursor.fetchall()

        # keep file path but extract img name from json ** care for tuple errors
        imgdb = face_recognition.load_image_file("static/uploads/" + dbresult[0]['mImages'])
        imgdb = cv2.cvtColor(imgdb, cv2.COLOR_BGR2RGB)

        percentage = 0
        # insert image into sighting image database
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(basedir, app.config['UPLOAD_FOLDER'], filename))

                imgsight = face_recognition.load_image_file("static/uploads/" + file.filename)
                imgsight = cv2.cvtColor(imgsight, cv2.COLOR_BGR2RGB)

                encodeDB = face_recognition.face_encodings(imgdb)[0]

                encodeSight = face_recognition.face_encodings(imgsight)[0]

                faceDis = face_recognition.face_distance([encodeDB], encodeSight)

                comparingpercentage = (1.0 - (faceDis[0]))

                if(comparingpercentage > percentage):
                    percentage = comparingpercentage

                finalpercentage = round(percentage * 100, 2)

                print(str(finalpercentage) + " match")

                cursor.execute(
                    'INSERT INTO sightimages (sImages, sightId, numOfImg, comparingpercentage) VALUES (%s, %s, %s, %s)',
                    (filename, sightid, files.index(file), finalpercentage))

        cursor.close()
        mysql.connection.commit()

    return render_template("completerqst.html")


@app.route('/sightings')
def sightings():
    if "email" in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # display all sightings
        query = "SELECT rqstforms.mName, sightimages.sImages, sightimages.comparingpercentage, sightforms.sDate, sightforms.user, sightforms.sAddress FROM sightforms INNER JOIN rqstforms ON sightforms.rqstId = rqstforms.rqstId " \
                "LEFT JOIN sightimages ON sightforms.sightId = sightimages.sightId WHERE status ='2' AND numOfImg = '0'"
        cursor.execute(query)
        row = cursor.fetchall()
        cursor.close()

        return render_template("sightings.html", row=row)
    else:
        return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
