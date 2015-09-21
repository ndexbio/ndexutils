__author__ = 'dexter'

import tsv.cx2ndex as c2n
import tsv.delim2cx as d2c
import json
import ndex.client as nc
import requests
import os

# body

# this utility currently uses an early prototype cx as an intermediate form for a network
# parsed from a tsv file in which each row corresponds to an edge

# later it will be converted to use the real cx API

import argparse, sys

parser = argparse.ArgumentParser(description='create NDEx network from TSV, one edge per line')

parser.add_argument('username', action='store')
parser.add_argument('password', action='store')
parser.add_argument('server', action='store')
parser.add_argument('tsv', action='store')
parser.add_argument('plan', action='store')
parser.add_argument('name', action='store')
parser.add_argument('desc', action='store')

arg = parser.parse_args()

try:
    current_directory = os.path.dirname(os.path.abspath(__file__))

    plan_filename = os.path.join(current_directory, "import_plans", arg.plan)

    print "loading plan from: " + plan_filename

    with open(plan_filename) as json_file:
        import_plan = json.load(json_file)

    # set up the tsv -> cx converter
    tsv_converter = d2c.TSV2CXConverter(import_plan)

    tsv_filename = os.path.join(current_directory, "import", arg.tsv)

    print "loading tsv from: " + tsv_filename

    # (prototype) cx from tsv
    # this is NOT the standard CX under development as of september 2015
    cx_network = tsv_converter.convert_tsv(tsv_filename, 3)

    # set up the cx -> ndex converter
    c2n_converter = c2n.Cx2NdexConverter(cx_network)

    # ndex json object converted from prototype cx
    ndex_network = c2n_converter.convertToNdex()

    # add a name and description
    ndex_network['name'] = arg.name
    ndex_network['description'] = arg.desc

    # set up the ndex connection
    my_ndex = nc.Ndex("http://" + arg.server, arg.username, arg.password)

    # save the network
    response_json = my_ndex.save_new_network(ndex_network)

except requests.exceptions.RequestException, e:
    print "error in request to NDEx server: " + str(e)









