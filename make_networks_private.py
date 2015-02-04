import requests
import json
from requests.auth import HTTPBasicAuth
import ndex

def make_network_public(network_id, server, username, password):
    url = 'http://'+server+'/network/' + network_id + '/summary'
    payload = {"visibility":"PRIVATE"}
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
parser.add_argument('server', action='store')

arg = parser.parse_args()

networks = ndex.get_networks_administered(arg.server, arg.username, arg.password)
num_already_private = 0
changes = 0
for network in networks:
    if network['visibility'] != 'PRIVATE':
        status_code = make_network_public(network['externalId'], arg.server, arg.username, arg.password)
        if status_code == 204:
            changes += 1
            print("Made '" + network['name'] + "' PRIVATE")
        else:
            print("FAILED to make '" + network['name'] + "' PRIVATE")
    else:
        num_already_private += 1
        print("'" + network['name'] + "'" + " is already PRIVATE")
print()
print("Made " + str(changes) + " networks PRIVATE for account: " + arg.username)
if num_already_private > 0:
    print( str(num_already_private) + " were already PRIVATE" )