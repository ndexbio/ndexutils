#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ndex` module."""

import tempfile
import shutil
import os
import json
import unittest
from unittest.mock import MagicMock
import ndex2
from ndex2.nice_cx_network import NiceCXNetwork
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

        try:
            wrapper.spring_layout(None)
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertEqual('Graph passed in is None', str(ne))

        g = networkx.path_graph(3)
        pos = wrapper.spring_layout(g)
        res = wrapper.convert_positions_to_cartesian_aspect(networkx_pos=pos)
        self.assertEqual(3, len(res))

    def test_get_center_as_list(self):
        wrapper = NetworkxLayoutWrapper()
        self.assertEquals(None, wrapper.get_center_as_list())


        try:
            wrapper.get_center_as_list('123')
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertTrue(str(ne).startswith('Expecting single comma'))

        self.assertEquals([4, 5], wrapper.get_center_as_list('4,5'))

        try:
            wrapper.get_center_as_list('x,23')
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertTrue(str(ne).startswith('Value passed in'))

        try:
            wrapper.get_center_as_list(',10')
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertTrue(str(ne).startswith('Value passed in'))

        try:
            wrapper.get_center_as_list(',10,12')
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertTrue(str(ne).startswith('Expecting single comma'))

    def test_run_layout_algorithm_invalid_layouts(self):
        wrapper = NetworkxLayoutWrapper()
        try:
            wrapper.run_layout_algorithm()
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertEqual('Layout cannot be None', str(ne))

        g = networkx.path_graph(3)
        try:
            wrapper.run_layout_algorithm(layout='foo',
                                         netx_graph=g)
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertEqual('foo does not match supported layout',
                             str(ne))

    def test_run_layout_algorithm_spring(self):
        wrapper = NetworkxLayoutWrapper()
        g = networkx.path_graph(3)

        # try with defaults
        wrapper.spring_layout = MagicMock(return_value='hi')
        pos = wrapper.run_layout_algorithm(layout='spring', netx_graph=g)
        self.assertEqual('hi', pos)
        # check we are passing values right
        wrapper.spring_layout.assert_called_with(g,
                                                 k=None, iterations=50,
                                                 center=None, scale=None)

        wrapper.spring_layout = MagicMock(return_value='hi')
        # try with paraemters set and empty arg_dict
        pos = wrapper.run_layout_algorithm(layout='spring', netx_graph=g,
                                           center='10,20', scale=300.0,
                                           arg_dict={})
        self.assertEqual('hi', pos)
        # check we are passing values right
        wrapper.spring_layout.assert_called_with(g,
                                                 k=None, iterations=50,
                                                 center=[10.0, 20.0], scale=300.0)

        wrapper.spring_layout = MagicMock(return_value='hi')
        # try with parameters set and set arg_dict
        pos = wrapper.run_layout_algorithm(layout='spring', netx_graph=g,
                                           center='10,20', scale=300.0,
                                           arg_dict={'spring_k': 0.1,
                                                     'spring_iterations': 2})
        self.assertEqual('hi', pos)
        # check we are passing values right
        wrapper.spring_layout.assert_called_with(g,
                                                 k=0.1, iterations=2,
                                                 center=[10.0, 20.0], scale=300.0)

    def test_apply_layout_invalid_layout(self):

        wrapper = NetworkxLayoutWrapper()
        try:
            wrapper.apply_layout(input_cx_file='input',
                                 output_cx_file='output')
        except NDExUtilError as ne:
            self.assertEqual('Layout cannot be None', str(ne))

    def test_apply_layout(self):
        temp_dir = tempfile.mkdtemp()
        try:
            net = NiceCXNetwork()
            node_one = net.create_node('node1')
            node_two = net.create_node('node2')
            net.create_edge(node_one, node_two)
            cxfile = os.path.join(temp_dir, 'input.cx')
            cxout = os.path.join(temp_dir, 'res.cx')
            with open(cxfile, 'w') as f:
                json.dump(net.to_cx(), f)
            wrapper = NetworkxLayoutWrapper()
            cart_asp, outfile = wrapper.apply_layout(input_cx_file=cxfile,
                                                     output_cx_file=cxout,
                                                     layout='spring', scale=300.0,
                                                     center='10,15',
                                                     arg_dict={'spring_k': 0.1,
                                                     'spring_iterations': 2})

            self.assertEqual(cxout, outfile)
            self.assertEqual(2, len(cart_asp))
            resnet = ndex2.create_nice_cx_from_file(cxout)
            self.assertEqual(resnet.get_opaque_aspect('cartesianLayout'),
                             cart_asp)
        finally:
            shutil.rmtree(temp_dir)

