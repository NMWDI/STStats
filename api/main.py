from fastapi import FastAPI
import requests

app = FastAPI()


def st2_count(tag, f=None):
    base = 'https://st2.newmexicowaterdata.org/FROST-Server/v1.1'
    url = f'{base}/{tag}?$count=true&$top=1'
    if f:
        url = f'{url}&{f}'

    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json().get('@iot.count')
    else:
        return 0


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get('/st2_report')
async def get_st2_report():
    return {"locations": st2_count("Locations"),
            "things": st2_count("Things"),
            "Depth To Water Datastreams": st2_count("Datastreams", f="$filter=name eq 'Groundwater Levels'")
            }


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
