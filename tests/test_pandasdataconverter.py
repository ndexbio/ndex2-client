# -*- coding: utf-8 -*-

"""Tests for `PandasDataConverter` class."""

import os
import unittest

from ndex2 import constants
from ndex2.exceptions import NDExError
from ndex2.util import DataConverter
from ndex2.util import PandasDataConverter

SKIP_REASON = 'NDEX2_TEST_SERVER environment variable detected, ' \
              'skipping for integration tests'


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestDefaultNetworkXFactory(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures, if any."""
        pass

    def tearDown(self):
        """Tear down test fixtures, if any."""
        pass

    def test_data_converter_class(self):
        converter = DataConverter()
        try:
            converter.convert_value()
            self.fail('Expected NotImplementedError')
        except NotImplementedError as ne:
            self.assertEqual('Must be implemented by subclass', str(ne))

    def test_convert_value_unknown_types(self):
        converter = PandasDataConverter()
        try:
            converter.convert_value('asdf', 'FOO')
            self.fail('Expected NDExError')
        except NDExError as ne:
            self.assertEqual('FOO unknown data type, cannot convert: asdf', str(ne))

        try:
            converter.convert_value(None, converter)
            self.fail('Expected NDExError')
        except NDExError as ne:
            self.assertTrue('Unable to convert None' in str(ne))

    def test_convert_value_basic_types(self):
        converter = PandasDataConverter()
        # test None
        self.assertEqual('None', converter.convert_value())

        # test no data type (assume str)
        self.assertEqual('hello', converter.convert_value('hello'))

        # test str
        converted_val = converter.convert_value('true',
                                                datatype=constants.STRING_DATATYPE)
        self.assertTrue(isinstance(converted_val, str))
        self.assertEqual('hello', converter.convert_value(value='hello',
                                                          datatype='STRING'))

        # test boolean
        converted_val = converter.convert_value('true',
                                                datatype=constants.BOOLEAN_DATATYPE)
        self.assertTrue(isinstance(converted_val, bool))
        self.assertEqual(True, converter.convert_value(True,
                                                       datatype=constants.BOOLEAN_DATATYPE))
        self.assertEqual(False, converter.convert_value(False,
                                                        datatype=constants.BOOLEAN_DATATYPE))

        self.assertEqual(True, converter.convert_value(7,
                                                       datatype=constants.BOOLEAN_DATATYPE))
        self.assertEqual(True, converter.convert_value(1,
                                                       datatype=constants.BOOLEAN_DATATYPE))
        self.assertEqual(False, converter.convert_value(0,
                                                        datatype=constants.BOOLEAN_DATATYPE))

        self.assertEqual(True, converter.convert_value('TruE',
                                                       datatype=constants.BOOLEAN_DATATYPE))
        self.assertEqual(False, converter.convert_value('fAlse',
                                                        datatype=constants.BOOLEAN_DATATYPE))
        self.assertEqual(True, converter.convert_value('rando text',
                                                       datatype=constants.BOOLEAN_DATATYPE))

        # test long and int
        for dtype in [constants.INTEGER_DATATYPE, constants.LONG_DATATYPE]:
            converted_val = converter.convert_value('3',
                                                    datatype=dtype)
            self.assertTrue(isinstance(converted_val, int))
            self.assertEqual(1, converter.convert_value(True,
                                                        datatype=dtype))
            self.assertEqual(0, converter.convert_value(False,
                                                        datatype=dtype))

            self.assertEqual(7, converter.convert_value(7,
                                                        datatype=dtype))
            self.assertEqual(1, converter.convert_value(1.1,
                                                        datatype=dtype))
            self.assertEqual(-5, converter.convert_value(-5,
                                                         datatype=dtype))
            try:
                converter.convert_value('TruE',
                                        datatype=dtype)
                self.fail('Expected exception')
            except NDExError as ne:
                self.assertTrue('Unable to convert TruE to type '
                                'compatible with ' + dtype.lower() +
                                ' CX data type :' in str(ne))

        # test double
        converted_val = converter.convert_value('5.5',
                                                datatype=constants.DOUBLE_DATATYPE)
        self.assertTrue(isinstance(converted_val, float))
        self.assertEqual(1, converter.convert_value(True,
                                                    datatype=constants.DOUBLE_DATATYPE))
        self.assertEqual(0, converter.convert_value(False,
                                                    datatype=constants.DOUBLE_DATATYPE))

        self.assertEqual(7, converter.convert_value(7,
                                                    datatype=constants.DOUBLE_DATATYPE))
        self.assertEqual(1.1, converter.convert_value(1.1,
                                                      datatype=constants.DOUBLE_DATATYPE))
        self.assertEqual(-5, converter.convert_value(-5,
                                                     datatype=constants.DOUBLE_DATATYPE))
        try:
            converter.convert_value('TruE',
                                    datatype=constants.DOUBLE_DATATYPE)
            self.fail('Expected exception')
        except NDExError as ne:
            self.assertTrue('Unable to convert TruE to type '
                            'compatible with double CX data type :' in str(ne))

    def test_convert_value_list_types(self):
        converter = PandasDataConverter()

        # list_of_string
        res = converter.convert_value(value='ha',
                                      datatype=constants.LIST_OF_STRING)
        self.assertEqual('ha', res)

        res = converter.convert_value(value=[],
                                      datatype=constants.LIST_OF_STRING)
        self.assertEqual('', res)

        res = converter.convert_value(value=[1, '2', 'TrUE', None],
                                      datatype=constants.LIST_OF_STRING)
        self.assertEqual('1,2,TrUE,None', res)

        # list_of_boolean
        res = converter.convert_value(value=[],
                                      datatype=constants.LIST_OF_BOOLEAN)
        self.assertEqual('', res)
        res = converter.convert_value(value=[False, 'fAlse', 1,
                                             '1', 'TrUE', None, 0],
                                      datatype=constants.LIST_OF_BOOLEAN)
        self.assertEqual('False,fAlse,1,1,TrUE,None,0', res)

        # list_of_double
        res = converter.convert_value(value=[0, '1', '2.0', '-3.0', True, False],
                                      datatype=constants.LIST_OF_DOUBLE)
        self.assertEqual('0,1,2.0,-3.0,True,False', res)

        # list_of_long, list_of_integer
        for dtype in [constants.LIST_OF_INTEGER, constants.LIST_OF_LONG]:
            res = converter.convert_value(value=[],
                                          datatype=dtype)
            self.assertEqual('', res)

