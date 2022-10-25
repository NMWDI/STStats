import time
from collections import Counter
from datetime import datetime
from threading import Thread

from fastapi import FastAPI
import requests

app = FastAPI()

ST2 = 'https://st2.newmexicowaterdata.org/FROST-Server/v1.1'




def st2_count(tag, f=None):
    url = f'{ST2}/{tag}?$count=true&$top=1'
    if f:
        url = f'{url}&{f}'

    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json().get('@iot.count')
    else:
        return 0


def st2_get(tag):
    url = f'{ST2}/{tag}'
    resp = requests.get(f'{ST2}/{tag}')
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


def st2_report():
    global last_time
    global cached_report
    if not cached_report or (last_time and time.time() - last_time > 60):
        last_time = time.time()
        agg_stats = aggregate_stats()

        obsprops = st2_get("ObservedProperties")
        obsprops = [o['name'] for o in obsprops['value']]

        maxd = st2_get('Observations?$orderby=phenomenonTime desc&$top=1')
        mind = st2_get('Observations?$orderby=phenomenonTime asc&$top=1')
        mind = mind['value'][0]['phenomenonTime']
        maxd = maxd['value'][0]['phenomenonTime']

        now = datetime.now()
        now = now.strftime('%Y-%m-%dT%H:%M:%S.000Z')

        future_obs = st2_get(f"Observations?$filter=phenomenonTime gt {now}&$top=1&$count=true")
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
                  "@report.duration": time.time()-last_time
                  }
        report.update(agg_stats)
        cached_report = report
        # print(f'report generation complete {time.time()-last_time}')
    return cached_report


def st2_report_poll():
    while 1:
        st2_report()
        time.sleep(60)


t = Thread(target=st2_report_poll)
t.setDaemon(True)
t.start()


@app.get('/st2_report')
async def get_st2_report():
    return st2_report()


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


if __name__ == '__main__':
    aggregate_stats()