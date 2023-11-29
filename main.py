import os
import yaml
import requests
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
    examples = [('Get all Locations from EBID',
                 "https://st2.newmexicowaterdata.org/FROST-Server/v1.1/Locations?$filter=properties/agency eq 'EBID'"),
                ('Get all Locations and Things from EBID',
                 "https://st2.newmexicowaterdata.org/FROST-Server/v1.1/Locations?$filter=properties/agency eq "
                 "'EBID'&$expand=Things"),
                ("Get all Locations and Things with a Location name that startswith 'AR-'<br/>",
                 "https://st2.newmexicowaterdata.org/FROST-Server/v1.1/Locations?$filter=startswith(name,"
                 "'AR-')&$expand=Things"),
                ("Get all Locations and Things within a given bounding box defined by latitudes and longitudes",
                 "https://st2.newmexicowaterdata.org/FROST-Server/v1.1/Locations?$filter=st_within(location, "
                 "geography'POLYGON((-106.9466 34.1201,-106.8038 34.1201,-106.8038 34.0086,-106.9466 34.0086,-106.9466 34.1201))')&$expand=Things"),
                ("Get all datastreams with name 'Groundwater level(Pressure)'",
                 "https://st2.newmexicowaterdata.org/FROST-Server/v1.1/Datastreams?$filter=name eq 'Groundwater level(Pressure)'"),
                ]

    return render_template('browser_examples.html', examples=examples)


@app.route("/scoreboard")
def scoreboard():
    resp = requests.get('http://developer.newmexicowaterdata.org/api/v1/st2_report')
    sb = {}
    if resp.status_code == 200:
        sb = resp.json()
    return render_template("scoreboard.html", sb=sb)


@app.route("/")
def help_link():
    return render_template('index.html')


@app.route("/snippets")
def get_snippets():
    ds = []
    root = 'static/snippets/python'
    for path in os.listdir(root):
        if path.endswith('.py'):
            with open(os.path.join(root, path), 'r') as rfile:
                text = rfile.read()
                yaml_name = os.path.splitext(path)[0]
                ypath = os.path.join(root, f'{yaml_name}.yaml')
                yd = {}
                if os.path.isfile(ypath):
                    with open(ypath, 'r') as yfile:
                        yd = yaml.load(yfile, Loader=yaml.FullLoader)

                ds.append(dict(name=yd.get('name', ''), description=yd.get('description', ''), text=text))
    return render_template('snippets.html', datasets=ds)
