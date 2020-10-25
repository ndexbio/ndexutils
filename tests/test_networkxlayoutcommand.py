#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ndex` module."""

import tempfile
import shutil
import os
import unittest
from unittest.mock import call, MagicMock


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