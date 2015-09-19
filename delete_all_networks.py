
import common_ndex_utilities

# body

import argparse

parser = argparse.ArgumentParser(description='delete_all_networks')

parser.add_argument('username', action='store')
parser.add_argument('password', action='store')
parser.add_argument('server', action='store')

arg = parser.parse_args()

networks = common_ndex_utilities.get_networks_administered(arg.server, arg.username, arg.password)
num_networks_deleted = 0
num_networks_not_deleted = 0;
for network in networks:
    status_code = common_ndex_utilities.delete_network(network['externalId'], arg.server, arg.username, arg.password)
    print 'status code = ' + str(status_code)
    if status_code == 204:
        print("Deleted " + network['name'] + "' PRIVATE")
        num_networks_deleted += 1
    else:
        num_networks_not_deleted += 1
        print("FAILED to delete " + network['name'])

print("")
print("Deleted " + str(num_networks_deleted) + " networks for account: " + arg.username)
if num_networks_not_deleted > 0:
    print( str(num_networks_not_deleted) + " networks were not deleted." )