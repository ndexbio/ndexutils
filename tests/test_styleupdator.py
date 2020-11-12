#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ndexmisctools` module."""

import tempfile
import shutil
import os
import json
import unittest
from unittest.mock import MagicMock

import ndex2
from ndex2.nice_cx_network import NiceCXNetwork
from ndexutil.exceptions import ConfigError
from ndexutil.exceptions import NDExUtilError
from ndexutil.ndexmisctools import StyleUpdator
from ndexutil.config import NDExUtilConfig


class TestStyleUpdator(unittest.TestCase):
    """
        Tests StyleUpdate in ndexmisctools module
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
            remover = StyleUpdator(p)
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
            p.profile = 'foo'
            loader = StyleUpdator(p)
            loader._parse_config()
            self.assertEqual('theuser', loader._user)
            self.assertEqual('thepass', loader._pass)
            self.assertEqual('theserver', loader._server)
        finally:
            shutil.rmtree(temp_dir)

    def test_get_client_with_alt_set(self):
        p = MagicMock()
        adder = StyleUpdator(p, altclient='foo')
        self.assertEqual('foo', adder._get_client())

    def test_get_style_function_with_style_file(self):
        temp_dir = tempfile.mkdtemp()
        try:
            p = MagicMock()
            p.stylefile = os.path.join(temp_dir, 'foo.cx')
            p.newcopy = False
            net = NiceCXNetwork()
            net.set_name('foo')
            with open(p.stylefile, 'w') as f:
                json.dump(net.to_cx(), f)

            loader = StyleUpdator(p)
            loader._get_style_function_to_use()
            self.assertEqual('foo', loader._style.get_name())
            sf = loader._get_style_function_to_use()
            self.assertEqual(type(loader._apply_style_from_file_to_new_network),
                             type(sf))
            self.assertTrue('_apply_style_from_file_'
                            'to_original_network' in str(sf))

            # try with copy
            loader._args.newcopy = True
            loader._get_style_function_to_use()
            self.assertEqual('foo', loader._style.get_name())
            sf = loader._get_style_function_to_use()
            self.assertEqual(type(loader._apply_style_from_file_to_new_network),
                             type(sf))
            self.assertTrue('_apply_style_from_file_to_new_network' in str(sf))

        finally:
            shutil.rmtree(temp_dir)

    def test_get_style_function_with_no_style_file(self):
        p = MagicMock()
        p.stylefile = None
        p.newcopy = False

        loader = StyleUpdator(p)
        loader._get_style_function_to_use()
        sf = loader._get_style_function_to_use()
        self.assertEqual(type(loader._apply_style_from_file_to_new_network),
                         type(sf))
        self.assertTrue('_apply_style_from_uuid_to_original_network' in str(sf))

        # try with copy
        loader._args.newcopy = True
        loader._get_style_function_to_use()
        sf = loader._get_style_function_to_use()
        self.assertEqual(type(loader._apply_style_from_file_to_new_network),
                         type(sf))
        self.assertTrue('_apply_style_from_uuid_to_new_network' in str(sf))





