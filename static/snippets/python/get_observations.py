import matplotlib.pyplot as plt

import requests

BASE_URL = 'https://st2.newmexicowaterdata.org/FROST-Server/v1.1'


def get_location(pid):
    url = f'{BASE_URL}/Locations?$filter=name eq \'{pid}\'&$expand=Things/Datastreams'
    print(url)
    resp = requests.get(url)
    if resp.ok:
        return resp.json()['value'][0]


def get_datastream(pointid, thing_name, datastream_name):
    location = get_location(pointid)
    for thing in location['Things']:
        if thing['name'] == thing_name:
            for ds in thing['Datastreams']:
                if ds['name'] == datastream_name:
                    return ds


def rget(url, items=None):
    if items is None:
        items = []

    resp = requests.get(url)
    if resp.ok:
        items.extend(resp.json()['value'])
        if '@iot.nextLink' in resp.json():
            items = rget(resp.json()['@iot.nextLink'], items)
    return items


def get_observations():
    pointid = 'EB-220'
    ds = get_datastream(pointid, "Water Well", "Groundwater Levels(Pressure)")

    selflink = ds['@iot.selfLink']
    url = f'{selflink}/Observations?$orderby=phenomenonTime desc'

    items = rget(url)
    return items


def main():
    observations = get_observations()

    xs, ys = [], []
    for obs in observations:
        xs.append(obs['resultTime'])
        ys.append(obs['result'])

    plt.plot(xs, ys)
    plt.show()


if __name__ == '__main__':
    main()
