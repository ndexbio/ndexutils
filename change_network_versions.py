import requests
import json
from requests.auth import HTTPBasicAuth
import ndex

def change_network_version(network_id, server, username, password, version):
    url = 'http://'+server+'/network/' + network_id + '/summary'
    payload = {"version":version}
    headers = {
        'content-type': 'application/json',
    }
    auth = HTTPBasicAuth(username, password)
    r = requests.post(url, auth=auth, data=json.dumps(payload), headers=headers)
    return r.status_code

# body

import argparse

parser = argparse.ArgumentParser(description='get_account_statistics')

parser.add_argument('username', action='store')
parser.add_argument('password', action='store')
parser.add_argument('version', action='store')
parser.add_argument('server', action='store')


arg = parser.parse_args()

networks = ndex.get_networks_administered(arg.server, arg.username, arg.password)
changes = 0
for network in networks:
    status_code = change_network_version(network['externalId'], arg.server, arg.username, arg.password, arg.version)
    if status_code == 204:
        changes += 1
        print("Changed the version of: " + network['name'])
    else:
        print("FAILED to change the version of: " + network['name'])

print("")
print("Changed the version of " + str(changes) + " networks for account: " + arg.username)
