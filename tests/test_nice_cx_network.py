#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `nice_cx_network` package."""

import unittest
from ndex2.nice_cx_network import NiceCXNetwork
from ndex2.exceptions import NDExError
from ndex2 import constants

class TestNiceCXNetwork(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures, if any."""
        pass

    def tearDown(self):
        """Tear down test fixtures, if any."""
        pass

    def test_set_node_attribute_none_values(self):
        net = NiceCXNetwork()
        try:
            net.set_node_attribute(None, 'foo', 'blah')
            self.fail('Expected exception')
        except NDExError as ne:
            self.assertEqual(str(ne), 'Node attribute requires property_of')

        try:
            net.set_node_attribute('hi', None, 'blah')
            self.fail('Expected exception')
        except NDExError as ne:
            self.assertEqual(str(ne), 'Node attribute requires the name and '
                                      'values property')

    def test_set_node_attribute_passing_empty_dict(self):
        # try int
        net = NiceCXNetwork()
        try:
            net.set_node_attribute({}, 'attrname', 5)
            self.fail('Expected NDExError')
        except NDExError as ne:
            self.assertEqual(str(ne), 'No id found in Node')


    def test_set_node_attribute_passing_node_object(self):
        # try int
        net = NiceCXNetwork()
        node_id = net.create_node(node_name='foo')
        node = net.get_node(node_id)
        net.set_node_attribute(node, 'attrname', 5)
        res = net.get_node_attributes(node_id)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][constants.NODE_ATTR_PROPERTYOF], node_id)
        self.assertEqual(res[0][constants.NODE_ATTR_NAME], 'attrname')
        self.assertEqual(res[0][constants.NODE_ATTR_VALUE], 5)
        self.assertEqual(res[0][constants.NODE_ATTR_DATATYPE], 'integer')

    def test_set_node_attribute_empty_add_autodetect_datatype(self):

        # try int
        net = NiceCXNetwork()
        net.set_node_attribute(1, 'attrname', 5)
        res = net.get_node_attributes(1)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][constants.NODE_ATTR_PROPERTYOF], 1)
        self.assertEqual(res[0][constants.NODE_ATTR_NAME], 'attrname')
        self.assertEqual(res[0][constants.NODE_ATTR_VALUE], 5)
        self.assertEqual(res[0][constants.NODE_ATTR_DATATYPE], 'integer')

        # try double/float
        net = NiceCXNetwork()
        net.set_node_attribute(1, 'attrname', 5.5)
        res = net.get_node_attributes(1)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][constants.NODE_ATTR_PROPERTYOF], 1)
        self.assertEqual(res[0][constants.NODE_ATTR_NAME], 'attrname')
        self.assertEqual(res[0][constants.NODE_ATTR_VALUE], 5.5)
        self.assertEqual(res[0][constants.NODE_ATTR_DATATYPE], 'double')

        # try list of string
        net = NiceCXNetwork()
        net.set_node_attribute(1, 'attrname', ['hi', 'bye'])
        res = net.get_node_attributes(1)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][constants.NODE_ATTR_PROPERTYOF], 1)
        self.assertEqual(res[0][constants.NODE_ATTR_NAME], 'attrname')
        self.assertEqual(res[0][constants.NODE_ATTR_VALUE], ['hi', 'bye'])
        self.assertEqual(res[0][constants.NODE_ATTR_DATATYPE], 'list_of_string')

    def test_set_node_attribute_empty_add_overwrite_toggled(self):
        net = NiceCXNetwork()
        net.set_node_attribute(1, 'attrname', 'value')
        res = net.get_node_attributes(1)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][constants.NODE_ATTR_PROPERTYOF], 1)
        self.assertEqual(res[0][constants.NODE_ATTR_NAME], 'attrname')
        self.assertEqual(res[0][constants.NODE_ATTR_VALUE], 'value')

        net = NiceCXNetwork()
        net.set_node_attribute(1, 'attrname', 1, type='double')
        res = net.get_node_attributes(1)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][constants.NODE_ATTR_PROPERTYOF], 1)
        self.assertEqual(res[0][constants.NODE_ATTR_NAME], 'attrname')
        self.assertEqual(res[0][constants.NODE_ATTR_VALUE], 1)

        net = NiceCXNetwork()
        net.set_node_attribute(1, 'attrname', 'value', overwrite=True)
        res = net.get_node_attributes(1)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][constants.NODE_ATTR_PROPERTYOF], 1)
        self.assertEqual(res[0][constants.NODE_ATTR_NAME], 'attrname')
        self.assertEqual(res[0][constants.NODE_ATTR_VALUE], 'value')

        net = NiceCXNetwork()
        net.set_node_attribute(1, 'attrname', 1, type='double',
                               overwrite=True)
        res = net.get_node_attributes(1)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][constants.NODE_ATTR_PROPERTYOF], 1)
        self.assertEqual(res[0][constants.NODE_ATTR_NAME], 'attrname')
        self.assertEqual(res[0][constants.NODE_ATTR_VALUE], 1)

    def test_set_node_attribute_add_duplicate_attributes(self):
        net = NiceCXNetwork()
        net.set_node_attribute(1, 'attrname', 'value')
        res = net.get_node_attributes(1)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][constants.NODE_ATTR_PROPERTYOF], 1)
        self.assertEqual(res[0][constants.NODE_ATTR_NAME], 'attrname')
        self.assertEqual(res[0][constants.NODE_ATTR_VALUE], 'value')

        net.set_node_attribute(1, 'attrname', 'value2')
        res = net.get_node_attributes(1)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0][constants.NODE_ATTR_PROPERTYOF], 1)
        self.assertEqual(res[0][constants.NODE_ATTR_NAME], 'attrname')
        self.assertEqual(res[0][constants.NODE_ATTR_VALUE], 'value')
        self.assertEqual(res[1][constants.NODE_ATTR_PROPERTYOF], 1)
        self.assertEqual(res[1][constants.NODE_ATTR_NAME], 'attrname')
        self.assertEqual(res[1][constants.NODE_ATTR_VALUE], 'value2')

        net.set_node_attribute(1, 'attrname', 'value3')
        res = net.get_node_attributes(1)
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0][constants.NODE_ATTR_PROPERTYOF], 1)
        self.assertEqual(res[0][constants.NODE_ATTR_NAME], 'attrname')
        self.assertEqual(res[0][constants.NODE_ATTR_VALUE], 'value')
        self.assertEqual(res[1][constants.NODE_ATTR_PROPERTYOF], 1)
        self.assertEqual(res[1][constants.NODE_ATTR_NAME], 'attrname')
        self.assertEqual(res[1][constants.NODE_ATTR_VALUE], 'value2')
        self.assertEqual(res[2][constants.NODE_ATTR_PROPERTYOF], 1)
        self.assertEqual(res[2][constants.NODE_ATTR_NAME], 'attrname')
        self.assertEqual(res[2][constants.NODE_ATTR_VALUE], 'value3')

    def test_set_node_attribute_add_duplicate_attributes_overwriteset(self):
        net = NiceCXNetwork()
        net.set_node_attribute(1, 'attrname', 'value', overwrite=True)
        res = net.get_node_attributes(1)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][constants.NODE_ATTR_PROPERTYOF], 1)
        self.assertEqual(res[0][constants.NODE_ATTR_NAME], 'attrname')
        self.assertEqual(res[0][constants.NODE_ATTR_VALUE], 'value')

        net.set_node_attribute(1, 'attrname', 'value2', overwrite=True)
        res = net.get_node_attributes(1)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][constants.NODE_ATTR_PROPERTYOF], 1)
        self.assertEqual(res[0][constants.NODE_ATTR_NAME], 'attrname')
        self.assertEqual(res[0][constants.NODE_ATTR_VALUE], 'value2')





