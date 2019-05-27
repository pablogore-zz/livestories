import datetime
import os
import urllib.request
from collections import namedtuple
from pathlib import Path
import pandas as pd
import xlrd

from config import BASE_URL, FILE_PREFIX

UnemploymentRecord = namedtuple('UnemploymentRecord', ('laus_code',
                                                       'state_fips_code',
                                                       'country_fips_code',
                                                       'name',
                                                       'year',
                                                       'labor_force',
                                                       'employed',
                                                       'unemployment',
                                                       'unemployment_rate'))


def average(data, is_country=False):
    name = data['name'].str.split(",", expand=True)

    if is_country is True:
        data['name'] = name[0]
    else:
        data['name'] = name[1]

    return data.groupby(['name', 'year'])['unemployment'].mean().reset_index(name='avg')


def build_data_frame(data_files):
    result = pd.DataFrame()
    for url in data_files:
        data = load_data(url)
        result = result.append(data, sort=False)
    return result


def load_data(url):
    request = urllib.request.Request(url)
    response = urllib.request.urlopen(request)

    workbook = xlrd.open_workbook(file_contents=response.read())
    sheet = workbook.sheet_by_index(0)

    data = []

    for index in range(6, sheet.nrows - 4):
        row = sheet.row_values(index)
        record = build_unemployment_tuple(row)
        data.append(record)

    return pd.DataFrame(data, columns=UnemploymentRecord._fields)


def build_unemployment_tuple(row):
    record = UnemploymentRecord(
        laus_code=row[0],
        state_fips_code=row[1],
        country_fips_code=row[2],
        name=row[3],
        year=int(row[4]),
        labor_force=int(row[6]) if row[6] != 'N.A.' else 0,
        employed=int(row[7]) if row[7] != 'N.A.' else 0,
        unemployment=int(row[8]) if row[8] != 'N.A.' else 0,
        unemployment_rate=float(row[9]) if row[9] != 'N.A.' else 0.)

    return record


if __name__ == '__main__':
    current_year = datetime.datetime.today().year
    year_list = range(2018, current_year)

    files = ["{0}/{1}{2}.xlsx".format(BASE_URL, FILE_PREFIX, str(year)[-2:]) for year in year_list]

    df = build_data_frame(files)

    state = average(df.copy(), False)
    country = average(df.copy(), True)

    path = Path().absolute().joinpath("files")

    if not os.path.exists(path):
        os.makedirs(path)

    state.to_csv(os.path.join(path, r'states_{0}.csv'.format(datetime.datetime.now().timestamp())))
    country.to_csv(os.path.join(path, r'countries_{0}.csv'.format(datetime.datetime.now().timestamp())))
