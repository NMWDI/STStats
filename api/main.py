import time
from collections import Counter
from datetime import datetime
from threading import Thread
from jsonschema import validate, ValidationError
from fastapi import FastAPI
import requests

app = FastAPI()

ST2 = 'https://st2.newmexicowaterdata.org/FROST-Server/v1.1'


def st_count(url, tag, f=None):
    url = f'{url}/{tag}?$count=true&$top=1'
    if f:
        url = f'{url}&$filter={f}'

    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json().get('@iot.count')
    else:
        return 0


def st_get(url, tag):
    url = f'{url}/{tag}'
    resp = requests.get(url)
    return resp.json()


@app.get("/")
async def root():
    return {"message": "Hello World"}


last_time = None
cached_report = None


def rget(url):
    resp = requests.get(url)
    if resp.status_code == 200:
        rj = resp.json()
        nextlink = rj.get('@iot.nextLink')
        yield rj['value']
        if nextlink:
            yield from rget(nextlink)


def aggregate_stats():
    names = []
    for v in rget(f'{ST2}/Datastreams?$select=name'):
        for vi in v:
            if vi['name'] not in names:
                names.append(vi['name'])

    ag = Counter()
    for v in rget(f'{ST2}/Locations?$select=properties'):
        for vi in v:
            ag.update((vi['properties']['agency'],))

    agency_counts = {}
    for k, v in ag.items():
        agency_counts[k] = {'locations': v, 'gwl_observations': agency_gwl_observations(ST2, k)}

    return {'datastream_names': names,
            'agency_counts': agency_counts}


def agency_gwl_observations(url, agency):
    obs = 0
    print(f'agency observations ==== {agency}')
    for i, locations in enumerate(agency_locations(url, agency)):
        lobs = 0
        # for i, l in enumerate(locations[:1]):
        for j, l in enumerate(locations):
            for t in l['Things']:
                for d in t['Datastreams']:
                    if d['name'] == 'Groundwater Levels':
                        lobs += st_count(url, f"Datastreams({d['@iot.id']})/Observations")
            obs += lobs
            print(i*1000+j, l['name'], lobs, obs)
        # break

    return obs


def agency_locations(url, agency):
    return rget(f"{url}/Locations?$filter=properties/agency eq '{agency}'&$expand=Things/Datastreams")


def st_report(url, tag):
    global last_time
    global cached_report

    if not cached_report or (last_time and time.time() - last_time > 60):
        def st2_count(*args, **kw):
            return st_count(url, *args, **kw)

        last_time = time.time()
        agg_stats = aggregate_stats()

        obsprops = st_get(url, "ObservedProperties")
        obsprops = [o['name'] for o in obsprops['value']]

        maxd = st_get(url, 'Observations?$orderby=phenomenonTime desc&$top=1')
        mind = st_get(url, 'Observations?$orderby=phenomenonTime asc&$top=1')
        mind = mind['value'][0]['phenomenonTime']
        maxd = maxd['value'][0]['phenomenonTime']

        now = datetime.now()
        now = now.strftime('%Y-%m-%dT%H:%M:%S.000Z')

        future_obs = st_get(url, f"Observations?$filter=phenomenonTime gt {now}&$top=1&$count=true")
        report = {"locations": st2_count("Locations"),
                  "things": st2_count("Things"),
                  "datastreams": st2_count("Datastreams"),
                  "observations": st2_count("Observations"),
                  "depth_to_water_datastreams": st2_count("Datastreams", f="name eq 'Groundwater Levels'"),
                  "observed_properties": obsprops,
                  "min_observed_datetime": mind,
                  "max_observed_datetime": maxd,
                  "future_obs": future_obs['@iot.count'],
                  "@report.timestamp": now,
                  "@report.duration": time.time() - last_time,
                  "@report.sturl": url
                  }
        report.update(agg_stats)
        cached_report = report
        # print(f'report generation complete {time.time() - last_time}')

    # print(cached_report)
    return cached_report


