from flask import Flask, redirect, url_for, render_template

app = Flask(__name__)

@app.route('/admin')
def admin():
    return redirect(url_for("mainmenu"))

@app.route('/')
def login():
    return render_template("login.html")

@app.route('/register')
def register():
    return render_template("register.html")

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

@app.route('/aboutus')
def aboutus():
    return render_template("aboutus.html")

if __name__ == "__main__":
    app.run(debug=True)
