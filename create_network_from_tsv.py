__author__ = 'dexter'

import tsv.delim2cx as d2c
import json
import ndex.client as nc
import requests
import os
import io

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
    # set up the ndex connection
    # error thrown if cannot authenticate
    my_ndex = nc.Ndex("http://" + arg.server, arg.username, arg.password)

    current_directory = os.path.dirname(os.path.abspath(__file__))

    plan_filename = os.path.join(current_directory, "import_plans", arg.plan)

    print "loading plan from: " + plan_filename

    # error thrown if no plan is found
    with open(plan_filename) as json_file:
        import_plan = json.load(json_file)

    # set up the tsv -> cx converter
    tsv_converter = d2c.TSV2CXConverter(import_plan)

    tsv_filename = os.path.join(current_directory, "import", arg.tsv)

    print "loading tsv from: " + tsv_filename

    cx = tsv_converter.convert_tsv_to_cx(tsv_filename, name=arg.name)

    #print json.dumps(cx, indent=4)

    response_json = my_ndex.save_new_network(cx)


except requests.exceptions.RequestException, e:
    print "error in request to NDEx server: " + str(e)
    raise e











