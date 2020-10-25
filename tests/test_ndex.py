#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ndex` module."""

import tempfile
import shutil
import os
import unittest
from unittest.mock import MagicMock
import requests
import requests_mock

from ndexutil.ndex import NDExExtraUtils
from ndexutil.exceptions import NDExUtilError


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


