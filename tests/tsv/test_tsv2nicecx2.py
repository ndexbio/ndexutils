#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `tsv2nicecx2` module."""

import tempfile
import shutil
import os
import io
import unittest
import pandas as pd
import json
from ndexutil.tsv import tsv2nicecx2
from ndexutil.exceptions import NDExUtilError
import ndex2


class Testtsv2nicecx2(unittest.TestCase):
    """
    Tests tsv2nicecx2.py
    """
    def setUp(self):
        """Set up test fixtures, if any."""
        pass

    def tearDown(self):
        """Tear down test fixtures, if any."""
        pass

    def test_context_set_correctly_on_network(self):
        temp_dir = tempfile.mkdtemp()
        try:
            here = os.path.dirname(__file__)
            tsvfile = os.path.join(here, 'ctd_test.tsv')
            loadplanfile = os.path.join(here,
                                        'ctd-gene-disease-2019-norm-'
                                        'plan-collapsed.json')

            with open(loadplanfile, 'r') as f:
                loadplan = json.load(f)

            df = pd.read_csv(tsvfile, sep='\t')
            first = tsv2nicecx2.convert_pandas_to_nice_cx_with_load_plan(df, loadplan,
                                                                         name='mynetwork',
                                                                         description='mydesc')

            nadd = [{'n': 'hi', 'v': 'data'}]
            second = tsv2nicecx2.convert_pandas_to_nice_cx_with_load_plan(df, loadplan,
                                                                          network_attributes=nadd)
            for net in [first, second]:
                res = net.get_network_attribute('@context')
                self.assertEqual('{"ncbigene": "http://ctdbase.org/detail.go'
                                 '?type=gene&acc=", "OMIM": "http://ctdbase.'
                                 'org/detail.go?type=disease&acc=OMIM:", "ME'
                                 'SH": "http://ctdbase.org/detail.go?type=dis'
                                 'ease&acc=MESH:", "pubmed": "http://ctdbase.'
                                 'org/detail.go?type=reference&acc="}', res['v'])
                self.assertEqual(len(net.edges), 49)
                self.assertEqual(len(net.nodes), 50)
                node_attr_cnt = 0
                for key, value in net.nodeAttributes.items():
                    node_attr_cnt += len(value)
                self.assertEqual(node_attr_cnt, 50)
                edge_attr_cnt = 0
                for key, value in net.edgeAttributes.items():
                    edge_attr_cnt += len(value)
                self.assertEqual(edge_attr_cnt, 147)

            self.assertEqual(len(first.networkAttributes), 3)
            self.assertEqual(len(second.networkAttributes), 2)
            self.assertEqual('data', second.get_network_attribute('hi')['v'])

        finally:
            shutil.rmtree(temp_dir)
