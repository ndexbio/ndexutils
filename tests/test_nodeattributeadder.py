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
from ndexutil.ndexmisctools import NodeAttributeAdder
from ndexutil.config import NDExUtilConfig


class Params(object):
    pass


class TestNodeAttributeAdder(unittest.TestCase):
    """
        Tests NodeAttributeAdder in ndexmisctools module
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
            remover = NodeAttributeAdder(p)
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
            loader = NodeAttributeAdder(p)
            loader._parse_config()
            self.assertEqual('theuser', loader._user)
            self.assertEqual('thepass', loader._pass)
            self.assertEqual('theserver', loader._server)
        finally:
            shutil.rmtree(temp_dir)

    def test_get_nodes_to_skip(self):
        p = MagicMock()

        # try with nodestoinclude set to None
        p.nodestoskip = None
        adder = NodeAttributeAdder(p)
        self.assertEqual([], adder._get_nodes_to_skip())

        # try with one element
        p.nodestoskip = '12'
        adder = NodeAttributeAdder(p)
        self.assertEqual([12], adder._get_nodes_to_skip())

        # try with two elements
        p.nodestoskip = '10,11'
        adder = NodeAttributeAdder(p)
        self.assertEqual([10, 11], adder._get_nodes_to_skip())

        # try with non numeric element
        p.nodestoskip = '10,11,x'
        adder = NodeAttributeAdder(p)
        try:
            adder._get_nodes_to_skip()
            self.fail('Expected NdexUtilError')
        except NDExUtilError as ne:
            self.assertEqual('Non numeric node id in '
                             '--nodestoskip parameter: x',
                             str(ne))

    def test_get_client_with_alt_set(self):
        p = MagicMock()
        adder = NodeAttributeAdder(p, altclient='foo')
        self.assertEqual('foo', adder._get_client())

    def test_run_success(self):
        temp_dir = tempfile.mkdtemp()
        try:
            p = MagicMock()
            p.nodestoskip = None
            p.profile = 'foo'
            p.name = 'foo'
            p.value = 'hi'
            p.type = None
            p.uuid = 'someuuid'
            configfile = self.get_dummy_configfile(temp_dir)
            p.conf = configfile

            net = NiceCXNetwork()
            node_one_id = net.create_node('node1')
            node_two_id = net.create_node('node2')

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json = MagicMock(return_value=net.to_cx())
            mockclient = MagicMock()
            mockclient.get_network_as_cx_stream = MagicMock(return_value=mock_resp)
            adder = NodeAttributeAdder(p, altclient=mockclient)
            self.assertEqual(0, adder.run())
            update_args = mockclient.update_cx_network.call_args
            self.assertEqual(p.uuid, update_args[0][1])
            updated_net = json.load(update_args[0][0])
            new_net = ndex2.create_nice_cx_from_raw_cx(updated_net)
            self.assertEqual('hi', new_net.get_node_attribute(node_two_id, 'foo')['v'])
            self.assertEqual('hi', new_net.get_node_attribute(node_one_id, 'foo')['v'])
        finally:
            shutil.rmtree(temp_dir)

    def test_run_success_with_nodestoinclude(self):
        temp_dir = tempfile.mkdtemp()
        try:
            p = MagicMock()
            p.profile = 'foo'
            p.name = 'foo'
            p.value = '7'
            p.type = 'integer'
            p.uuid = 'someuuid'
            configfile = self.get_dummy_configfile(temp_dir)
            p.conf = configfile

            net = NiceCXNetwork()
            node_one_id = net.create_node('node1')
            p.nodestoskip = str(node_one_id)
            node_two_id = net.create_node('node2')

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json = MagicMock(return_value=net.to_cx())
            mockclient = MagicMock()
            mockclient.get_network_as_cx_stream = MagicMock(return_value=mock_resp)
            adder = NodeAttributeAdder(p, altclient=mockclient)
            self.assertEqual(0, adder.run())
            net.remove_node_attribute(node_one_id, 'foo')
            update_args = mockclient.update_cx_network.call_args
            self.assertEqual(p.uuid, update_args[0][1])
            updated_net = json.load(update_args[0][0])
            new_net = ndex2.create_nice_cx_from_raw_cx(updated_net)
            self.assertEqual(7, new_net.get_node_attribute(node_two_id, 'foo')['v'])
            self.assertEqual('integer', new_net.get_node_attribute(node_two_id, 'foo')['d'])
            self.assertEqual(None, new_net.get_node_attribute(node_one_id, 'foo'))
        finally:
            shutil.rmtree(temp_dir)

    def test_run_success_with_double_val(self):
        temp_dir = tempfile.mkdtemp()
        try:
            p = MagicMock()
            p.profile = 'foo'
            p.nodestoskip = None
            p.name = 'foo'
            p.value = '7.5'
            p.type = 'double'
            p.uuid = 'someuuid'
            configfile = self.get_dummy_configfile(temp_dir)
            p.conf = configfile

            net = NiceCXNetwork()
            node_one_id = net.create_node('node1')
            node_two_id = net.create_node('node2')

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json = MagicMock(return_value=net.to_cx())
            mockclient = MagicMock()
            mockclient.get_network_as_cx_stream = MagicMock(return_value=mock_resp)
            adder = NodeAttributeAdder(p, altclient=mockclient)
            self.assertEqual(0, adder.run())
            net.remove_node_attribute(node_one_id, 'foo')
            update_args = mockclient.update_cx_network.call_args
            self.assertEqual(p.uuid, update_args[0][1])
            updated_net = json.load(update_args[0][0])
            new_net = ndex2.create_nice_cx_from_raw_cx(updated_net)
            self.assertEqual(7.5, new_net.get_node_attribute(node_one_id, 'foo')['v'])
            self.assertEqual('double', new_net.get_node_attribute(node_one_id, 'foo')['d'])
            self.assertEqual(7.5, new_net.get_node_attribute(node_two_id, 'foo')['v'])
            self.assertEqual('double', new_net.get_node_attribute(node_two_id, 'foo')['d'])
        finally:
            shutil.rmtree(temp_dir)

    def test_run_success_with_boolean_val(self):
        temp_dir = tempfile.mkdtemp()
        try:
            p = MagicMock()
            p.profile = 'foo'
            p.nodestoskip = None
            p.name = 'foo'
            p.value = 'true'
            p.type = 'boolean'
            p.uuid = 'someuuid'
            configfile = self.get_dummy_configfile(temp_dir)
            p.conf = configfile

            net = NiceCXNetwork()
            node_one_id = net.create_node('node1')
            node_two_id = net.create_node('node2')

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json = MagicMock(return_value=net.to_cx())
            mockclient = MagicMock()
            mockclient.get_network_as_cx_stream = MagicMock(return_value=mock_resp)
            adder = NodeAttributeAdder(p, altclient=mockclient)
            self.assertEqual(0, adder.run())
            net.remove_node_attribute(node_one_id, 'foo')
            update_args = mockclient.update_cx_network.call_args
            self.assertEqual(p.uuid, update_args[0][1])
            updated_net = json.load(update_args[0][0])
            new_net = ndex2.create_nice_cx_from_raw_cx(updated_net)
            self.assertEqual(True, new_net.get_node_attribute(node_one_id, 'foo')['v'])
            self.assertEqual('boolean', new_net.get_node_attribute(node_one_id, 'foo')['d'])
            self.assertEqual(True, new_net.get_node_attribute(node_two_id, 'foo')['v'])
            self.assertEqual('boolean', new_net.get_node_attribute(node_two_id, 'foo')['d'])
        finally:
            shutil.rmtree(temp_dir)

    def test_run_fail_due_to_type_conversion_failure(self):
        temp_dir = tempfile.mkdtemp()
        try:
            p = MagicMock()
            p.profile = 'foo'
            p.nodestoskip = None
            p.name = 'foo'
            p.value = 'haha'
            p.type = 'integer'
            p.uuid = 'someuuid'
            configfile = self.get_dummy_configfile(temp_dir)
            p.conf = configfile
            net = NiceCXNetwork()
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json = MagicMock(return_value=net.to_cx())
            mockclient = MagicMock()
            mockclient.get_network_as_cx_stream = MagicMock(return_value=mock_resp)
            adder = NodeAttributeAdder(p, altclient=mockclient)
            try:
                adder.run()
            except NDExUtilError as ne:
                self.assertEqual('Unable to convert --value haha to integer : '
                                 'invalid literal for int() with '
                                 'base 10: \'haha\'', str(ne))
        finally:
            shutil.rmtree(temp_dir)

    def test_run_unable_to_get_network(self):
        temp_dir = tempfile.mkdtemp()
        try:
            p = MagicMock()
            p.nodestoinclude = None
            p.profile = 'foo'
            p.name = 'foo'
            p.uuid = 'someuuid'
            configfile = self.get_dummy_configfile(temp_dir)
            p.conf = configfile

            mock_resp = MagicMock()
            mock_resp.status_code = 500
            mockclient = MagicMock()
            mockclient.get_network_as_cx_stream = MagicMock(return_value=mock_resp)
            adder = NodeAttributeAdder(p, altclient=mockclient)
            try:
                adder.run()
                self.fail('Expected NDExUtilError')
            except NDExUtilError as ne:
                self.assertEqual('Unable to download network with id: '
                                 'someuuid from NDEx', str(ne))
        finally:
            shutil.rmtree(temp_dir)

    def test_run_unable_to_get_network_due_to_exception_on_download(self):
        temp_dir = tempfile.mkdtemp()
        try:
            p = MagicMock()
            p.nodestoinclude = None
            p.profile = 'foo'
            p.name = 'foo'
            p.uuid = 'someuuid'
            configfile = self.get_dummy_configfile(temp_dir)
            p.conf = configfile

            mockclient = MagicMock()
            mockclient.get_network_as_cx_stream = MagicMock(side_effect=Exception('some error'))
            adder = NodeAttributeAdder(p, altclient=mockclient)
            try:
                adder.run()
                self.fail('Expected NDExUtilError')
            except NDExUtilError as ne:
                self.assertEqual('Caught an exception downloading network: '
                                 'some error', str(ne))
        finally:
            shutil.rmtree(temp_dir)

    def test_run_unable_to_get_network_due_to_exception_on_convert(self):
        temp_dir = tempfile.mkdtemp()
        try:
            p = MagicMock()
            p.nodestoinclude = None
            p.profile = 'foo'
            p.name = 'foo'
            p.uuid = 'someuuid'
            configfile = self.get_dummy_configfile(temp_dir)
            p.conf = configfile

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json = MagicMock(return_value=[])
            mockclient = MagicMock()
            mockclient.get_network_as_cx_stream = MagicMock(return_value=mock_resp)
            adder = NodeAttributeAdder(p, altclient=mockclient)
            try:
                adder.run()
                self.fail('Expected NDExUtilError')
            except NDExUtilError as ne:
                self.assertEqual('Caught an exception converting '
                                 'downloaded networkto '
                                 'NiceCXNetwork object: '
                                 'CX is empty', str(ne))
        finally:
            shutil.rmtree(temp_dir)
