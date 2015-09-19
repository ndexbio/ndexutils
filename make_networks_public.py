
import common_ndex_utilities

# body

import argparse

parser = argparse.ArgumentParser(description='get_account_statistics')

parser.add_argument('username', action='store')
parser.add_argument('password', action='store')
parser.add_argument('server', action='store')

arg = parser.parse_args()

networks = common_ndex_utilities.get_networks_administered(arg.server, arg.username, arg.password)
num_already_public = 0
changes = 0
for network in networks:
    if network['visibility'] != 'PUBLIC':
        status_code = common_ndex_utilities.set_network_visibility(network['externalId'], arg.server, arg.username, arg.password, "PUBLIC")
        if status_code == 204:
            changes += 1
            print("Made '" + network['name'] + "' PUBLIC")
        else:
            print("FAILED to make '" + network['name'] + "' PUBLIC")
    else:
        num_already_public += 1
        print("'" + network['name'] + "'" + " is already PUBLIC")
print("")
print("Made " + str(changes) + " networks PUBLIC for account: " + arg.username)
if num_already_public > 0:
    print( str(num_already_public) + " were already PUBLIC" )