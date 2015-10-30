
import common_ndex_utilities

# body

import argparse

parser = argparse.ArgumentParser(description='change the description of a network')

parser.add_argument('username', action='store')
parser.add_argument('password', action='store')
parser.add_argument('server', action='store')
parser.add_argument('description', action='store')
parser.add_argument('--private', dest='privacy_filter', action='store_const',
                    const="PRIVATE", default=None,
                    help='only operate on private networks')

parser.add_argument('--public', dest='privacy_filter', action='store_const',
                    const="PUBLIC", default=None,
                    help='only operate on public networks')

arg = parser.parse_args()

networks = common_ndex_utilities.get_networks_administered(arg.server, arg.username, arg.password)
changes = 0
skipped = 0
networks_to_update = []

for network in networks:
    if arg.privacy_filter:
        visibility = network.get("visibility")
        readOnlyCommit = network.get("readOnlyCommitId")
        #print str(readOnlyCommit)
        if arg.privacy_filter == visibility and readOnlyCommit <= 0 :
            networks_to_update.append(network)
        else:
            skipped += 1
    else:
        networks_to_update.append(network)

print "Found " + str(len(networks_to_update)) + " networks, skipping " + str(skipped)

for network in networks_to_update:
    try:
        response = common_ndex_utilities.change_network_description(network['externalId'], arg.server, arg.username, arg.password, arg.description)
        if response == "":
            changes += 1
            print("Changed the description of: " + network['name'])
        else:
            print("FAILED to change the description of: " + network['name'])
            print(str(response))
    except:
        print("Server error for " + network['name'])


print("")
print("Changed the description of " + str(changes) + " networks for account: " + arg.username)
