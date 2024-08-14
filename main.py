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
    st2_examples = [('Get all Locations from EBID',
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

    cocorahs_examples = [("Get all results for station NM-DA-265 from 2024-01-01 to present",
                         "https://data.cocorahs.org/export/exportreports.aspx?Format=json&ReportType=Daily&ResponseFields=all&stations=NM-DA-265&ReportDateType=timestamp&Date=01/10/2024"),
                         ("Get all results for station NM-BR-2 for 2023-11-28",
                         "https://data.cocorahs.org/export/exportreports.aspx?Format=json&ReportType=Daily&ResponseFields=all&stations=NM-BR-2&ReportDateType=reportdate&Date=11/28/2023")]

    return render_template('browser_examples.html', st2_examples=st2_examples, cocorahs_examples=cocorahs_examples)

@app.route("/apistore")
def apistore():

    apis = [dict(name="ST2",
                 description="New Mexico Water Data Initiative",
                 url="https://st2.newmexicowaterdata.org/FROST-Server/v1.1"),
            dict(name="DWW",
                 description="New Mexico Environment Department Drinking Water Watch",
                 url="https://nmenv.newmexicowaterdata.org/FROST-Server/v1.1"),
            dict(name="OSE RealTime Measurements",
                 description="New Mexico Office of the State Engineer RealTime Measurements",
                 url="https://meterexttest.oseisc.org/extmrintake/api/meas_readings/148"),
            dict(name="USGS NWIS",
                 description="National Water Information System",
                 url="https://waterservices.usgs.gov/docs/instantaneous-values/instantaneous-values-details/"),
            dict(name="WQP",
                 description="Water Quality Portal",
                 url="https://www.waterqualitydata.us/webservices_documentation/"),
            dict(name="CoCoRaHS",
                 description="Community Collaborative Rain, Hail & Snow Network",
                 url="https://data.cocorahs.org/cocorahs/Export/ExportManager.aspx"),
            dict(name="AMPAPI",
                 description="Aquifer Mapping Program API",
                 url="https://waterdata.nmt.edu")
            ]

    return render_template("apistore.html",
                           apis=apis)
# @app.route("/scoreboard")
# def scoreboard():
#     resp = requests.get('http://developer.newmexicowaterdata.org/api/v1/st2_report')
#     sb = {}
#     if resp.status_code == 200:
#         sb = resp.json()
#     return render_template("scoreboard.html", sb=sb)


@app.route("/")
def help_link():
    return render_template('index.html')


@app.route("/help")
def help():
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
