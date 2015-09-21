
import common_ndex_utilities

# body

import argparse

parser = argparse.ArgumentParser(description='change the description of a network')

parser.add_argument('username', action='store')
parser.add_argument('password', action='store')
parser.add_argument('server', action='store')
parser.add_argument('description', action='store')

arg = parser.parse_args()

networks = common_ndex_utilities.get_networks_administered(arg.server, arg.username, arg.password)
changes = 0
for network in networks:
    status_code = common_ndex_utilities.change_network_description(network['externalId'], arg.server, arg.username, arg.password, arg.description)
    if status_code == 204:
        changes += 1
        print("Changed the description of: " + network['name'])
    else:
        print("FAILED to change the description of: " + network['name'])

print("")
print("Changed the description of " + str(changes) + " networks for account: " + arg.username)