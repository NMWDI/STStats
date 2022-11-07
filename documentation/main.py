from flask import Flask, render_template

app = Flask(__name__)


@app.route("/tutorial")
def tutorial_simple():
    return render_template('tutorial.html')


@app.route("/")
def help_link():
    return render_template('help_link.html')



