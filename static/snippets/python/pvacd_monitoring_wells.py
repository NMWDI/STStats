from pprint import pprint

import requests

BASE_URL = 'https://st2.newmexicowaterdata.org/FROST-Server/v1.1'


def get_pvacd_monitoring_wells():
    url = f'{BASE_URL}/Locations?$filter=properties/agency eq \'PVACD\'&$expand=Things'
    resp = requests.get(url)
    if resp.ok:
        return resp.json()


def main():
    wells = get_pvacd_monitoring_wells()
    pprint(wells)


if __name__ == '__main__':
    main()