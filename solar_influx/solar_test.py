import re
import requests
from bs4 import BeautifulSoup as bs 

from requests.auth import HTTPBasicAuth
basic = HTTPBasicAuth('mkluge', '!0Alpha1')
URL = "http://192.168.178.171/status.html"
response = requests.get(URL, auth=basic) 
print(response.status_code) # If the request went Ok we usually get a 200 status. 
soup = bs(response.content, "html.parser") 
data  = str(soup.find_all("script")[1].string)
m = re.search('var webdata_now_p = "(.*?)"', data)
print(int(m.groups()[0]))
m = re.search('var webdata_alarm = "(.*?)"', data)
print(m.groups()[0])

