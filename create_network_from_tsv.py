__author__ = 'dexter'

import tsv.delim2cx as d2c
import ndex.client as nc
import ndex.beta.toolbox as toolbox
import ndex.beta.layouts as layouts
import ndex.networkn as networkn
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
    parser.add_argument('-t',
                    action='store',
                    dest='template_id',
                    help='network id for the network to use as a graphic template')
    parser.add_argument('-l',
                    action='store',
                    dest='layout',
                    help='name of the layout to apply')
    parser.add_argument('-u',
                    action='store',
                    dest='update_uuid',
                    help='uuid of the network to update')

#    parser.add_argument('update_username' )
#    parser.add_argument('update_password')
#    parser.add_argument('update_server')

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



        #print json.dumps(cx, indent=4)
        template_network = None
        if arg.template_id:
            response = my_ndex.get_network_as_cx_stream(arg.template_id)
            template_cx = response.json()
            template_network = networkn.NdexGraph(template_cx)

        # If update_uuid is set, then we get the existing network's attributes and provenance
        if arg.update_uuid:
            response = my_ndex.get_network_aspect_as_cx_stream(arg.update_uuid, "networkAttributes")
            network_attributes = response.json()
            provenance = my_ndex.get_provenance(arg.update_uuid)
            ng = tsv_converter.convert_tsv_to_cx(arg.tsv, network_attributes=network_attributes, provenance=provenance)
            if template_network:
                toolbox.apply_network_as_template(ng, template_network)
            else:
                response = my_ndex.get_network_aspect_as_cx_stream(arg.update_uuid, "cyVisualProperties")
                visual_properties = response.json()
                if len(visual_properties) > 0:
                    ng.unclassified_cx.append({"cyVisualProperties": visual_properties})
            if arg.layout:
                if arg.layout == "df_simple":
                    layouts.apply_directed_flow_layout(ng)

            my_ndex.update_cx_network(ng.to_cx_stream(), arg.update_uuid)
        else:
            ng = tsv_converter.convert_tsv_to_cx(arg.tsv, name=arg.name, description = arg.desc)
            if template_network:
                toolbox.apply_network_as_template(ng, template_network)
            if arg.layout:
                if arg.layout == "df_simple":
                    layouts.apply_directed_flow_layout(ng)
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








