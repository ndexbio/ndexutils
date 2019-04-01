#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `streamtsvloader` module."""

import tempfile
import shutil
import os
import io
import unittest
from ndexutil.tsv.streamtsvloader import StreamTSVLoader
from ndexutil.tsv.streamtsvloader import CXStreamWriter
from ndexutil.exceptions import NDExUtilError
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

    def test_write_pre_metadata_none_as_stream(self):
        writer = CXStreamWriter(None)
        try:
            writer.write_pre_metadata({})
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertEqual('Output stream is None', str(ne))

    def test_write_aspect_fragment_called_before_write_premeta(self):
        writer = CXStreamWriter(None)
        try:
            writer.write_aspect_fragment({})
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertTrue('Data aspects can only' in str(ne))

    def test_write_post_metadata_called_before_write_premeta(self):
        writer = CXStreamWriter(None)
        try:
            writer.write_post_metadata({})
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertTrue('Post metadata aspect can only' in str(ne))

    def test_write_pre_metadata_twice(self):
        stream = io.StringIO()
        writer = CXStreamWriter(stream)
        writer.write_pre_metadata({})
        try:
            writer.write_pre_metadata({})
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertTrue('PreMetadata has already' in str(ne))

    def test_write_post_metadata_twice(self):
        stream = io.StringIO()
        writer = CXStreamWriter(stream)
        writer.write_pre_metadata({})
        writer.write_post_metadata({})
        try:
            writer.write_post_metadata({})
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertTrue('Post metadata aspect can only' in str(ne))

    def test_creating_network(self):
        temp_dir = tempfile.mkdtemp()
        try:
            here = os.path.dirname(__file__)
            tsvfile = os.path.join(here, 'ctd_test.tsv')
            with open (tsvfile, 'r') as tsvfile:
                tmpcx = 'out.cx'
                with open(tmpcx, "w") as out:
                    nicecx = ndex2.create_nice_cx_from_file(os.path.join(here, 'gene-disease-style.cx'))
                    loader = StreamTSVLoader(os.path.join(here, 'ctd-gene-disease-2019-norm-plan-collapsed.json'),nicecx)
                    loader.write_cx_network(tsvfile, out, [{'n': 'name', 'v': "CTD: gene-disease association (Human)"},
                                                           {'n': 'version', 'v': "0.0.1"}], batchsize=4)

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

    def test_network_without_represent(self):
        temp_dir = tempfile.mkdtemp()
        try:
            here = os.path.dirname(__file__)
            tsvfile = os.path.join(here, 'BRCA-2012-TP53-pathway.txt_with_a_b.csv')
            with open (tsvfile, 'r') as tsvfile:
                #with open (os.path.join ( temp_dir, "out.cx"),"w") as out:
                tmpcx = 'out.cx'
                with open(tmpcx, "w") as out:
                    loader = StreamTSVLoader(os.path.join(here, 'BRCA-2012-loadplan.json'), None)
                    loader.write_cx_network(tsvfile, out, [{'n': 'name', 'v': "test pathway"},
                                                           {'n':'version', 'v': "0.0.1"}])

                nicecx = ndex2.create_nice_cx_from_file(tmpcx)
                self.assertEqual(len(nicecx.networkAttributes), 3)
                self.assertEqual(len(nicecx.edges), 8)
                self.assertEqual(len(nicecx.nodes), 9)
                self.assertEqual(nicecx.nodes[0].get('r'), None)
                node_attr_cnt = 0
                for key, value in nicecx.nodeAttributes.items():
                    node_attr_cnt += len(value)
                self.assertEqual(node_attr_cnt, 25)

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
