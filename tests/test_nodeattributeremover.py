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
from ndexutil.ndexmisctools import NodeAttributeRemover
from ndexutil.config import NDExUtilConfig


class Params(object):
    pass


class TestNodeAttributeRemover(unittest.TestCase):
    """
        Tests NodeAttributeRemover in ndexmisctools module
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
            remover = NodeAttributeRemover(p)
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
            loader = NodeAttributeRemover(p)
            loader._parse_config()
            self.assertEqual('theuser', loader._user)
            self.assertEqual('thepass', loader._pass)
            self.assertEqual('theserver', loader._server)
        finally:
            shutil.rmtree(temp_dir)

    def test_get_nodes_to_include(self):
        p = MagicMock()

        # try with nodestoinclude set to None
        p.nodestoinclude = None
        remover = NodeAttributeRemover(p)
        self.assertEqual(None, remover._get_nodes_to_include())

        # try with one element
        p.nodestoinclude = '12'
        remover = NodeAttributeRemover(p)
        self.assertEqual([12], remover._get_nodes_to_include())

        # try with two elements
        p.nodestoinclude = '10,11'
        remover = NodeAttributeRemover(p)
        self.assertEqual([10, 11], remover._get_nodes_to_include())

        # try with non numeric element
        p.nodestoinclude = '10,11,x'
        remover = NodeAttributeRemover(p)
        try:
            remover._get_nodes_to_include()
            self.fail('Expected NdexUtilError')
        except NDExUtilError as ne:
            self.assertEqual('Non numeric node id in '
                             '--nodestoinclude parameter: x',
                             str(ne))

    def test_get_client_with_alt_set(self):
        p = MagicMock()
        remover = NodeAttributeRemover(p, altclient='foo')
        self.assertEqual('foo', remover._get_client())

    def test_run_success(self):
        temp_dir = tempfile.mkdtemp()
        try:
            p = MagicMock()
            p.nodestoinclude = None
            p.profile = 'foo'
            p.name = 'foo'
            p.uuid = 'someuuid'
            configfile = self.get_dummy_configfile(temp_dir)
            p.conf = configfile

            net = NiceCXNetwork()
            node_one_id = net.create_node('node1')
            node_two_id = net.create_node('node2')
            net.add_node_attribute(node_one_id, name='foo', values='v1')
            net.add_node_attribute(node_two_id, name='foo', values='v2')

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json = MagicMock(return_value=net.to_cx())
            mockclient = MagicMock()
            mockclient.get_network_as_cx_stream = MagicMock(return_value=mock_resp)
            remover = NodeAttributeRemover(p, altclient=mockclient)
            self.assertEqual(0, remover.run())
            update_args = mockclient.update_cx_network.call_args
            self.assertEqual(p.uuid, update_args[0][1])
            updated_net = json.load(update_args[0][0])
            new_net = ndex2.create_nice_cx_from_raw_cx(updated_net)
            self.assertEqual(None, new_net.get_node_attribute(node_two_id, 'foo'))
            self.assertEqual(None, new_net.get_node_attribute(node_one_id, 'foo'))
        finally:
            shutil.rmtree(temp_dir)

    def test_run_success_with_nodestoinclude(self):
        temp_dir = tempfile.mkdtemp()
        try:
            p = MagicMock()
            p.nodestoinclude = None
            p.profile = 'foo'
            p.name = 'foo'
            p.uuid = 'someuuid'
            configfile = self.get_dummy_configfile(temp_dir)
            p.conf = configfile

            net = NiceCXNetwork()
            node_one_id = net.create_node('node1')
            p.nodestoinclude = str(node_one_id)
            node_two_id = net.create_node('node2')
            net.add_node_attribute(node_one_id, name='foo', values='v1')
            net.add_node_attribute(node_two_id, name='foo', values='v2')

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json = MagicMock(return_value=net.to_cx())
            mockclient = MagicMock()
            mockclient.get_network_as_cx_stream = MagicMock(return_value=mock_resp)
            remover = NodeAttributeRemover(p, altclient=mockclient)
            self.assertEqual(0, remover.run())
            net.remove_node_attribute(node_one_id, 'foo')
            update_args = mockclient.update_cx_network.call_args
            self.assertEqual(p.uuid, update_args[0][1])
            updated_net = json.load(update_args[0][0])
            new_net = ndex2.create_nice_cx_from_raw_cx(updated_net)
            self.assertEqual('v2', new_net.get_node_attribute(node_two_id, 'foo')['v'])
            self.assertEqual(None, new_net.get_node_attribute(node_one_id, 'foo'))
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
            remover = NodeAttributeRemover(p, altclient=mockclient)
            try:
                remover.run()
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
            remover = NodeAttributeRemover(p, altclient=mockclient)
            try:
                remover.run()
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
            remover = NodeAttributeRemover(p, altclient=mockclient)
            try:
                remover.run()
                self.fail('Expected NDExUtilError')
            except NDExUtilError as ne:
                self.assertEqual('Caught an exception converting '
                                 'downloaded networkto '
                                 'NiceCXNetwork object: '
                                 'CX is empty', str(ne))
        finally:
            shutil.rmtree(temp_dir)


"""
    def test_upload_network_with_new_network(self):
        p = self.get_dummy_params()
        p.u = None
        mockclient = MagicMock()
        mockclient.save_cx_stream_as_new_network = MagicMock(return_value='hi')
        loader = TSVLoader(p)
        res = loader._upload_network(mockclient,
                                     self.get_gene_disease_style_cx_file())
        self.assertEqual(0, res)

    def test_upload_network_update_network(self):
        p = self.get_dummy_params()
        p.u = 'hello'
        mockclient = MagicMock()
        mockclient.update_cx_network = MagicMock(return_value='hi')
        loader = TSVLoader(p)
        res = loader._upload_network(mockclient,
                                     self.get_gene_disease_style_cx_file())
        self.assertEqual(0, res)

    def test_upload_network_with_invalid_credentials(self):
        p = self.get_dummy_params()
        p.u = None
        mockclient = MagicMock()
        mockclient.save_cx_stream_as_new_network =\
            MagicMock(side_effect=HTTPError('401 Client Error'))
        loader = TSVLoader(p)
        res = loader._upload_network(mockclient,
                                     self.get_gene_disease_style_cx_file())
        self.assertEqual(2, res)

    def test_upload_network_with_some_other_error(self):
        p = self.get_dummy_params()
        p.u = None
        mockclient = MagicMock()
        mockclient.save_cx_stream_as_new_network =\
            MagicMock(side_effect=HTTPError('500 Server Error'))
        loader = TSVLoader(p)
        res = loader._upload_network(mockclient,
                                     self.get_gene_disease_style_cx_file())
        self.assertEqual(3, res)

    def test_mock_run_success(self):
        temp_dir = tempfile.mkdtemp()
        try:
            p = self.get_dummy_params()
            p.tsv_file = 'somefile.tsv'
            with open(p.tsv_file, 'w') as f:
                f.write('a\tb\n')
                f.write('c\td\n')
            p.t = self.get_gene_disease_style_cx_file()
            p.u = None
            p.header = None
            p.name = 'new name'
            p.tmpdir = temp_dir
            p.uppercaseheader = False
            p.description = 'new description'
            p.load_plan = 'plan'
            p.outputcx = None
            p.skipupload = None
            p.copyattribs = True
            mockclient = MagicMock()
            mockclient.save_cx_stream_as_new_network =\
                MagicMock(return_value='hi')
            mockfac = MagicMock()
            mocktsvloader = MagicMock()
            mocktsvloader.write_cx_network = MagicMock(return_value=None)

            mockfac.get_tsv_streamloader =\
                MagicMock(return_value=mocktsvloader)

            loader = TSVLoader(p, altclient=mockclient, streamtsvfac=mockfac)
            loader.run()

            mockfac.get_tsv_streamloader.assert_called_once()
            self.assertEqual('plan',
                             mockfac.get_tsv_streamloader.call_args[0][0])
            mocktsvloader.write_cx_network.assert_called_once()
            n_a = mocktsvloader.write_cx_network.call_args[1]
            self.assertTrue({'n': 'name',
                             'v': 'new name',
                             'd': 'string'} in n_a['network_attributes'])
            mockclient.save_cx_stream_as_new_network.assert_called_once()
            for entry in os.listdir(temp_dir):
                full_path = os.path.join(entry)
                if os.path.isdir(full_path):
                    self.fail('The run() method should have deleted '
                              'this directory: ' + full_path)

        finally:
            shutil.rmtree(temp_dir)

    def test_mock_run_success_outputcx_and_skipupload_set(self):
        temp_dir = tempfile.mkdtemp()
        try:
            p = self.get_dummy_params()
            p.t = self.get_gene_disease_style_cx_file()
            p.tsv_file = 'somefile.tsv'
            with open(p.tsv_file, 'w') as f:
                f.write('a\tb\n')
                f.write('c\td\n')
            p.header = None
            p.name = 'new name'
            p.uppercaseheader = False
            p.tmpdir = temp_dir
            p.description = 'new description'
            p.load_plan = 'plan'
            p.outputcx = os.path.join(temp_dir, 'my.cx')
            p.skipupload = True
            p.copyattribs = True
            mockclient = MagicMock()
            mockfac = MagicMock()
            mocktsvloader = MagicMock()
            mocktsvloader.write_cx_network = MagicMock(return_value=None)

            mockfac.get_tsv_streamloader = \
                MagicMock(return_value=mocktsvloader)

            loader = TSVLoader(p, altclient=mockclient, streamtsvfac=mockfac)
            loader.run()
            mockfac.get_tsv_streamloader.assert_called_once()
            self.assertEqual('plan',
                             mockfac.get_tsv_streamloader.call_args[0][0])
            mocktsvloader.write_cx_network.assert_called_once()
            n_a = mocktsvloader.write_cx_network.call_args[1]
            self.assertTrue({'n': 'name',
                             'v': 'new name',
                             'd': 'string'} in n_a['network_attributes'])
            for entry in os.listdir(temp_dir):
                full_path = os.path.join(entry)
                if os.path.isdir(full_path):
                    self.fail('The run() method should have deleted '
                              'this directory: ' + full_path)
            self.assertTrue(os.path.isfile(p.outputcx))
        finally:
            shutil.rmtree(temp_dir)
"""