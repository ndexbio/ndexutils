#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ndexutils` script."""

import tempfile
import shutil
import os
import unittest
from ndexutil.tsv.streamtsvloader import StreamTSVLoader
import ndex2



class TeststreamTSVLoader(unittest.TestCase):
    """
    Tests streamtsvloader.py
    """
    def setUp(self):
        """Set up test fixtures, if any."""
        pass

    def tearDown(self):
        """Tear down test fixtures, if any."""
        pass

    def test_parse_arguments(self):
        temp_dir = tempfile.mkdtemp()
        try:
            self.assertEqual(1,1)
            here = os.path.dirname(__file__)
            tsvfile = os.path.join(here, 'ctd_test.tsv')
            with open (tsvfile, 'r') as tsvfile:
                #with open (os.path.join ( temp_dir, "out.cx"),"w") as out:
                tmpcx = 'out.cx'
                with open(tmpcx, "w") as out:
                    nicecx = ndex2.create_nice_cx_from_file(os.path.join(here, 'gene-disease-style.cx'))
                    loader = StreamTSVLoader(os.path.join(here, 'ctd-gene-disease-2019-norm-plan-collapsed.json'),nicecx)
                    loader.write_cx_network(tsvfile, out, [{'n': 'name', 'v': "CTD: gene-disease association (Human)"},
                                                           {'n':'version', 'v': "0.0.1"}], batchsize=4)

                nicecx = ndex2.create_nice_cx_from_file(tmpcx)
                self.assertEqual(len(nicecx.networkAttributes), 3)
                self.assertEqual(len(nicecx.edges), 49)
                self.assertEqual(len(nicecx.nodes), 50)
                node_attr_cnt = 0
                for key, value in nicecx.nodeAttributes.items():
                    node_attr_cnt += len(value)
                self.assertEqual(node_attr_cnt, 50)
                edge_attr_cnt = 0
                for key, value in nicecx.edgeAttributes.items():
                    edge_attr_cnt += len(value)
                self.assertEqual(edge_attr_cnt, 147)
                self.assertEqual(len(nicecx.opaqueAspects.get("cyVisualProperties")), 3)
        finally:
            shutil.rmtree(temp_dir)

 #   def test_parse_arguments(self):
 #           here = os.path.dirname(__file__)
 #           tsvfile = os.path.join("/Users/chenjing/git/ndexctdloader/ndexctdloader", 'collapsed_Homo_sapiens.tsv')
 #           with open(tsvfile, 'r') as tsvfile:
                # with open (os.path.join ( temp_dir, "out.cx"),"w") as out:
 #               with open("/Users/chenjing/Downloads/ctdout.cx", "w") as out:
 #                   nicecx = ndex2.create_nice_cx_from_file(os.path.join(here, 'gene-disease-style.cx'))
 #                   loader = StreamTSVLoader(os.path.join(here, 'ctd-gene-disease-2019-norm-plan-collapsed.json'),
 #                                            nicecx)
 #                   loader.write_cx_network(tsvfile, out, [{'n': 'name', 'v': "CTD: gene-disease association (Homo_Sapiens)"},
 #                                                          {'n': 'version', 'v': "0.0.1"}], batchsize=5000)
