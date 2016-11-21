__author__ = 'aarongary'

import unittest
import warnings
import os
import tsv.cx2ndex as c2n
import tsv.delim2cx as d2c
import json
import ndex.client as nc
import networkx as nx
from ndex.networkn import NdexGraph

class ScratchTests(unittest.TestCase):
    #==============================
    # CLUSTER SEARCH TEST
    #==============================
    def test_source_data(self):
        current_directory = os.path.dirname(os.path.abspath(__file__))

        #plan_filename = os.path.join(current_directory, '../import_plans', 'bindingdb_example_plan.json')
        plan_filename = os.path.join(current_directory, '../import_plans', 'drugbank-target_drugs-plan.json')
        #plan_filename = os.path.join(current_directory, '../import_plans', 'guenole2012-sscore-plan.json')

        print 'loading plan from: ' + plan_filename

        # error thrown if no plan is found
        with open(plan_filename) as json_file:
            import_plan = json.load(json_file)

        # set up the tsv -> cx converter
        tsv_converter = d2c.TSV2CXConverter(import_plan)

        #tsv_filename = os.path.join(current_directory, '../import', 'bindingdb_example.txt')
        tsv_filename = os.path.join(current_directory, '../import', 'drugbank-carrier_drugs.txt')
        #tsv_filename = os.path.join(current_directory, '../import', 'Guenole2012.txt')

        print "loading tsv from: " + tsv_filename

        cx = tsv_converter.convert_tsv_to_cx_using_networkn(tsv_filename)


        self.assertTrue(True)
