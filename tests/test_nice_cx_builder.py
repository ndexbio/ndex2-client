#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `nice_cx_builder` package."""

import os
import math
import unittest


from unittest.mock import MagicMock, ANY
import requests_mock
from ndex2 import client
from ndex2.nice_cx_network import NiceCXNetwork
from ndex2.exceptions import NDExError
from ndex2 import constants
from ndex2cx.nice_cx_builder import NiceCXBuilder
import ndex2


SKIP_REASON = 'NDEX2_TEST_USER environment variable detected, ' \
              'skipping for integration tests'


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestNiceCXBuilder(unittest.TestCase):

    TEST_DIR = os.path.dirname(__file__)
    WNT_SIGNAL_FILE = os.path.join(TEST_DIR, 'data', 'wntsignaling.cx')
    DARKTHEME_FILE = os.path.join(TEST_DIR, 'data', 'darkthemefinal.cx')
    DARKTHEMENODE_FILE = os.path.join(TEST_DIR, 'data',
                                      'darkthemefinalwithnodevis.cx')
    GLYPICAN_FILE = os.path.join(TEST_DIR, 'data', 'glypican2.cx')

    def setUp(self):
        """Set up test fixtures, if any."""
        pass

    def tearDown(self):
        """Tear down test fixtures, if any."""
        pass

    def test_infer_data_type_none_val(self):
        builder = NiceCXBuilder()
        self.assertEqual((None, None),
                         builder._infer_data_type(None))

    def test_infer_data_type_str_split_is_false(self):
        builder = NiceCXBuilder()

        # empty string
        self.assertEqual(('', 'string'),
                         builder._infer_data_type(''))

        # string with space
        self.assertEqual((' ', 'string'),
                         builder._infer_data_type(' '))

        # simple string
        self.assertEqual(('foo', 'string'),
                         builder._infer_data_type('foo'))

        # simple string with double quote
        self.assertEqual(('foo"', 'string'),
                         builder._infer_data_type('foo"'))

        # string with comma delimiter, but split_string is left
        # to default which is False
        self.assertEqual(('item1,item2', 'string'),
                         builder._infer_data_type('item1,item2'))

        # string with comma delimiter, but split_string is left
        # to default which is False
        self.assertEqual(('item1;item2', 'string'),
                         builder._infer_data_type('item1;item2'))

        # string with comma and semicolon delimiter and double quote,
        # but split_string is left to default which is False
        self.assertEqual(('item1;item2,item3"', 'string'),
                         builder._infer_data_type('item1;item2,item3"'))

    def test_infer_data_type_str_split_is_true(self):
        builder = NiceCXBuilder()

        # empty string
        self.assertEqual(('', 'string'),
                         builder._infer_data_type('',
                                                  split_string=True))

        # string with space
        self.assertEqual((' ', 'string'),
                         builder._infer_data_type(' ',
                                                  split_string=True))

        # simple string
        self.assertEqual(('foo', 'string'),
                         builder._infer_data_type('foo',
                                                  split_string=True))

        # simple string with double quote
        self.assertEqual(('foo', 'string'),
                         builder._infer_data_type('foo"',
                                                  split_string=True))

        # string with comma delimiter, but split_string is left
        # to default which is False
        self.assertEqual((['item1', 'item2'], 'list_of_string'),
                         builder._infer_data_type('item1,item2',
                                                  split_string=True))

        # string with comma delimiter, but split_string is left
        # to default which is False
        self.assertEqual((['item1', 'item2'], 'list_of_string'),
                         builder._infer_data_type('item1;item2',
                                                  split_string=True))

        # string with comma and semicolon delimiter and double quote,
        # but split_string is left to default which is False
        self.assertEqual((['item1;item2', 'item3'], 'list_of_string'),
                         builder._infer_data_type('item1;item2,item3"',
                                                  split_string=True))

    def test_infer_data_type_bool(self):
        """
        Test added for bug: https://github.com/ndexbio/ndex2-client/issues/83
        :return:
        """
        builder = NiceCXBuilder()

        self.assertEqual((True, 'boolean'),
                         builder._infer_data_type(True))

        self.assertEqual((True, 'boolean'),
                         builder._infer_data_type(True,
                                                  split_string=True))

    def test_infer_data_type_int(self):
        """
        Test added for bug: https://github.com/ndexbio/ndex2-client/issues/83
        :return:
        """
        builder = NiceCXBuilder()

        self.assertEqual((1, 'integer'),
                         builder._infer_data_type(1))

        self.assertEqual((1, 'integer'),
                         builder._infer_data_type(1,
                                                  split_string=True))
        self.assertEqual((0, 'integer'),
                         builder._infer_data_type(0))

        self.assertEqual((0, 'integer'),
                         builder._infer_data_type(0,
                                                  split_string=True))

        self.assertEqual((-1, 'integer'),
                         builder._infer_data_type(-1))

        self.assertEqual((-1, 'integer'),
                         builder._infer_data_type(-1,
                                                  split_string=True))

    def test_infer_data_type_double(self):
        """
        Test added for bug: https://github.com/ndexbio/ndex2-client/issues/83
        :return:
        """
        builder = NiceCXBuilder()

        self.assertEqual((1.5, 'double'),
                         builder._infer_data_type(1.5))

        self.assertEqual((1.5, 'double'),
                         builder._infer_data_type(1.5,
                                                  split_string=True))
        self.assertEqual((0.0, 'double'),
                         builder._infer_data_type(0.0))

        self.assertEqual((0.0, 'double'),
                         builder._infer_data_type(0.0,
                                                  split_string=True))

        self.assertEqual((-1.0, 'double'),
                         builder._infer_data_type(-1.0))

        self.assertEqual((-1.0, 'double'),
                         builder._infer_data_type(-1.0,
                                                  split_string=True))

        self.assertEqual((-1.0, 'double'),
                         builder._infer_data_type(-1.0))

        self.assertEqual((-1.0, 'double'),
                         builder._infer_data_type(-1.0,
                                                  split_string=True))

        self.assertEqual((None, 'double'),
                         builder._infer_data_type(math.nan))

        self.assertEqual((None, 'double'),
                         builder._infer_data_type(math.nan,
                                                  split_string=True))
        self.assertEqual(('INFINITY', 'double'),
                         builder._infer_data_type(math.inf))

        self.assertEqual(('INFINITY', 'double'),
                         builder._infer_data_type(math.inf,
                                                  split_string=True))

    def test_infer_data_type_list_of_bool(self):
        """
        Test added for bug: https://github.com/ndexbio/ndex2-client/issues/83
        :return:
        """
        builder = NiceCXBuilder()

        self.assertEqual(([True, False], 'list_of_boolean'),
                         builder._infer_data_type([True, False]))

        self.assertEqual(([True, False], 'list_of_boolean'),
                         builder._infer_data_type([True, False],
                                                  split_string=True))

    def test_infer_data_type_empty_list(self):
        builder = NiceCXBuilder()

        self.assertEqual(([], 'list_of_string'),
                         builder._infer_data_type([]))

        self.assertEqual(([], 'list_of_string'),
                         builder._infer_data_type([],
                                                  split_string=True))

    def test_infer_data_type_list_of_double(self):
        """
        Test added for bug: https://github.com/ndexbio/ndex2-client/issues/83
        :return:
        """
        builder = NiceCXBuilder()

        self.assertEqual(([1.5], 'list_of_double'),
                         builder._infer_data_type([1.5]))

        self.assertEqual(([1.5], 'list_of_double'),
                         builder._infer_data_type([1.5],
                                                  split_string=True))

    def test_infer_data_type_list_of_integer(self):
        """
        Test added for bug: https://github.com/ndexbio/ndex2-client/issues/83
        :return:
        """
        builder = NiceCXBuilder()

        self.assertEqual(([1], 'list_of_integer'),
                         builder._infer_data_type([1]))

        self.assertEqual(([1], 'list_of_integer'),
                         builder._infer_data_type([1],
                                                  split_string=True))

    def test_set_context(self):
        # set context as list
        builder = NiceCXBuilder()
        builder.set_context([{'a': 'a_url', 'b': 'b_url'}])

        res = builder.get_nice_cx()
        self.assertEqual({'a': 'a_url',
                          'b': 'b_url'}, res.get_context())

        # set context as dict
        builder = NiceCXBuilder()
        builder.set_context({'a': 'a_url', 'b': 'b_url'})

        res = builder.get_nice_cx()
        self.assertEqual({'a': 'a_url',
                          'b': 'b_url'}, res.get_context())




