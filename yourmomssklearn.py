import numpy
import pandas as pd
from pprint import pprint
from misc1 import find_closest_weather_stations
from e_coli_data import total_infections_by_codes
import misc1
import e_coli_data
from sklearn import linear_model
from typing import Dict

# Only works for Aberporth rn, too lazy
# Works for all stations now bb
"""
========== MODEL: TIME => TEMPERATURE ==========
"""

# with open('Temperature Data/aberporthdata.txt', 'r') as txt:
#     temperature_data = txt.readlines()
#     temperature_data = [entry.split() for entry in temperature_data]
#     temperature_data = temperature_data[7:]
#
# time_x = []
# temperature_y = []
#
# for entry in temperature_data:
#     if entry[2] != '---' and entry[3] != '---':
#         year = float(entry[0])
#         month = float(entry[1])
#         time = year + (month - 1) / 12
#         mean_temperature = (float(entry[2]) + float(entry[3])) / 2
#         time_x.append([time])
#         temperature_y.append(mean_temperature)
#
# time_x, temperature_y = numpy.array(time_x), numpy.array(temperature_y)
# time_to_temperature_model = linear_model.LinearRegression()
# time_to_temperature_model.fit(time_x, temperature_y)

"""
========== MODEL: TEMPERATURE => ECOLI ==========
"""

# Using Hyak's api
ecoli_file_name = 'Monthly E.Coli 2012-2020 with Location.csv'
temperature_dir = 'Temperature Data'
weather_stations = find_closest_weather_stations(ecoli_file_name, temperature_dir)


def get_model_station(station: str):
    """Does cool shit"""
    path = station + 'data.txt'
    with open('Temperature Data/' + path, 'r') as txt:
        temperature_data = txt.readlines()
        temperature_data = [entry.split() for entry in temperature_data]
        temperature_data = temperature_data[7:]

    if len(temperature_data[-1]) <= 2:
        temperature_data.pop()
    for entry in temperature_data:
        try:
            float(entry[0])
        except ValueError:
            temperature_data.remove(entry)
        if entry[2][-1] == "*":
            entry[2] = entry[2][:-1]
        if entry[3][-1] == "*":
            entry[3] = entry[3][:-1]

    ecoli = total_infections_by_codes(weather_stations[station]).to_frame()
    ecoli_time = ecoli.index.tolist()
    ecoli_time = [time[:7] for time in ecoli_time]
    ecoli_value = ecoli.values.tolist()
    temperature_x = []
    ecoli_y = []
    for entry in temperature_data:
        year = entry[0]
        month = entry[1]
        if len(month) == 1:
            month = '0' + month
        time = "{}-{}".format(year, month)
        if time in ecoli_time:
            mean_temperature = (float(entry[2]) + float(entry[3])) / 2
            ecoli_index = ecoli_time.index(time)
            ecoli = ecoli_value[ecoli_index][0]
            temperature_x.append([mean_temperature])
            ecoli_y.append(ecoli)

    temperature_x, ecoli_y = numpy.array(temperature_x), numpy.array(ecoli_y)
    temperature_to_ecoli_model = linear_model.LinearRegression()

    temperature_to_ecoli_model.fit(temperature_x, ecoli_y)

    time_x = []
    temperature_y = []

    for entry in temperature_data:
        if entry[2] != '---' and entry[3] != '---':
            year = float(entry[0])
            month = float(entry[1])
            time = year + (month - 1) / 12
            mean_temperature = (float(entry[2]) + float(entry[3])) / 2
            time_x.append([time])
            temperature_y.append(mean_temperature)


    time_x, temperature_y = numpy.array(time_x), numpy.array(temperature_y)
    time_to_temperature_model = linear_model.LinearRegression()
    time_to_temperature_model.fit(time_x, temperature_y)

    return (time_to_temperature_model, temperature_to_ecoli_model)

"""
========== PROFIT ==========
"""



def get_data_station(station: str, start: int, end: int):
    years_to_predict = [year for year in range(start, end + 1)]
    model = get_model_station(station)
    df = pd.DataFrame(columns=list('AB'))

    time_temp_model = model[0]
    temp_ecoli_model = model[1]

    for year in years_to_predict:
        temperature_prediction = time_temp_model.predict([[year]])[0]
        ecoli_prediction = temp_ecoli_model.predict([[temperature_prediction]])
        df2 = pd.DataFrame([[year, ecoli_prediction]], columns=list('AB'))
        df = df.append(df2)
    return df


def get_data_all_stations(start: int, end: int) -> Dict[str, pd.DataFrame]:
    result_so_far = {}
    for station in weather_stations:
        result_so_far[station] = get_data_station(station, start, end)
    return result_so_far


def get_percentage_increase_all_stations(start: int, end: int):
    projection = get_data_all_stations(start, end)
    station_codes = misc1.find_closest_weather_stations(misc1.hospital_data_with_locations, misc1.weather_stations_directory)
    result_so_far = {}
    for station in projection:
        past_data = e_coli_data.total_infections_by_codes(station_codes[station])
        total = past_data.sum(axis=0)
        average = total / len(past_data.index)
        df = projection[station]
        for i in range(len(df.index)):
            df.iat[i, 1] = ((df.iat[i, 1] / average) - 1) * 100
        result_so_far[station] = df
    return result_so_far


def get_total_data1(start: int, end: int):
    dfs = []
    for station in weather_stations:
        dfs.append(get_data_station(station, start, end))
    df = dfs[0]
    # for i in range(len(dfs) - 1):
    #     df = df.merge(dfs[i+1], on='A')
    # sums = df.sum(axis=1)
    # result = pd.DataFrame({'years': df['A']})
    # result = result.assign(ecoli=sums)
    # return result
    return dfs


def get_total_data(start: int, end: int):
    dfs = []
    for station in weather_stations:
        dfs.append(get_data_station(station, start, end))
    df = dfs[0]
    for i in range(len(dfs) - 1):
        df = df.merge(dfs[i+1], on='A')
    sums = df.iloc[:, 1:].sum(axis=1)
    print(sums)
    result = pd.DataFrame({'years': df['A']})
    result = result.assign(ecoli=sums)
    return result

#
# first_values = []
# data = get_total_data1(2020, 2030)
# for df in data:
#     first_values.append(df.iat[0,1])
# test = get_total_data(2020, 2030).iat[0,1]
# sum = sum(first_values)




#data = get_percentage_increase_all_stations(2020, 2030)
# data1 = get_data_station('aberporth', 2020, 2050)
# data = get_total_data(2020, 2100)




# models = get_model_station('Aberporth')
#
# for year in years_to_predict:
#     temperature_prediction = models[0].predict([[year]])[0]
#     ecoli_prediction = models[1].predict([[temperature_prediction]])
#     print("ecoli prediction for {}: {}".format(year, ecoli_prediction))




