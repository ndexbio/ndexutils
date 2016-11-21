
import ebs.ebs2cx as ebs2cx
import sys
from ebs import temp_append_path
sys.path.insert(1, temp_append_path)

import ndex.client as nc
import ndex.networkn as networkn
import json
import os
from bson.json_util import dumps

# body

import argparse

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

parser.add_argument('-d',
                    action='store',
                    default='$wd$',
                    dest='directory',
                    help='directory that is the source for EBS files'
                    )

parser.add_argument('-t',
                    action='store',
                    dest='template',
                    help='network id for the network to use as a graphic template')

parser.add_argument('-g',
                    action='store',
                    dest='group',
                    help='the groupname to which the uploaded EBS networks should be assigned')

parser.add_argument('-l',
                    action='store',
                    dest='layout',
                    help='the layout algorithm to apply to each EBS file')

parser.add_argument('-m',
                    action='store',
                    dest='max',
                    type=int,
                    help='the maximum number of files to upload - useful for testing')

# parser.print_help()

# example:
# -n
# "http://dev2.ndexbio.org"
# -l
# "directed_flow"
# -p
# "drh"
# -u
# "mupit"
# -t
# "8981e7f2-900f-11e6-93d8-0660b7976219"
# -g
# "test group 1"
# -m
# 5
# -d
# "test_dir/pid_EXTENDED_BINARY_SIF_2016-09-24T14:04:47.203937"

args = parser.parse_args()

print vars(args)

ndex = nc.Ndex(args.server, args.username, args.password)
template_network = None

if args.template:
    response = ndex.get_network_as_cx_stream(args.template)
    template_cx = response.json()
    #print template_network
    template_network = networkn.NdexGraph(template_cx)

    print "Cytoscape template: " + str(template_network)

ebs2cx.upload_ebs_files(
    args.directory,
    ndex,
    #groupname=args.group,
    template_network=template_network,
    layout=args.layout,
    remove_orphans=True,
    max=args.max
)



#network.write_to("/Users/dexter/" + network.get_name() + ".cx")

