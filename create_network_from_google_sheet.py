__author__ = 'dexter'

import tsv.delim2cx as d2c
import ndex.client as nc
import ndex.beta.layouts as layouts
import ndex.beta.toolbox as toolbox
import ndex.networkn as networkn
import requests
import jsonschema
import gspread
from oauth2client.service_account import ServiceAccountCredentials

import argparse, sys


def main():
    parser = argparse.ArgumentParser(description='create NDEx network from google sheet, one edge per line')

    parser.add_argument('username' )
    parser.add_argument('password')
    parser.add_argument('server')
    parser.add_argument('google_sheet_url')
    parser.add_argument('plan')
    parser.add_argument('name')
    parser.add_argument('desc')
    parser.add_argument('template')

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

        print("authorizing")
        scope = ['https://spreadsheets.google.com/feeds']

        credentials = ServiceAccountCredentials.from_json_keyfile_name('/Users/dexter/ndexaccess-c27e6047fc32.json', scope)
        gc = gspread.authorize(credentials)

        print("getting spreadsheet")
        spreadsheet = gc.open_by_url(arg.google_sheet_url)
        worksheet = spreadsheet.sheet1


        #  set up the tsv -> cx converter

        print ("creating converter with loading plan ...")
        tsv_converter = d2c.TSV2CXConverter(import_plan)

        print ("parsing worksheet")
        ng = tsv_converter.convert_google_worksheet_to_cx(worksheet, name=arg.name, description = arg.desc)

        if arg.template:
            print("Applying graphic style from template network with id = : " + str(arg.template))
            response = my_ndex.get_network_as_cx_stream(arg.template)
            template_cx = response.json()
            template_network = networkn.NdexGraph(cx=template_cx)
            print("template = " + template_network.name)
            toolbox.apply_network_as_template(ng, template_network)

            # apply graphic style


        #print("applying layout")
        #layouts.apply_directed_flow_layout(ng, directed_edge_types=['Links To'])

        print ("saving to NDEx ...")
        my_ndex.save_cx_stream_as_new_network(ng.to_cx_stream())

        print("Done.")

    except jsonschema.exceptions.ValidationError as ve:
        print str(ve)
        exit(1)
    except requests.exceptions.RequestException, e:
        print "error in request to NDEx server: " + str(e)
        raise e
#    except Exception, e:
#        print "Other Error: " + str(e)
#        raise e


if __name__ == '__main__':
    main()








