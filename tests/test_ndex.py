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


