
import common_ndex_utilities

# body

import argparse

parser = argparse.ArgumentParser(description='get_account_statistics')

parser.add_argument('username', action='store')
parser.add_argument('password', action='store')
parser.add_argument('server', action='store')
parser.add_argument('version', action='store')

arg = parser.parse_args()

networks = common_ndex_utilities.get_networks_administered(arg.server, arg.username, arg.password)
changes = 0
for network in networks:
    status_code = common_ndex_utilities.change_network_version(network['externalId'], arg.server, arg.username, arg.password, arg.version)
    if status_code == 204:
        changes += 1
        print("Changed the version of: " + network['name'])
    else:
        print("FAILED to change the version of: " + network['name'])

print("")
print("Changed the version of " + str(changes) + " networks for account: " + arg.username)
