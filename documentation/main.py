from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def help_link():
    return render_template('help_link.html')


