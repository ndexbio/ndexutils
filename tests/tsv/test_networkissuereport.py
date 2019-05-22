#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `NetworkIssueReport` class."""

import os
import tempfile
import shutil

import unittest
from ndexutil.tsv.loaderutils import NetworkIssueReport


class TestNetworkIssueReport(unittest.TestCase):
    """Tests for `NetworkIssueReport` class."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_get_fullreport_as_string(self):
        report = NetworkIssueReport(None)
        # empty network
        self.assertEqual('', report.get_fullreport_as_string())

        # add none for issue list
        report.addissues('description', None)
        self.assertEqual('', report.get_fullreport_as_string())

        # add none for description
        report.addissues(None, ['hi'])
        self.assertEqual('', report.get_fullreport_as_string())

        # empty issue list
        report.addissues('description', [])
        self.assertEqual('', report.get_fullreport_as_string())

        # valid issues added
        report.addissues('description', ['hi'])
        self.assertEqual('None\n\t1 issue -- description\n\t\thi\n',
                         report.get_fullreport_as_string())

        report = NetworkIssueReport('network')
        report.addissues('blah blah', ['yo', 'there'])
        self.assertEqual('network\n\t2 issues -- blah blah\n'
                         '\t\tyo\n\t\tthere\n',
                         report.get_fullreport_as_string())

    def test_get_nodetypes(self):
        report = NetworkIssueReport(None)
        self.assertEqual(set(), report.get_nodetypes())
        report.add_nodetype(None)
        self.assertEqual(set(), report.get_nodetypes())

        report.add_nodetype('hi')

        self.assertTrue('hi' in report.get_nodetypes())

        report.add_nodetype('hi')
        report.add_nodetype('bye')
        self.assertEqual(2, len(report.get_nodetypes()))
        self.assertTrue('hi' in report.get_nodetypes())
        self.assertTrue('bye' in report.get_nodetypes())
