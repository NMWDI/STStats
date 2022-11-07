from flask import Flask, render_template

app = Flask(__name__)


@app.route("/tutorial/<page>")
def tutorial(page):
    return render_template(f'tutorial{page}.html')


@app.route("/")
def help_link():
    return render_template('help_link.html')



