#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ndex` module."""

import tempfile
import shutil
import os
import json
import unittest
from unittest.mock import call, MagicMock

from ndex2.nice_cx_network import NiceCXNetwork
from ndexutil.networkx import NetworkxLayoutCommand
from ndexutil.config import NDExUtilConfig
from ndexutil.exceptions import ConfigError
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

    def get_dummy_configfile(self, temp_dir):
        """
        Given a base temp directory create a config file
        :param temp_dir:
        :return: full path to the config file
        """
        cfile = os.path.join(temp_dir, 'configfile')
        with open(cfile, 'w') as f:
            f.write('[foo]\n')
            f.write(NDExUtilConfig.USER + ' = theuser\n')
            f.write(NDExUtilConfig.PASSWORD + ' = thepass\n')
            f.write(NDExUtilConfig.SERVER + ' = theserver\n')
        return cfile

    def test_parse_config_no_configfile(self):
        temp_dir = tempfile.mkdtemp()
        try:
            p = MagicMock()
            p.username = 'bob'
            p.password = '-'
            p.server = 'public.ndexbio.org'
            p.conf = temp_dir
            remover = NetworkxLayoutCommand(p)
            remover._parse_config()
            self.fail('Expected ConfigError')
        except ConfigError as e:
            self.assertEqual('No configuration file found', str(e))
        finally:
            shutil.rmtree(temp_dir)

    def test_parse_config_valid_configfile(self):
        temp_dir = tempfile.mkdtemp()
        try:
            cfile = self.get_dummy_configfile(temp_dir)

            # try with username set to - to load it from config
            p = MagicMock()
            p.conf = cfile
            p.username = '-'
            p.password = '-'
            p.server = '-'
            p.profile = 'foo'
            loader = NetworkxLayoutCommand(p)
            loader._parse_config()
            self.assertEqual('theuser', loader._user)
            self.assertEqual('thepass', loader._pass)
            self.assertEqual('theserver', loader._server)
        finally:
            shutil.rmtree(temp_dir)

    def test_parse_config_all_set_via_cmdline(self):
        temp_dir = tempfile.mkdtemp()
        try:
            cfile = self.get_dummy_configfile(temp_dir)

            # try with username set to - to load it from config
            p = MagicMock()
            p.conf = cfile
            p.username = 'u'
            p.password = 'p'
            p.server = 's'
            loader = NetworkxLayoutCommand(p)
            loader._parse_config()
            self.assertEqual('u', loader._user)
            self.assertEqual('p', loader._pass)
            self.assertEqual('s', loader._server)
        finally:
            shutil.rmtree(temp_dir)

    def test_add_subparsers(self):
        mock_sub = MagicMock()
        mock_parse = MagicMock()
        mock_sub.add_parser = MagicMock(return_value=mock_parse)
        NetworkxLayoutCommand.add_subparser(mock_sub)

        mock_parse.add_argument.assert_has_calls([call('layout',
                                                       choices=['spring'],
                                                       help='Name of layout to run.')],
                                                       any_order=True)

    def test_get_center_as_list(self):
        p = MagicMock()
        p.username = 'u'
        p.password = 'p'
        p.server = 's'
        p.center = None

        cmd = NetworkxLayoutCommand(p)
        self.assertEquals(None, cmd.get_center_as_list())

        p.center = '123'
        try:
            cmd.get_center_as_list()
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertTrue(str(ne).startswith('Expecting single comma'))

        p.center = '4,5'
        self.assertEquals([4, 5], cmd.get_center_as_list())

        p.center = 'x,23'
        try:
            cmd.get_center_as_list()
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertTrue(str(ne).startswith('Value passed to --center'))

        p.center = ',10'
        try:
            cmd.get_center_as_list()
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertTrue(str(ne).startswith('Value passed to --center'))

        p.center = ',10,12'
        try:
            cmd.get_center_as_list()
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertTrue(str(ne).startswith('Expecting single comma'))

    def test_run_layout_algorithm_invalid_layout(self):
        p = MagicMock()
        p.username = 'u'
        p.password = 'p'
        p.server = 's'
        p.layout = 'nope'
        p.center = None
        cmd = NetworkxLayoutCommand(p)
        try:
            cmd._run_layout_algorithm(netx_graph='graph')
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertEqual('nope does not match supported layout', str(ne))

    def test_run_layout_algorithm(self):
        p = MagicMock()
        p.username = 'u'
        p.password = 'p'
        p.server = 's'
        p.center = None
        p.layout = 'spring'
        p.spring_k = 1.0
        p.spring_iterations = 50
        p.scale = 300.0

        layout = MagicMock()
        layout.spring_layout = MagicMock(return_value='result')

        cmd = NetworkxLayoutCommand(p,
                                    layout_wrapper=layout)
        res = cmd._run_layout_algorithm(netx_graph='graph')
        self.assertEqual('result', res)
        layout.spring_layout.assert_called_with('graph',
                                                k=1.0,
                                                iterations=50,
                                                center=None,
                                                scale=300.0)

    def test_apply_layout(self):
        p = MagicMock()
        p.username = 'u'
        p.password = 'p'
        p.server = 's'
        p.center = '3,2'
        p.layout = 'spring'
        p.spring_k = 1.0
        p.spring_iterations = 2
        p.scale = 300.0
        p.outputcx = None

        temp_dir = tempfile.mkdtemp()
        try:
            cxfile = os.path.join(temp_dir, 'input.cx')
            net = NiceCXNetwork()
            node_one = net.create_node('node1', 'rep1')
            node_two = net.create_node('node2', 'rep2')
            net.create_edge(node_one, node_two, 'links')
            with open(cxfile, 'w') as f:
                json.dump(net.to_cx(), f)
            cmd = NetworkxLayoutCommand(p)
            cmd._tmpdir = temp_dir
            c_a, outfile = cmd.apply_layout(cxfile=cxfile)
            self.assertTrue(os.path.isfile(outfile))
            self.assertEqual(2, len(c_a))
        finally:
            shutil.rmtree(temp_dir)

    def test_apply_layout_outputcx_set(self):
        temp_dir = tempfile.mkdtemp()
        p = MagicMock()
        p.username = 'u'
        p.password = 'p'
        p.server = 's'
        p.center = None
        p.layout = 'spring'
        p.spring_k = 1.0
        p.spring_iterations = 2
        p.scale = 300.0
        ocx = os.path.join(temp_dir, 'out.cx')
        p.outputcx = ocx

        try:
            cxfile = os.path.join(temp_dir, 'input.cx')
            net = NiceCXNetwork()
            node_one = net.create_node('node1', 'rep1')
            node_two = net.create_node('node2', 'rep2')
            net.create_edge(node_one, node_two, 'links')
            with open(cxfile, 'w') as f:
                json.dump(net.to_cx(), f)
            cmd = NetworkxLayoutCommand(p)
            cmd._tmpdir = temp_dir
            c_a, outfile = cmd.apply_layout(cxfile=cxfile)
            self.assertEqual(ocx, outfile)
            self.assertTrue(os.path.isfile(outfile))
            self.assertEqual(2, len(c_a))
        finally:
            shutil.rmtree(temp_dir)

    def test_run(self):
        temp_dir = tempfile.mkdtemp()
        p = MagicMock()
        p.tmpdir = None
        p.username = 'u'
        p.password = 'p'
        p.server = 's'
        p.center = None
        p.layout = 'spring'
        p.spring_k = 1.0
        p.spring_iterations = 2
        p.scale = 300.0
        p.uuid = 'uuid'
        p.skipupload = False
        p.updatefullnetwork = False

        mockextra = MagicMock()
        mocklayout = MagicMock()
        mockclient = MagicMock()
        cmd = NetworkxLayoutCommand(p, ndexextra=mockextra,
                                    layout_wrapper=mocklayout,
                                    altclient=mockclient)

        try:
            cmd.run()
            self.fail('Expected exception')
        except Exception as e:
            pass
