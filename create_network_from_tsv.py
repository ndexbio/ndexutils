__author__ = 'dexter'

import tsv.delim2cx as d2c
import ndex.client as nc
import requests
import os
import io
import jsonschema


import argparse, sys


def main():
    parser = argparse.ArgumentParser(description='create NDEx network from TSV, one edge per line')

    parser.add_argument('username' )
    parser.add_argument('password')
    parser.add_argument('server')
    parser.add_argument('tsv')
    parser.add_argument('plan')
    parser.add_argument('name')
    parser.add_argument('desc')

    arg = parser.parse_args()

    try:
        # set up the ndex connection
        # error thrown if cannot authenticate
        my_ndex = nc.Ndex("http://" + arg.server, arg.username, arg.password)

#        current_directory = os.path.dirname(os.path.abspath(__file__))

 #       plan_filename = os.path.join(current_directory, "import_plans", arg.plan)

        print "loading plan from: " + arg.plan

        try :
            import_plan = d2c.TSVLoadingPlan(arg.plan)

        except jsonschema.ValidationError as e1:
            print "Failed to parse the loading plan '" + arg.plan + "': " + e1.message
            print 'at path: ' + str(e1.absolute_path)
            print "in block: "
            print e1.instance
            return

        # set up the tsv -> cx converter

        print "parsing tsv file using loading plan ..."
        tsv_converter = d2c.TSV2CXConverter(import_plan)

        ng = tsv_converter.convert_tsv_to_cx(arg.tsv, name=arg.name, description = arg.desc)

        #print json.dumps(cx, indent=4)

        #response_json =
        my_ndex.save_cx_stream_as_new_network(ng.to_cx_stream())

        print "Done."

    except jsonschema.exceptions.ValidationError as ve:
        print str(ve)
        exit(1)
    except requests.exceptions.RequestException, e:
        print "error in request to NDEx server: " + str(e)
        raise e


if __name__ == '__main__':
    main()








