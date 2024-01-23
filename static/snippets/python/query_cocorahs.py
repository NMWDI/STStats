from datetime import date
import json
import requests

def query_func(country: str | None = None,
               state: str | None = None,
               county: str | None = None,
               stations: list | None = None,
               report_date: str | None = None,
               start_date: str | None = None,
               end_date: str | None = None,
               time_stamp: str | None = None,
               res_format: str = 'json',
               report_type: str = 'Daily',
               response_fields: str = 'all',
               chatty = False
               ):

    base_url = 'https://data.cocorahs.org/export/exportreports.aspx'
    query_params = []

    # response format - only change if you want it to not be a JSON
    if res_format:
        query_params.append(f'Format={res_format}')

    # report type
    if report_type:
        query_params.append(f'ReportType={report_type}')

    # response fields
    if response_fields:
        query_params.append(f'ResponseFields={response_fields}')

    # the country
    if country:
        query_params.append(f'country={country}')

    # the state
    if state:
        query_params.append(f'State={state}')
    
    # the county - a two-letter abbreviation
    if county:
        query_params.append(f'county={county}')

    # a list of station numbers to query
    if stations:
        stations_str = ','.join(stations)
        query_params.append(f'stations={stations_str}')

    # single report date
    if report_date:
        try:
            rd = date.fromisoformat(report_date)
        except ValueError:
            raise ValueError("Incorrect report_date format, should be YYYY-MM-DD")

        report_date_str = rd.strftime('%m/%d/%Y')
        query_params.append(f'ReportDateType=reportdate&Date={report_date_str}')
    
    if time_stamp:
        try:
            ts = date.fromisoformat(time_stamp)
        except ValueError:
            raise ValueError("Incorrect time_stamp format, should be YYYY-MM-DD")

        time_stamp_str = ts.strftime('%m/%d/%Y')
        query_params.append(f'ReportDateType=timestamp&Date={time_stamp_str}')

    # start and end dates
    if start_date and end_date:
        try:
            sd = date.fromisoformat(start_date)
        except ValueError:
            raise ValueError("Incorrect start_date format, should be YYYY-MM-DD")
        
        try:
            ed = date.fromisoformat(end_date)
        except ValueError:
            raise ValueError("Incorrect end_date format, should be YYYY-MM-DD")
        
        start_date_str = sd.strftime('%m/%d/%Y')
        query_params.append(f'ReportDateType=reportdate&StartDate={start_date_str}')

        end_date_str = ed.strftime('%m/%d/%Y')
        query_params.append(f'EndDate={end_date_str}')

    
    query_str = '&'.join(query_params)
    query_url = f'{base_url}?{query_str}'
    response = requests.get(query_url)

    if chatty:
        print()
        print(response)
        print()
        print(json.dumps(response.json(), indent=4))
        print()
        print(query_url)

    return response.json()

if __name__ == "__main__":
    stations_dates = [(["NM-BR-2"], '2024-01-01'),
                      (["NM-DA-265"], '2024-01-01')]
    
    for station_date in stations_dates:
        results = query_func(stations=station_date[0],
                             time_stamp=station_date[1],
                             chatty=True)