
import ebs.ebs2cx as ebs2cx
import ndex.client as nc
import ndex.networkn as networkn
import ndex.beta.layouts as layouts
import ndex.beta.toolbox as toolbox
import argparse
import json

NETWORK_ID_LISTS = {"dev2":
                        ["f83a4b58-6186-11e5-8ac5-06603eb7f303",
                         "535eb44a-6188-11e5-8ac5-06603eb7f303",
                         "a49aaae0-6191-11e5-8ac5-06603eb7f303",
                         "1fd12dbd-6192-11e5-8ac5-06603eb7f303",
                         "fab184fb-6194-11e5-8ac5-06603eb7f303",
                         "0c2862fa-6196-11e5-8ac5-06603eb7f303",
                         "15a017bb-6196-11e5-8ac5-06603eb7f303"
                         #"8eaff319-bfff-11e6-8820-0660b7976219"
                        ],
                    "public_fix":
                        ["92180cef-6191-11e5-8ac5-06603eb7f303"],
                    "big-dev2":
                        {"09f3c90a-121a-11e6-a039-06603eb7f303"},
                    "big-preview":
                        {"09f3c90a-121a-11e6-a039-06603eb7f303"},
                    "dev2-newguy":
                        ["aef0380a-c0b9-11e6-b256-0660b7976219",
                         "aee64cf9-c0b9-11e6-b256-0660b7976219",
                         "aed228b8-c0b9-11e6-b256-0660b7976219",
                         "aebea0b7-c0b9-11e6-b256-0660b7976219",
                         "aea8f5d6-c0b9-11e6-b256-0660b7976219",
                         "ae89d515-c0b9-11e6-b256-0660b7976219",
                         "af10914c-c0b9-11e6-b256-0660b7976219",
                         "aef9adeb-c0b9-11e6-b256-0660b7976219"
                        ],
                    "preview":
                        [
                        "15a017bb-6196-11e5-8ac5-06603eb7f303",
                        "0c2862fa-6196-11e5-8ac5-06603eb7f303",
                        "fab184fb-6194-11e5-8ac5-06603eb7f303",
                        "1fd12dbd-6192-11e5-8ac5-06603eb7f303",
                        "a49aaae0-6191-11e5-8ac5-06603eb7f303",
                        "92180cef-6191-11e5-8ac5-06603eb7f303",
                        "535eb44a-6188-11e5-8ac5-06603eb7f303",
                        "f83a4b58-6186-11e5-8ac5-06603eb7f303"
                        ]
}

DIRECTED_INTERACTIONS = ["controls-state-change-of",
                         "controls-transport-of",
                         "controls-phosphorylation-of",
                         "controls-expression-of",
                         "catalysis-precedes",
                         "controls-production-of",
                         "controls-transport-of-chemical",
                         "chemical-affects",
                         "used-to-produce"
                         ]

def get_template(ndex, template_id):
    if not template_id:
        raise ValueError("no template id")
    print "template_id: " + str(args.template_id)
    response = ndex.get_network_as_cx_stream(args.template_id)
    template_cx = response.json()
    t_network = networkn.NdexGraph(template_cx)
    return t_network


def get_network_to_convert(ndex, network_name, username):
    search_string = "'%s'" % network_name
    networks_found = []
    search_result = ndex.search_networks(search_string=search_string, account_name=username)
    if "networks" in search_result:
        networks_in_account = search_result["networks"]
    else:
        networks_in_account = search_result

    for network in networks_in_account:
        if "properties" in network:
            for property in network["properties"]:
                property_name = property["predicateString"]
                if property_name == "format_me":
                    networks_found.append(network)

    if len(networks_found) > 1:
        raise ValueError("multiple networks marked for formatting matching '%s' for user %s" % (network_name, username))
    elif len(networks_found) == 0:
        raise ValueError("zero networks marked for formatting matching '%s' for user %s" % (network_name, username))
    else:
        ns =networks_found[0]
        network_id = ns["externalId"]
        response = ndex.get_network_as_cx_stream(network_id)
    cx = response.json()
    network = networkn.NdexGraph(cx)
    return network, network_id


def update_network(ndex, network_id, network, template_network):
    print "filtering " + str(network_id)
    ebs2cx.ndex_edge_filter(network)

    # apply graphic style
    print "styling"
    toolbox.apply_network_as_template(network, template_network)

    print "layout"
    # apply layout
    layouts.apply_directed_flow_layout(network, directed_edge_types=DIRECTED_INTERACTIONS)

    print "update"
    # update network
    ndex.update_cx_network(network.to_cx_stream(), network_id)

parser = argparse.ArgumentParser(description='upload-ebs-to-ndex arguments')

# name or flags - Either a name or a list of option strings, e.g. foo or -f, --foo.
# action - The basic type of action to be taken when this argument is encountered at the command line.
# nargs - The number of command-line arguments that should be consumed.
# const - A constant value required by some action and nargs selections.
# default - The value produced if the argument is absent from the command line.
# type - The type to which the command-line argument should be converted.
# choices - A container of the allowable values for the argument.
# required - Whether or not the command-line option may be omitted (optionals only).
# help - A brief description of what the argument does.
# metavar - A name for the argument in usage messages.
# dest - The name of the attribute to be added to the object returned by parse_args().

parser.add_argument('-z' ,
                    dest='network_name',
                    action='store',
                    default=None
                    )

parser.add_argument('-d',
                    action='store',
                    dest='network_id_list_name',
                    default=None
                    )

parser.add_argument('-n',
                    action='store',
                    dest='server',
                    help='NDEx server for the target NDEx account',
                    default='http://www.ndexbio.org/rest'
                    )

parser.add_argument('-u',
                    dest='username',
                    action='store',
                    help='username for the target NDEx account')

parser.add_argument('-p',
                    dest='password',
                    action='store',
                    help='password for the target NDEx account')

parser.add_argument('-t',
                    action='store',
                    dest='template_id',
                    help='network id for the network to use as a graphic template')


args = parser.parse_args()

print vars(args)

ndex = nc.Ndex(args.server, args.username, args.password)

if args.template_id:
    print "template_id: " + str(args.template_id)
    response = ndex.get_network_as_cx_stream(args.template_id)
    template_cx = response.json()
    template_network = networkn.NdexGraph(template_cx)
else:
    path = "test_dir/NCI_Style.cx"
    with open(path, 'rU') as cxfile:
        cx = json.load(cxfile)
        template_network = networkn.NdexGraph(cx)

if args.network_id_list_name:
    network_ids = NETWORK_ID_LISTS[args.network_id_list_name]
    for network_id in network_ids:
        response = ndex.get_network_as_cx_stream(network_id)
        cx = response.json()
        network = networkn.NdexGraph(cx)
        update_network(ndex, network_id, network,template_network)

else:

    network_name = ebs2cx.network_name_from_path(file)
    print network_name
    network, network_id = get_network_to_convert(ndex, network_name, args.username)
    update_network(ndex, network_id, network,template_network)

#network.write_to('temp_network.cx')




