from flask import Flask, render_template

app = Flask(__name__)

DESCRIPTIONS = ['Start', 'Getting More Data', 'Writing to CSV', 'JSON Schema']

@app.route("/tutorial/<int:page>")
def tutorial(page):
    page_description = DESCRIPTIONS[page]

    return render_template(f'tutorial{page}.html',
                           page=page, page_description=page_description)

@app.route("/qgis")
def qgis():
    return render_template("qgis_example.html")


@app.route("/browser_examples")
def examples():
    return render_template('browser_examples.html')


@app.route("/")
def help_link():
    return render_template('index.html')



