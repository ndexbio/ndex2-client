#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `nbgwas_rest` package."""


import decimal
import unittest

import numpy as np

from ndex2.client import DecimalEncoder

class TestClient(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures, if any."""
        pass

    def tearDown(self):
        """Tear down test fixtures, if any."""
        pass

    def test_decimalencoder(self):
        dec = DecimalEncoder()

        # test bytes is returned as string
        res = dec.default(bytes('hello', 'utf-8'))
        self.assertTrue(isinstance(res, str))

        # test decimal.Decimal is float
        res = dec.default(decimal.Decimal(5))
        self.assertTrue(isinstance(res, float))

        # test numpy.int64 is int
        res = dec.default(np.int64(12))
        self.assertTrue(isinstance(res, int))

        # test regular old int which throws TypeError
        try:
            res = dec.default(1)
            self.fail('Expected exception')
        except TypeError:
            pass
