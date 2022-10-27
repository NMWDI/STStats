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
        url = f'{url}&{f}'

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


def aggregate_stats():
    def rget(url):
        resp = requests.get(url)
        if resp.status_code == 200:
            rj = resp.json()
            nextlink = rj.get('@iot.nextLink')
            yield rj['value']
            if nextlink:
                yield from rget(nextlink)

    names = []
    for v in rget(f'{ST2}/Datastreams?$select=name'):
        for vi in v:
            if vi['name'] not in names:
                names.append(vi['name'])

    agencies = Counter()
    for v in rget(f'{ST2}/Locations?$select=properties'):
        for vi in v:
            agencies.update((vi['properties']['agency'],))

    return {'datastream_names': names, 'agencies_location_counts': agencies}


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
                  "depth_to_water_datastreams": st2_count("Datastreams", f="$filter=name eq 'Groundwater Levels'"),
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
        # print(f'report generation complete {time.time()-last_time}')
    return cached_report


def st_report_poll():
    while 1:
        st_report(ST2, 'st2')
        time.sleep(60)


t = Thread(target=st_report_poll)
t.setDaemon(True)
t.start()


@app.get('/st2_report')
async def get_st2_report():
    return st_report(ST2, 'st2')


LOCATION_SCHEMA = None


@app.get('/st2_validate')
async def get_st2_validation():
    global LOCATION_SCHEMA
    url = ST2
    if LOCATION_SCHEMA is None:
        resp = requests.get('https://raw.githubusercontent.com/NMWDI/VocabService/main/schemas/location.schema.json#')
        LOCATION_SCHEMA = resp.json()

    failures = []
    # for agency in ('NMBGMR', 'EBID'):
    for agency in ('NMBGMR', 'EBID'):
        locations = st_get(url, f"Locations?$top=10&$filter=properties/agency eq '{agency}'")
        for location in locations['value']:
            try:
                validate(location, LOCATION_SCHEMA)
            except ValidationError  as e:
                failures.append(e)

    return failures


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


if __name__ == '__main__':
    aggregate_stats()
