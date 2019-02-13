#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ndexutils` script."""

import tempfile
import unittest

from ndexutil import ndexutils


class TestNDexUtils(unittest.TestCase):
    """
    Tests ndexutils.py
    """
    def setUp(self):
        """Set up test fixtures, if any."""
        pass

    def tearDown(self):
        """Tear down test fixtures, if any."""
        pass

    def test_parse_arguments(self):
        res = ndexutils._parse_arguments('hi', ['foo'])
        self.assertEqual(res.command, None)