def st_report_poll():
    while 1:
        st_report(ST2, 'st2')
        time.sleep(3600)


t = Thread(target=st_report_poll)
t.setDaemon(True)
t.start()


@app.get('/st2_report')
async def get_st2_report():
    return cached_report


LOCATION_SCHEMA = None
THING_SCHEMA = None
THING_SCHEMA = {
    "$id": "https://vocab.newmexicowaterdata.org/schemas/gwl_thing",
    "title": "NMWDI Groundwater Level Thing Schema",
    "description": "",
    "version": "0.0.1",
    "type": "object",
    "required": ["name", "description", "properties"],
    "properties": {
        "name": {
            "type": "string",
            "description": "name of a Thing for groundwater levels should be `Water Well`"
        },
        "description": {
            "type": "string",
            "description": "description of this location"
        },
        "properties": {
            "type": "object",
            "description": "a flexible place to associate additional attributes with a thing",
            "required": ["welldepth", "welldepth_unit", "geologic_formation"],
            "welldepth": {
                "type": "number",
                "description": ""
            },
            "welldepth_unit": {
                "type": "string",
                "enum": [
                    "FTBGS",
                    "MBGS"
                ],
                "description": ""
            },
            "geologic_formation":
                {
                    "type": "string",
                    "description": ""
                }
        }
    }
}

DATASTREAM_SCHEMA = {
    "$id": "https://vocab.newmexicowaterdata.org/schemas/gwl_thing",
    "title": "NMWDI Groundwater Level Thing Schema",
    "description": "",
    "version": "0.0.1",
    "type": "object",
    "required": ["name", "description", "properties"],
    "properties": {
        "name": {
            "type": "string",
            "description": "name for Groundwater levels",
            "enum": ["Groundwater Levels", "Groundwater Levels(Acoustic)", "Groundwater Levels(Pressure)"]
        },
        "description": {
            "type": "string",
            "description": "description of this location"
        },
        "properties": {
            "required": ["topic"],
            "type": "object",
            "description": "a flexible place to associate additional attributes with a thing",
            "topic": {"type": "string",
                      "enum": ["Water Quantity"]}
        }
    }
}


@app.get('/st2_validate')
async def get_st2_validation():
    return validation(ST2)


def validation(url):
    global LOCATION_SCHEMA, THING_SCHEMA, DATASTREAM_SCHEMA

    if LOCATION_SCHEMA is None:
        resp = requests.get('https://raw.githubusercontent.com/NMWDI/VocabService/main/schemas/location.schema.json#')
        LOCATION_SCHEMA = resp.json()

    if THING_SCHEMA is None:
        resp = requests.get(
            'https://raw.githubusercontent.com/NMWDI/VocabService/main/schemas/groundwaterlevel.thing.schema.json#')
        THING_SCHEMA = resp.json()

    if DATASTREAM_SCHEMA is None:
        resp = requests.get(
            'https://raw.githubusercontent.com/NMWDI/VocabService/main/schemas/groundwaterlevel.datastream.schema.json#'
        )
        DATASTREAM_SCHEMA = resp.json()

    flocations = []
    fthings = []
    fdatastreams = []
    for agency in ('NMBGMR', 'EBID'):
        locations = st_get(url, f"Locations?$top=10&$filter=properties/agency eq '{agency}'&$expand=Things/Datastreams")
        for location in locations['value']:
            try:
                validate(location, LOCATION_SCHEMA)
            except ValidationError as e:
                flocations.append(e)

            for thing in location['Things']:
                try:
                    validate(thing, THING_SCHEMA)
                except ValidationError as e:
                    fthings.append(e)

                for datastream in thing['Datastreams']:
                    try:
                        validate(datastream, DATASTREAM_SCHEMA)
                    except ValidationError as e:
                        fdatastreams.append(e)

    return flocations, fthings, fdatastreams


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


if __name__ == '__main__':
    fl, ft, fds = validation(ST2)
    print(len(fl), len(ft), len(fds))
    for f in fds:
        print(f)

    # aggregate_stats()
