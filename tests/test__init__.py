#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `__init__` package."""

import os
import unittest
import sys
import warnings

from unittest.mock import MagicMock, ANY
import requests_mock
from ndex2 import client
from ndex2.nice_cx_network import NiceCXNetwork
from ndex2.exceptions import NDExError
from ndex2.exceptions import NDExUnauthorizedError
from ndex2.exceptions import NDExNotFoundError
from ndex2 import constants
import ndex2


SKIP_REASON = 'NDEX2_TEST_SERVER environment variable detected, ' \
              'skipping for integration tests'


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestInit(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures, if any."""
        pass

    def tearDown(self):
        """Tear down test fixtures, if any."""
        pass

    def test_create_empty_nice_cx(self):
        net = ndex2.create_empty_nice_cx()
        self.assertEqual(None, net.get_name())
        self.assertEqual(0, len(net.get_nodes()))
        self.assertEqual(0, len(net.get_edges()))