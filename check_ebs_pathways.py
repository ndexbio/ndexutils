
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

# parser.add_argument('-p',
#                     dest='password',
#                     action='store',
#                     help='password for the target NDEx account')

parser.add_argument('-d',
                    action='store',
                    default='$wd$',
                    dest='directory',
                    help='directory that is the source for EBS files')

args = parser.parse_args()

ndex = nc.Ndex(args.server)

nci_table = ebs2cx.load_nci_table_to_dicts(getcwd() + "/pid_revised_list-v8-unicode.txt")

ebs2cx.check_upload_account(
    args.username,
    ndex,
    args.directory,
    nci_table=nci_table
)


