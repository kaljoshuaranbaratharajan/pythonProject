from flask import Flask
from flask_mysqldb import MySQL
import MySQLdb.cursors
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


def webcamtesting():
    imgpath = "static/uploads/"
    images = []
    clsnames = []
    imglist = os.listdir(imgpath)

    for cls in imglist:
        currentimg = cv2.imread(f'{imgpath}/{cls}')
        images.append(currentimg)
        clsnames.append(os.path.splitext(cls)[0])

    def encodings(images):
        encodeList = []
        for img in images:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encode = face_recognition.face_encodings(img)[0]
            encodeList.append(encode)
        return encodeList

    def recordwebcam(name):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        now = datetime.now().date()
        cursor.execute('SELECT * FROM webcamresults WHERE foundName = %s AND encounterDatetime = %s',
                       (name, now))
        results = cursor.fetchall()
        if len(results) <= 0:
            sql = "INSERT INTO webcamresults (foundName, encounterDatetime, encounterLocation) VALUES (%s, %s, %s)"
            val = (name, now, "George Town, Penang, Malaysia")
            cursor.execute(sql, val)
        else:
            sql = "UPDATE webcamresults SET encounterDatetime = %s, encounterLocation = %s WHERE foundName = %s"
            val = (now, "George Town, Penang, Malaysia", name)
            cursor.execute(sql, val)
        mysql.connection.commit()

    encodeListKnown = encodings(images)

    capture = cv2.VideoCapture(0)
    process_this_frame = True

    while True:
        success, img = capture.read()
        imgsmall = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgsmallrgb = imgsmall[:, :, ::-1]

        if process_this_frame:
            # Find all the faces and face encodings in the current frame of video
            currentframe = face_recognition.face_locations(imgsmallrgb)
            encodecurrentframe = face_recognition.face_encodings(imgsmallrgb, currentframe)

            face_names = []
            for face_encoding in encodecurrentframe:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(encodeListKnown, face_encoding)
                name = ""

                # Or instead, use the known face with the smallest distance to the new face
                face_distances = face_recognition.face_distance(encodeListKnown, face_encoding)
                matchindex = np.argmin(face_distances)
                if matches[matchindex]:
                    name = clsnames[matchindex].upper()

                face_names.append(name)

        process_this_frame = not process_this_frame

        for (top, right, bottom, left), name in zip(currentframe, face_names):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Draw a box around the face
            cv2.rectangle(img, (left, top), (right, bottom), (0, 0, 255), 2)

            # Draw a label with a name below the face
            cv2.rectangle(img, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(img, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
            recordwebcam(name)

        cv2.imshow("Webcam", img)
        cv2.waitKey(1)
