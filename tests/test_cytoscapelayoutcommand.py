#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ndex` module."""

import tempfile
import shutil
import os
import unittest
import json
from unittest.mock import MagicMock, call
from unittest import mock
import requests
import requests_mock

from ndexutil.config import NDExUtilConfig
from ndexutil.config import ConfigError
from ndexutil.cytoscape import CytoscapeLayoutCommand


class TestCytoscapeLayoutCommand(unittest.TestCase):
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
            remover = CytoscapeLayoutCommand(p)
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
            loader = CytoscapeLayoutCommand(p)
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
            loader = CytoscapeLayoutCommand(p)
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
        CytoscapeLayoutCommand.add_subparser(mock_sub)

        mock_parse.add_argument.assert_has_calls([call('layout',
                                                       help='Name of layout '
                                                            'to run. Set '
                                                            'layout name '
                                                            'to listlayout '
                                                            'to see all '
                                                            'options. If set '
                                                            'to - default '
                                                            'layout of '
                                                            'force-'
                                                            'directed-cl '
                                                            'will be used')],
                                                       any_order=True)

    def test_get_supported_layouts_ping_raises_exception(self):
        mockwrapper = MagicMock()
        mockwrapper.cytoscape_ping = MagicMock(side_effect=Exception('error'))

        res = CytoscapeLayoutCommand.get_supported_layouts(py4_wrapper=mockwrapper)
        self.assertEqual('\nA running Cytoscape was not found at: '
                         'http://localhost:1234/v1 Please start '
                         'Cytoscape or check value of --cyresturl '
                         ': error\n', res)

    def test_get_cytoscape_check_message_py4_not_loaded(self):
        mockwrapper = MagicMock()
        mockwrapper.is_py4cytoscape_loaded = MagicMock(return_value=False)
        res = CytoscapeLayoutCommand.get_cytoscape_check_message(py4_wrapper=mockwrapper)
        self.assertEqual('\nERROR: It appears py4cytoscape is NOT installed '
                         'to use this tool run pip install py4cytoscape and '
                         'run this tool again.\n', res)

    def test_get_cytoscape_check_message_cytoscape_not_running(self):
        mockwrapper = MagicMock()
        mockwrapper.cytoscape_ping = MagicMock(side_effect=Exception('error'))

        res = CytoscapeLayoutCommand.get_cytoscape_check_message(py4_wrapper=mockwrapper)
        self.assertTrue(res.startswith('\nWARNING: A locally running'))

    def test_get_supported_layouts_raises_exception(self):
        mockwrapper = MagicMock()
        mockwrapper.cytoscape_ping = MagicMock(return_value=None)

        mockwrapper.get_layout_name_mapping = MagicMock(side_effect=Exception('error2'))
        res = CytoscapeLayoutCommand.get_supported_layouts(py4_wrapper=mockwrapper)
        self.assertEqual('\nUnable to get list of layouts\n', res)

    def test_get_supported_layouts_none_for_layouts(self):
        mockwrapper = MagicMock()
        mockwrapper.cytoscape_ping = MagicMock(return_value=None)

        mockwrapper.get_layout_name_mapping = MagicMock(return_value=None)
        res = CytoscapeLayoutCommand.get_supported_layouts(py4_wrapper=mockwrapper)
        self.assertEqual('\nNo layouts found\n', res)

    def test_get_supported_layouts_empty_layouts(self):
        mockwrapper = MagicMock()
        mockwrapper.cytoscape_ping = MagicMock(return_value=None)
        mockwrapper.get_layout_name_mapping = MagicMock(return_value={})
        res = CytoscapeLayoutCommand.get_supported_layouts(py4_wrapper=mockwrapper)
        self.assertEqual('\nNo layouts found\n', res)

    def test_get_supported_layouts_success(self):
        mockwrapper = MagicMock()
        mockwrapper.cytoscape_ping = MagicMock(return_value=None)
        mockwrapper.get_layout_name_mapping = MagicMock(return_value={'key': 'value'})
        res = CytoscapeLayoutCommand.get_supported_layouts(py4_wrapper=mockwrapper)
        self.assertEqual('\nLayout Name\n\t-- Layout Name as seen in Cytoscape'
                         '\n\nvalue\n\t-- key\n\n\n', res)

