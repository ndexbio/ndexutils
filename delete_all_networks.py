import requests
import json
from requests.auth import HTTPBasicAuth
import ndex

def make_network_public(network_id, server, username, password):
    url = 'http://'+server+'/network/' + network_id;
    payload = {"visibility":"PRIVATE"}
    headers = {
        'content-type': 'application/json',
    }
    auth = HTTPBasicAuth(username, password)
    r = requests.delete(url, auth=auth, data=json.dumps(payload), headers=headers)
    return r.status_code

# body

import argparse

parser = argparse.ArgumentParser(description='delete_all_networks')

parser.add_argument('username', action='store')
parser.add_argument('password', action='store')
parser.add_argument('server', action='store')

arg = parser.parse_args()

networks = ndex.get_networks_administered(arg.server, arg.username, arg.password)
num_networks_deleted = 0
num_networks_not_deleted = 0;
for network in networks:
    status_code = make_network_public(network['externalId'], arg.server, arg.username, arg.password)
    print 'status code = ' + str(status_code)
    if status_code == 204:
        print("Deleted " + network['name'] + "' PRIVATE")
        num_networks_deleted += 1
    else:
        num_networks_not_deleted += 1
        print("FAILED to delete " + network['name'])

print
print("Deleted " + str(num_networks_deleted) + " networks for account: " + arg.username)
if num_networks_not_deleted > 0:
    print( str(num_already_private) + " networks were not deleted." )