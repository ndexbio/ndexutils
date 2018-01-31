__author__ = 'aarongary'

import unittest
import warnings
import os
import ndextsv.cx2ndex as c2n
import ndextsv.delim2cx as d2c
import json
import ndex.client as nc
import networkx as nx
from ndex.networkn import NdexGraph
import jsonschema
import requests
import ndexebs.ebs2cx as ebs2cx

class ScratchTests(unittest.TestCase):
    #==============================
    # CLUSTER SEARCH TEST
    #==============================
    @unittest.skip("not working using this method")
    def test_source_data(self):
        current_directory = os.path.dirname(os.path.abspath(__file__))

        #plan_filename = os.path.join(current_directory, '../import_plans', 'bindingdb_example_plan.json')
        plan_filename = os.path.join(current_directory, '../import_plans', 'drugbank-target_drugs-plan.json')
        #plan_filename = os.path.join(current_directory, '../import_plans', 'guenole2012-sscore-plan.json')

        print 'loading plan from: ' + plan_filename

        # error thrown if no plan is found
        with open(plan_filename) as json_file:
            import_plan = json.load(json_file)

        # set up the ndextsv -> cx converter
        tsv_converter = d2c.TSV2CXConverter(import_plan)

        #tsv_filename = os.path.join(current_directory, '../import', 'bindingdb_example.txt')
        tsv_filename = os.path.join(current_directory, '../import', 'drugbank-carrier_drugs.txt')
        #tsv_filename = os.path.join(current_directory, '../import', 'Guenole2012.txt')

        print "loading ndextsv from: " + tsv_filename

        cx = tsv_converter.convert_tsv_to_cx(tsv_filename)

        self.assertTrue(True)

    #@unittest.skip("not working using this method")
    def test_fix_backup_cx(self):
        current_directory = os.path.dirname(os.path.abspath(__file__))
        cx_path = os.path.join(current_directory, '..', 'cx_backup')
        cx_files = os.listdir(cx_path)
        upload_to_username = 'nci-pid'
        upload_to_password = 'nci-pid2015'
        upload_to_server = 'http://public.ndexbio.org'

        file_name_uuid = {}
        with open(os.path.join(cx_path, 'processed_cx.txt'), 'r') as file_handler:
            count = 0
            file_name = ''
            file_uuid = ''
            for line in file_handler:
                if count %4 == 0:
                    file_name = line.rstrip('\n')
                elif count %4 == 1:
                    file_uuid = line
                    file_name_uuid[file_name] = file_uuid.rstrip('\n')
                    print file_name + ' ' + file_uuid
                elif count %4 == 3:
                    file_name = ''


                count += 1
            print json.dumps(file_name_uuid)

        for cx_doc in cx_files:
            if os.path.isfile(os.path.join(cx_path, cx_doc)) and cx_doc != '.DS_Store' and cx_doc != 'Archive.zip':
                file_to_fix = os.path.join(cx_path, cx_doc)
                replaceable = file_name_uuid.get(cx_doc.replace('.cx', ''))
                if replaceable is not None:
                    file_raw = open(file_to_fix).read()
                    cx_json = json.loads(file_raw)
                    G = NdexGraph(cx=cx_json)
                    #new_network_id = G.upload_to(upload_to_server, upload_to_username, upload_to_password)
                    new_network_id = G.update_to(replaceable, upload_to_server, upload_to_username, upload_to_password)

                    print replaceable
                else:
                    print '************** Not Found *****************'
                #file = os.path.join(cx_path, cx_doc)


    @unittest.skip("not working using this method")
    def test_check_subnetwork_fix(self):
        #ndg = NdexGraph(server='http://dev.ndexbio.org', username='scratch', password='scratch', uuid='beaa203c-5077-11e7-8f50-06832d634f41')
        #ndg.upload_to(server='http://dev.ndexbio.org', username='scratch', password='scratch')
        #ndg.update_to(uuid='beaa203c-5077-11e7-8f50-06832d634f41', server='http://dev.ndexbio.org', username='scratch', password='scratch')


        ndex_meta_client = nc.Ndex('http://public.ndexbio.org', 'nci-pid', 'nci-pid2015') #ndex_server,'netpathtest','netpathtest') # #
        summaries = ndex_meta_client.search_networks('*', 'nci-pid',0,300)
        edge_types = {}
        count = 1
        for summary in summaries.get('networks'):
            if summary.get('name').upper().startswith('VISUAL'):
                print summary.get('name')
                print summary.get('externalId')
                ndg = NdexGraph(server='http://public.ndexbio.org', username='nci-pid', password='nci-pid2015', uuid=summary.get('externalId'))
                ndg.update_to(uuid=summary.get('externalId'), server='http://public.ndexbio.org', username='nci-pid', password='nci-pid2015')
                print count
                count += 1

        print "Done"

    @unittest.skip("not working using this method")
    def test_get_uniprot_ids(self):
        current_directory = os.path.dirname(os.path.abspath(__file__))
        sif_path = os.path.join(current_directory, '..', 'biopax', 'sif', 'ncipid')
        biopax_files = os.listdir(sif_path)

        uniprots = []
        for sif in biopax_files:
            if os.path.isfile(os.path.join(sif_path, sif)) and sif != '.DS_Store' and sif.upper().startswith('TGF'):

                file = os.path.join(sif_path, sif)
                ebs = ebs2cx.load_ebs_file_to_dict(file)

                if len(ebs.get('node_table')) > 0:
                    network = ebs2cx.ebs_to_network(ebs, name=sif)
                    #for n,d in network.nodes_iter(data=True):
                    #    print n

                    for n,d in network.nodes_iter(data=True):
                    #    if d.get('name') is not None:
                            print d

                    uniprots = [d.get('name') for n,d in network.nodes_iter(data=True) if d.get('name') is not None and d.get('name').upper().startswith('P0')]



                print uniprots

    @unittest.skip("not working using this method")
    def test_neighbor_of(self):
        ndex = nc.Ndex("http://dev.ndexbio.org", "scratch", "scratch")

        response = ndex.get_network_as_cx_stream("cfb93d3e-400f-11e7-96f7-06832d634f41")

        template_cx = response.json()
        G = NdexGraph(template_cx)

        for n,d in G.nodes_iter(data=True):
            if G[n]:
                for k in G[n].keys():
                    key_count = 0
                    all_neighbors = True
                    remove_these_edges = []
                    for kd in G[n][k]:
                        key_count +=1
                        if G[n][k][kd].get('interaction') == 'neighbor-of':
                            remove_these_edges.append(kd)
                        else:
                            all_neighbors = False

                    if len(remove_these_edges) > 0 and key_count > len(remove_these_edges):
                        #print G[n][k][remove_this_edge]
                        for rem_k in remove_these_edges:
                            print G[n][k][rem_k]
                            G.remove_edge_by_id(rem_k)
                    elif all_neighbors:
                        #==============================
                        # If all edges are neighbor-of
                        # allow one and remove the rest
                        #==============================
                        remove_these_edges.pop(0)
                        for rem_k in remove_these_edges:
                            print G[n][k][rem_k]
                            G.remove_edge_by_id(rem_k)


                    #print json.dumps(G[n])

        #for s,t,d in G.edges_iter(data=True):
            #print d
                #print G[n]
        print G


    @unittest.skip("not working using this method")
    def test_import(self):
        current_directory = os.path.dirname(os.path.abspath(__file__))
        username = 'scratch'
        password = 'scratch'
        server = 'dev.ndexbio.org'
        name = 'tsvImport1'
        desc = 'testing ndextsv import'

        tsv = os.path.join(current_directory, '..', 'import', 'bad_signor_all_data_27apr2017-clean.txt')
        plan = os.path.join(current_directory, '..', 'import_plans', 'bad_signor-27apr2017-plan.json')

        try:
            my_ndex = nc.Ndex("http://" + server, username, password)
            print "loading plan from: " + plan

            try :
                import_plan = d2c.TSVLoadingPlan(plan)

            except jsonschema.ValidationError as e1:
                print "Failed to parse the loading plan '" + plan + "': " + e1.message
                print 'at path: ' + str(e1.absolute_path)
                print "in block: "
                print e1.instance
                return

            print "parsing ndextsv file using loading plan ..."
            tsv_converter = d2c.TSV2CXConverter(import_plan)

            ng = tsv_converter.convert_tsv_to_cx(tsv, name=name, description=desc)

            my_ndex.save_cx_stream_as_new_network(ng.to_cx_stream())

            print "Done."

        except jsonschema.exceptions.ValidationError as ve:
            print str(ve)
            exit(1)
        except requests.exceptions.RequestException, e:
            print "error in request to NDEx server: " + str(e)
            raise e

        self.assertTrue(True)
