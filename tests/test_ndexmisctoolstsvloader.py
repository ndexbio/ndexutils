#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ndexmisctools` module."""

import tempfile
import shutil
import os
import uuid
from json.decoder import JSONDecodeError
from requests.exceptions import HTTPError
import unittest
from unittest.mock import MagicMock


from ndexutil.exceptions import ConfigError
from ndexutil.exceptions import NDExUtilError
from ndexutil.ndexmisctools import TSVLoader
from ndexutil import ndexmisctools
from ndexutil.config import NDExUtilConfig


class Params(object):
    pass


class TestTSVLoader(unittest.TestCase):
    """
        Tests TSVLoader in ndexmisctools module
    """

    def get_gene_disease_style_cx_file(self):
        return os.path.join(os.path.dirname(__file__),
                            'tsv', 'gene-disease-style.cx')

    def get_dummy_params(self):
        p = Params()
        p.username = 'bob'
        p.password = 'password'
        p.server = 'ndex'
        return p

    def setUp(self):
        """Set up test fixtures, if any."""
        pass

    def tearDown(self):
        """Tear down test fixtures, if any."""
        pass

    def test_parse_config_no_credentials_needed_from_configfile(self):
        temp_dir = tempfile.mkdtemp()
        try:
            p = MagicMock()
            p.username = 'bob'
            p.password = 'password'
            p.server = 'public.ndexbio.org'
            p.conf = temp_dir
            loader = TSVLoader(p)
            self.assertEqual('bob', loader._user)
            self.assertEqual('password', loader._pass)
            self.assertEqual('public.ndexbio.org', loader._server)
        finally:
            shutil.rmtree(temp_dir)

    def test_parse_config_no_configfile(self):
        temp_dir = tempfile.mkdtemp()
        try:
            p = MagicMock()
            p.username = 'bob'
            p.password = '-'
            p.server = 'public.ndexbio.org'
            p.conf = temp_dir
            loader = TSVLoader(p)
            self.fail('Expected ConfigError')
        except ConfigError as e:
            self.assertEqual('No configuration file found', str(e))
        finally:
            shutil.rmtree(temp_dir)

    def test_parse_config_valid_configfile(self):
        temp_dir = tempfile.mkdtemp()
        try:
            cfile = os.path.join(temp_dir, 'configfile')
            with open(cfile, 'w') as f:
                f.write('[foo]\n')
                f.write(NDExUtilConfig.USER + ' = theuser\n')
                f.write(NDExUtilConfig.PASSWORD + ' = thepass\n')
                f.write(NDExUtilConfig.SERVER + ' = theserver\n')

            # try with username set to - to load it from config
            p = MagicMock()
            p.username = '-'
            p.password = 'somepass'
            p.server = 'ndex'
            p.conf = cfile
            p.profile = 'foo'
            loader = TSVLoader(p)
            self.assertEqual('theuser', loader._user)
            self.assertEqual('somepass', loader._pass)
            self.assertEqual('ndex', loader._server)

            # try with password set to - to load it from config
            p.password = '-'
            loader = TSVLoader(p)
            self.assertEqual('theuser', loader._user)
            self.assertEqual('thepass', loader._pass)
            self.assertEqual('ndex', loader._server)

            # try with server set to - to load it from config
            p.server = '-'
            loader = TSVLoader(p)
            self.assertEqual('theuser', loader._user)
            self.assertEqual('thepass', loader._pass)
            self.assertEqual('theserver', loader._server)
        finally:
            shutil.rmtree(temp_dir)

    def test_get_client_with_alt_set(self):
        p = self.get_dummy_params()
        loader = TSVLoader(p, altclient='foo')
        self.assertEqual('foo', loader._get_client())

    def test_get_cx_style_template_not_set(self):
        p = self.get_dummy_params()
        p.t = None
        loader = TSVLoader(p)
        self.assertEqual(None, loader._get_cx_style())

    def test_get_cx_style_template_is_invalid_cx_not_in_jsonformat(self):
        temp_dir = tempfile.mkdtemp()
        try:
            p = self.get_dummy_params()

            invalidcx = os.path.join(temp_dir, 'foo.cx')
            with open(invalidcx, 'w') as f:
                f.write('hi')

            p.t = invalidcx
            loader = TSVLoader(p)
            loader._get_cx_style()
            self.fail('Expected JSONDecodeError')
        except JSONDecodeError:
            pass
        finally:
            shutil.rmtree(temp_dir)

    def test_get_cx_style_template_is_invalid_cx(self):
        temp_dir = tempfile.mkdtemp()
        try:
            p = self.get_dummy_params()

            invalidcx = os.path.join(temp_dir, 'foo.cx')
            with open(invalidcx, 'w') as f:
                f.write('{"hi": "there"}')

            p.t = invalidcx
            loader = TSVLoader(p)
            net = loader._get_cx_style()
            self.assertEqual(0, len(net.get_nodes()))
            self.assertEqual(0, len(net.get_edges()))
        finally:
            shutil.rmtree(temp_dir)

    def test_get_cx_style_template_is_invalid_uuid(self):
        temp_dir = tempfile.mkdtemp()
        try:
            p = self.get_dummy_params()

            p.t = str(uuid.uuid4()) + str(uuid.uuid4())
            loader = TSVLoader(p)
            loader._get_cx_style()
            self.fail('Expected NDExUtilError ')
        except NDExUtilError as e:
            self.assertEqual(p.t +
                             ' does not appear to be a valid NDEx UUID',
                             str(e))
        finally:
            shutil.rmtree(temp_dir)

    def test_get_cx_style_valid_cx_file(self):
        p = self.get_dummy_params()

        p.t = self.get_gene_disease_style_cx_file()
        loader = TSVLoader(p)
        net = loader._get_cx_style()
        self.assertEqual(5, len(net.get_nodes()))

    def test_get_cx_style_valid_network_file(self):
        p = self.get_dummy_params()
        p.t = str(uuid.uuid4())
        mockclient = MagicMock()

        with open(self.get_gene_disease_style_cx_file(), 'r') as f:
            cx = f.read()

        mockres = MagicMock()
        mockres.text = cx
        mockclient.get_network_as_cx_stream = MagicMock(return_value=mockres)
        loader = TSVLoader(p)

        net = loader._get_cx_style(client=mockclient)
        self.assertEqual(5, len(net.get_nodes()))

    def test_get_network_attributes_network_is_none(self):
        p = self.get_dummy_params()
        p.description = None
        p.name = None
        loader = TSVLoader(p)
        net_attribs = loader._get_network_attributes(None)
        self.assertEqual(None, net_attribs)

        # set name
        p.name = 'hello'
        loader = TSVLoader(p)
        net_attribs = loader._get_network_attributes(None)
        self.assertEqual(1, len(net_attribs))
        self.assertTrue({'n': 'name', 'v': 'hello',
                         'd': 'string'} in net_attribs)

        # now set description too
        p.description = 'something'
        loader = TSVLoader(p)
        net_attribs = loader._get_network_attributes(None)
        self.assertEqual(2, len(net_attribs))
        self.assertTrue({'n': 'name', 'v': 'hello',
                         'd': 'string'} in net_attribs)
        self.assertTrue({'n': 'description', 'v': 'something',
                         'd': 'string'} in net_attribs)

    def test_get_network_attributes_with_network(self):
        p = self.get_dummy_params()
        p.description = None
        p.name = None
        p.t = self.get_gene_disease_style_cx_file()
        loader = TSVLoader(p)
        net = loader._get_cx_style()
        net_attribs = loader._get_network_attributes(net)
        import sys
        sys.stdout.write(str(net_attribs))
        sys.stdout.flush()
        self.assertEqual(8, len(net_attribs))
        self.assertTrue({'n': 'description',
                         'v': 'Used to style CTD '
                              'gene-disease associations'} in net_attribs)
        self.assertTrue({'n': 'name',
                         'v': 'Style for CTD '
                              'Gene-disease associations'} in net_attribs)

        # set name
        p.name = 'hello'
        loader = TSVLoader(p)
        net_attribs = loader._get_network_attributes(net)
        self.assertEqual(8, len(net_attribs))
        self.assertTrue({'n': 'name', 'v': 'hello',
                         'd': 'string'} in net_attribs)
        self.assertTrue({'n': 'name',
                         'v': 'Style for CTD '
                              'Gene-disease associations'} not in net_attribs)

        # now set description too
        p.description = 'something'
        loader = TSVLoader(p)
        net_attribs = loader._get_network_attributes(net)
        self.assertEqual(8, len(net_attribs))
        self.assertTrue({'n': 'name', 'v': 'hello',
                         'd': 'string'} in net_attribs)
        self.assertTrue({'n': 'description', 'v': 'something',
                         'd': 'string'} in net_attribs)
        self.assertTrue({'n': 'description',
                         'v': 'Used to style CTD '
                              'gene-disease associations'} not in net_attribs)

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
        mockclient.save_cx_stream_as_new_network = MagicMock(side_effect=HTTPError('401 Client Error'))
        loader = TSVLoader(p)
        res = loader._upload_network(mockclient,
                                     self.get_gene_disease_style_cx_file())
        self.assertEqual(2, res)

    def test_upload_network_with_some_other_error(self):
        p = self.get_dummy_params()
        p.u = None
        mockclient = MagicMock()
        mockclient.save_cx_stream_as_new_network = MagicMock(side_effect=HTTPError('500 Server Error'))
        loader = TSVLoader(p)
        res = loader._upload_network(mockclient,
                                     self.get_gene_disease_style_cx_file())
        self.assertEqual(3, res)

    def test_get_tsvfile_header_is_none(self):
        p = self.get_dummy_params()
        p.tsv_file = 'sometemplate.cx'
        p.t = None
        p.uppercaseheader = False
        p.header = None
        loader = TSVLoader(p)
        self.assertEqual(p.tsv_file, loader._get_tsvfile())

    def test_get_tsvfile_header_is_set(self):
        temp_dir = tempfile.mkdtemp()
        try:
            p = self.get_dummy_params()
            cxfile = os.path.join(temp_dir, 'some.cx')
            with open(cxfile, 'w') as f:
                f.write('hello\n')
            p.t = cxfile
            p.tsv_file = cxfile
            p.tmpdir = temp_dir
            p.header = 'blahblah'
            loader = TSVLoader(p)
            loader._tmpdir = temp_dir
            tmptsv = os.path.join(temp_dir, 'temp.tsv')
            self.assertEqual(tmptsv,
                             loader._get_tsvfile())
            with open(tmptsv, 'r') as f:
                self.assertEqual('blahblah\n', f.readline())
                self.assertEqual('hello\n', f.readline())
                self.assertEqual('', f.read())
        finally:
            shutil.rmtree(temp_dir)

    def test_get_tsvfile_uppercaseheader_is_set(self):
        temp_dir = tempfile.mkdtemp()
        try:
            p = self.get_dummy_params()
            cxfile = os.path.join(temp_dir, 'some.cx')
            with open(cxfile, 'w') as f:
                f.write('myheader\n')
                f.write('hello\n')
            p.t = cxfile
            p.tsv_file = cxfile
            p.tmpdir = temp_dir
            p.header = None
            p.uppercaseheader = True
            loader = TSVLoader(p)
            loader._tmpdir = temp_dir
            tmptsv = os.path.join(temp_dir, 'temp.tsv')
            self.assertEqual(tmptsv,
                             loader._get_tsvfile())
            with open(tmptsv, 'r') as f:
                self.assertEqual('MYHEADER\n', f.readline())
                self.assertEqual('hello\n', f.readline())
                self.assertEqual('', f.read())
        finally:
            shutil.rmtree(temp_dir)

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
            mockclient = MagicMock()
            mockclient.save_cx_stream_as_new_network = MagicMock(return_value='hi')
            mockfac = MagicMock()
            mocktsvloader = MagicMock()
            mocktsvloader.write_cx_network = MagicMock(return_value=None)

            mockfac.get_tsv_streamloader = MagicMock(return_value=mocktsvloader)

            loader = TSVLoader(p, altclient=mockclient, streamtsvfac=mockfac)
            loader.run()

            mockfac.get_tsv_streamloader.assert_called_once()
            self.assertEqual('plan', mockfac.get_tsv_streamloader.call_args[0][0])
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
            mockclient = MagicMock()
            mockfac = MagicMock()
            mocktsvloader = MagicMock()
            mocktsvloader.write_cx_network = MagicMock(return_value=None)

            mockfac.get_tsv_streamloader = MagicMock(return_value=mocktsvloader)

            loader = TSVLoader(p, altclient=mockclient, streamtsvfac=mockfac)
            loader.run()
            net = loader._get_cx_style(None)
            mockfac.get_tsv_streamloader.assert_called_once()
            self.assertEqual('plan', mockfac.get_tsv_streamloader.call_args[0][0])
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
