
import ebs.ebs2cx as ebs2cx
import ndex.client as nc
import ndex.networkn as networkn
from os import getcwd
import json

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
                    help='directory that is the source for EBS files')

parser.add_argument('-t',
                    action='store',
                    dest='template_id',
                    help='network id for the network to use as a graphic template')

parser.add_argument('-g',
                    action='store',
                    dest='group_id',
                    help='the group id to which the uploaded EBS networks should be assigned')

parser.add_argument('-l',
                    action='store',
                    dest='layout',
                    help='the layout algorithm to apply to each EBS file')

parser.add_argument('-f',
                    action='store',
                    dest='filter',
                    help='the filtering algorithm to apply to each EBS file')

parser.add_argument('-m',
                    action='store',
                    dest='max',
                    type=int,
                    help='the maximum number of files to upload - useful for testing')

parser.add_argument('-x',
                    action='store',
                    dest='update',
                    type=bool,
                    help='update existing networks based on name matching')

parser.add_argument('-z',
                    action='store',
                    dest='nci',
                    type=bool,
                    help='take special actions for NCI networks')

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

nci_table = False
if args.nci:
    cwd = getcwd()
    nci_table = ebs2cx.load_nci_table_to_dicts(cwd + "/pid_revised_list-v8-unicode.txt")

id_map = ebs2cx.upload_ebs_files(
    args.directory,
    ndex,
    #group_id=args.group_id,
    template_network=template_network,
    layout=args.layout,
    filter=args.filter,
    max=args.max,
    update=args.update,
    nci_table=nci_table
)

with open(getcwd() + "/nci_ids.json", 'w') as file:
    file.write(json.dumps(id_map, indent=4))

