#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ndex` module."""

import tempfile
import shutil
import os
import unittest
import json
from unittest.mock import MagicMock
from unittest import mock
import requests
import requests_mock

from ndexutil.ndex import NDExExtraUtils
from ndexutil.exceptions import NDExUtilError
from ndex2.nice_cx_network import NiceCXNetwork


class TestNDExExtraUtils(unittest.TestCase):
    """
        Tests NDExExtraUtils in ndex module
    """
    def setUp(self):
        """Set up test fixtures, if any."""
        pass

    def tearDown(self):
        """Tear down test fixtures, if any."""
        pass

    def test_get_node_id_mapping_from_node_attribute_none_cx_file(self):
        util = NDExExtraUtils()
        try:
            util.get_node_id_mapping_from_node_attribute(cxfile=None)
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertEqual('cxfile is None', str(ne))

    def test_get_node_id_mapping_from_node_attribute_no_cx_file(self):
        util = NDExExtraUtils()
        temp_dir = tempfile.mkdtemp()
        try:
            nofile = os.path.join(temp_dir, 'doesnotexist.cx')
            util.get_node_id_mapping_from_node_attribute(cxfile=nofile)
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertEqual(nofile + ' file not found', str(ne))
        finally:
            shutil.rmtree(temp_dir)

    def test_get_node_id_mapping_from_node_attribute_no_nodeid_attr(self):
        util = NDExExtraUtils()
        temp_dir = tempfile.mkdtemp()
        try:
            cxfile = os.path.join(temp_dir, 'foo.cx')
            net = NiceCXNetwork()
            net.create_node('node1')
            net.create_node('node2')
            net.create_node('node3')
            with open(cxfile, 'w') as f:
                json.dump(net.to_cx(), f)
            res = util.get_node_id_mapping_from_node_attribute(cxfile=cxfile)
            self.assertEqual({}, res)
        finally:
            shutil.rmtree(temp_dir)

    def test_get_node_id_mapping_from_node_attribute_success(self):
        util = NDExExtraUtils()
        temp_dir = tempfile.mkdtemp()
        try:
            cxfile = os.path.join(temp_dir, 'foo.cx')
            net = NiceCXNetwork()
            net.create_node('node1')
            net.create_node('node2')
            net.create_node('node3')
            with open(cxfile, 'w') as f:
                json.dump(net.to_cx(), f)
            util.add_node_id_as_node_attribute(cxfile=cxfile,
                                               outcxfile=cxfile)
            res = util.get_node_id_mapping_from_node_attribute(cxfile=cxfile)
            self.assertEqual({0: 0, 1: 1, 2: 2}, res)
        finally:
            shutil.rmtree(temp_dir)

    def test_update_network_on_ndex_invalid_args(self):
        util = NDExExtraUtils()
        try:
            util.update_network_on_ndex()
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertEqual('NDEx client is None', str(ne))

        try:
            util.update_network_on_ndex(client=MagicMock())
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertEqual('Network UUID is None', str(ne))

        try:
            util.update_network_on_ndex(client=MagicMock(),
                                        networkid='1234')
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertEqual('cxfile is None', str(ne))

        temp_dir = tempfile.mkdtemp()
        try:
            try:
                non_exist_file = os.path.join(temp_dir,
                                              'doesnotexist')
                util.update_network_on_ndex(client=MagicMock(),
                                            networkid='1234',
                                            cxfile=non_exist_file)
                self.fail('Expected NDExUtilError')
            except NDExUtilError as ne:
                self.assertEqual(non_exist_file +
                                 ' is not a file', str(ne))
        finally:
            shutil.rmtree(temp_dir)

    def test_update_network_on_ndex_success(self):
        util = NDExExtraUtils()
        temp_dir = tempfile.mkdtemp()
        try:
            cxfile = os.path.join(temp_dir, 'some.cx')
            with open(cxfile, 'wb') as f:
                f.write(b'hello')
            client = MagicMock()
            client.update_cx_network = MagicMock(return_value='response')
            res = util.update_network_on_ndex(client=client,
                                              networkid='1234',
                                              cxfile=cxfile)
            self.assertEqual('response', res)
            client.update_cx_network.assert_called_with(mock.ANY,
                                                        '1234')
        finally:
            shutil.rmtree(temp_dir)

    def test_update_network_aspect_on_ndex_invalid_args(self):
        util = NDExExtraUtils()
        try:
            util.update_network_aspect_on_ndex()
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertEqual('NDEx client is None', str(ne))

        try:
            util.update_network_aspect_on_ndex(client=MagicMock())
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertEqual('Network UUID is None', str(ne))

        try:
            util.update_network_aspect_on_ndex(client=MagicMock(),
                                               networkid='1234')
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertEqual('Aspect name is None', str(ne))

        try:
            util.update_network_aspect_on_ndex(client=MagicMock(),
                                               networkid='1234',
                                               aspect_name='name')
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertEqual('Aspect data is None', str(ne))

    def test_update_network_aspect_on_ndex_success(self):
        util = NDExExtraUtils()
        temp_dir = tempfile.mkdtemp()
        try:
            client = MagicMock()
            client.put = MagicMock(return_value='response')
            cart_aspect = [{'node': 0, 'x': 2, 'y': 3}]
            res = util.update_network_aspect_on_ndex(client=client,
                                                     networkid='1234',
                                                     aspect_name='cartesianLayout',
                                                     aspect_data=cart_aspect)
            self.assertEqual('response', res)
            net = NiceCXNetwork()
            net.set_opaque_aspect('cartesianLayout', cart_aspect)
            client.put.assert_called_with('/network/1234/aspects',
                                                        put_json=json.dumps(net.to_cx()))
        finally:
            shutil.rmtree(temp_dir)

    def test_download_network_from_ndex_invalid_args(self):
        util = NDExExtraUtils()
        try:
            util.download_network_from_ndex()
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertEqual('NDEx client is None', str(ne))

        try:
            util.download_network_from_ndex(client=MagicMock())
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertEqual('Network UUID is None', str(ne))

        try:
            util.download_network_from_ndex(client=MagicMock(),
                                            networkid=MagicMock())
            self.fail('Expected NDExUtilError')
        except NDExUtilError as ne:
            self.assertEqual('Destfile is None', str(ne))

    def test_download_network_from_ndex_invalidfile(self):
        temp_dir = tempfile.mkdtemp()
        util = NDExExtraUtils()
        client = MagicMock()
        try:
            destfile = temp_dir
            with requests_mock.Mocker() as m:
                m.get('http://foo.com', content=b'hello')
                client.get_network_as_cx_stream = MagicMock(return_value=requests.get('http://foo.com', stream=True))
                try:
                    util.download_network_from_ndex(client=client,
                                                    networkid='1234',
                                                    destfile=destfile)
                    self.fail('Expected an error')
                except Exception as e:
                    pass

            client.get_network_as_cx_stream.assert_called_with('1234')
        finally:
            shutil.rmtree(temp_dir)

    def test_download_network_from_ndex_success(self):
        temp_dir = tempfile.mkdtemp()
        util = NDExExtraUtils()
        client = MagicMock()
        try:
            destfile = os.path.join(temp_dir, 'foo.cx')
            with requests_mock.Mocker() as m:
                m.get('http://foo.com', content=b'hello')
                client.get_network_as_cx_stream = MagicMock(return_value=requests.get('http://foo.com', stream=True))
                res = util.download_network_from_ndex(client=client,
                                                      networkid='1234',
                                                      destfile=destfile)
                self.assertTrue(os.path.isfile(res))
                with open(res, 'rb') as f:
                    self.assertEqual(b'hello', f.read())
            client.get_network_as_cx_stream.assert_called_with('1234')
        finally:
            shutil.rmtree(temp_dir)

    def test_extract_layout_aspect_from_cx_success(self):
        util = NDExExtraUtils()
        temp_dir = tempfile.mkdtemp()
        try:
            cxfile = os.path.join(temp_dir, 'foo.cx')
            net = NiceCXNetwork()
            nid = net.create_node('node1')
            net.add_node_attribute(property_of=nid,
                                   name=NDExExtraUtils.ORIG_NODE_ID_ATTR,
                                   values=4,
                                   type='long')
            nid = net.create_node('node2')
            net.add_node_attribute(property_of=nid,
                                   name=NDExExtraUtils.ORIG_NODE_ID_ATTR,
                                   values=5,
                                   type='long')
            nid = net.create_node('node3')
            net.add_node_attribute(property_of=nid,
                                   name=NDExExtraUtils.ORIG_NODE_ID_ATTR,
                                   values=6,
                                   type='long')
            net.set_opaque_aspect('cartesianLayout', [{'node': 0, 'x': 1, 'y': 2},
                                                      {'node': 1, 'x': 3, 'y': 4},
                                                      {'node': 2, 'x': 5, 'y': 6, 'z': 7}])
            with open(cxfile, 'w') as f:
                json.dump(net.to_cx(), f)
            res = util.get_node_id_mapping_from_node_attribute(cxfile=cxfile)
            self.assertEqual({0: 4, 1: 5, 2: 6}, res)

            res = util.extract_layout_aspect_from_cx(input_cx_file=cxfile)
            self.assertEqual([{'node': 4, 'x': 1.0, 'y': 2.0},
                              {'node': 5, 'x': 3.0, 'y': 4.0},
                              {'node': 6, 'x': 5.0, 'y': 6.0, 'z': 7.0}], res)
        finally:
            shutil.rmtree(temp_dir)

