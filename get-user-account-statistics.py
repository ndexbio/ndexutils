import requests
import json
from requests.auth import HTTPBasicAuth

def get_num_networks_administered(username, password):
    url = 'http://54.148.42.155/rest/network/search/0/1000'
    payload = {"accountName":username,"permission":"ADMIN","searchString":""}
    headers = {
        'content-type': 'application/json',
    }
    auth = HTTPBasicAuth(username, password)
    r = requests.post(url, auth=auth, data=json.dumps(payload), headers=headers)
    networks = r.json()
    return len(networks)

# body

import argparse

parser = argparse.ArgumentParser(description='get_account_statistics')

parser.add_argument('username', action='store')
parser.add_argument('password', action='store')

arg = parser.parse_args()

num_networks_administered = get_num_networks_administered(arg.username, arg.password)

print "User: " + arg.username
print "Number of networks administered: " + str(num_networks_administered)
