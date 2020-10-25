#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ndex` module."""

import tempfile
import shutil
import os
import unittest
from unittest.mock import MagicMock
import requests
import requests_mock
import networkx
from ndexutil.networkx import NetworkxLayoutWrapper
from ndexutil.exceptions import NDExUtilError


class TestNetworkxLayoutWrapper(unittest.TestCase):
    """
        Tests NDExExtraUtils in ndex module
    """
    def setUp(self):
        """Set up test fixtures, if any."""
        pass

    def tearDown(self):
        """Tear down test fixtures, if any."""
        pass

    def test_convert_positions_to_cartesian_aspect_invalid_args(self):
        wrapper = NetworkxLayoutWrapper()
        try:
            wrapper.convert_positions_to_cartesian_aspect()
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertEqual('networkx_pos is None', str(ne))

    def test_convert_positions_to_cartesian_aspect(self):
        wrapper = NetworkxLayoutWrapper()
        pos = {0: [4, 5],
               1: [6, 7]}
        res = wrapper.convert_positions_to_cartesian_aspect(networkx_pos=pos)
        self.assertEqual(0, res[0]['node'])
        self.assertEqual(4, res[0]['x'])
        self.assertEqual(5, res[0]['y'])
        self.assertEqual(1, res[1]['node'])
        self.assertEqual(6, res[1]['x'])
        self.assertEqual(7, res[1]['y'])

    def test_springlayout(self):
        wrapper = NetworkxLayoutWrapper()
        g = networkx.path_graph(3)
        pos = wrapper.spring_layout(g)
        res = wrapper.convert_positions_to_cartesian_aspect(networkx_pos=pos)
        self.assertEqual(3, len(res))

