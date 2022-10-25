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
    resp = requests.get(f'{ST2}/{tag}')
    return resp.json()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get('/st2_report')
async def get_st2_report():
    obsprops = st2_get("ObservedProperties")
    print(obsprops)
    obsprops = [o['name'] for o in obsprops['value']]

    return {"locations": st2_count("Locations"),
            "things": st2_count("Things"),
            "datastreams": st2_count("Datastreams"),
            "observations": st2_count("Observations"),
            "depth_to_water_datastreams": st2_count("Datastreams", f="$filter=name eq 'Groundwater Levels'"),
            "datastream_names": 0,
            "observed_properties": obsprops
            }


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
