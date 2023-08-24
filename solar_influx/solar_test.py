import re
import requests
import time
import json
from bs4 import BeautifulSoup as bs 
from influxdb import InfluxDBClient
from requests.auth import HTTPBasicAuth

INFLUXDB_ADDRESS = '192.168.178.104'
INFLUXDB_USER = 'admin'
INFLUXDB_PASSWORD = '12gamma3'
INFLUXDB_DATABASE = 'strom'

BASIC = HTTPBasicAuth('mkluge', '!0Alpha1')
URL = "http://192.168.178.171/status.html"

influxdb_client = InfluxDBClient(INFLUXDB_ADDRESS, 8086, INFLUXDB_USER, INFLUXDB_PASSWORD, None)

def _init_influxdb_database():
    databases = influxdb_client.get_list_database()
    if len(list(filter(lambda x: x['name'] == INFLUXDB_DATABASE, databases))) == 0:
        influxdb_client.create_database(INFLUXDB_DATABASE)
    influxdb_client.switch_database(INFLUXDB_DATABASE)

def send_sensor_data_to_influxdb(solar_data: dict):
    now = time.time()
    json_body = [
        {
            'measurement': "solar",
            'fields': solar_data
        }
    ]
    print(json_body)
    print("writing")
    try:
        res = influxdb_client.write_points(json_body)
    except Exception as X:
        print(X)
    print("res: " + res)
    print("done")
    if not res:
        _init_influxdb_database();

def main():
    _init_influxdb_database()
    while 1:
        solar_data={}
        try:
            response = requests.get(URL, auth=BASIC)
            if response.status_code!=200:
                print(f"Fehler beim Abruf {response.status_code}")
                time.sleep(5)
                continue
            soup = bs(response.content, "html.parser") 
            data  = str(soup.find_all("script")[1].string)
            m = re.search('var webdata_now_p = "(.*?)"', data)
            solar_data["watt_current"] = int(m.groups()[0])
            m = re.search('var webdata_today_e = "(.*?)"', data)
            solar_data["kwh_today"] = float(m.groups()[0])
            m = re.search('var webdata_total_e = "(.*?)"', data)
            solar_data["kwh_total"] = float(m.groups()[0])
            m = re.search('var webdata_alarm = "(.*?)"', data)
            if not len(m.groups()[0]):
                solar_data["alarm"] = 0
            else:
                solar_data["alarm"] = 1
                solar_data["alarm_text"] = m.groups()[0]
            send_sensor_data_to_influxdb(solar_data)
        except:
            pass
        time.sleep(60)

if __name__ == '__main__':
    main()
