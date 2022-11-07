from flask import Flask, render_template

app = Flask(__name__)


@app.route("/tutorial0")
def tutorial0():
    return render_template('tutorial0.html')


@app.route("/tutorial1")
def tutorial1():
    return render_template('tutorial1.html')


@app.route("/")
def help_link():
    return render_template('help_link.html')



