import requests
import json
from requests.auth import HTTPBasicAuth
import ndex


# body

import argparse

parser = argparse.ArgumentParser(description='get_account_statistics')

parser.add_argument('server', action='store')
parser.add_argument('username', action='store')
parser.add_argument('password', action='store')

arg = parser.parse_args()

networks = ndex.get_networks_administered(arg.server, arg.username, arg.password)
num_public = 0
num_private = 0
num_discoverable = 0

for network in networks:
    if network['visibility'] == 'PUBLIC':
        num_public += 1
    elif network['visibility'] == 'PRIVATE':
        num_private += 1
    elif network['visibility'] == 'DISCOVERABLE':
        num_discoverable += 1

print "Server: " + arg.server
print 'User: ' + arg.username
print 'Number of networks administered: ' + str(len(networks))
print ' PUBLIC: ' + str(num_public)
print ' PRIVATE: ' + str(num_private)
print ' DISCOVERABLE: ' + str(num_discoverable)
