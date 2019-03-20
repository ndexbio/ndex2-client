#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `nice_cx_network` package."""

import os
import sys
import unittest

import requests_mock
from requests.exceptions import HTTPError
from ndex2 import client
from ndex2.nice_cx_network import NiceCXNetwork
from ndex2.exceptions import NDExError
from ndex2 import constants
import ndex2


class TestNiceCXNetwork(unittest.TestCase):

    TEST_DIR = os.path.dirname(__file__)
    WNT_SIGNAL_FILE = os.path.join(TEST_DIR, 'data', 'wntsignaling.cx')
    DARKTHEME_FILE = os.path.join(TEST_DIR, 'data', 'darkthemefinal.cx')

    def get_rest_admin_status_dict(self, server_version):
        return {"networkCount": 1321,
                "userCount": 12,
                "groupCount": 0,
                "message": "Online",
                "properties": {"ServerVersion": server_version,
                               "ServerResultLimit": "10000"}}

    def get_rest_admin_status_url(self):
        return client.DEFAULT_SERVER + '/rest/admin/status'

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

    def test_upload_to_success(self):
        with requests_mock.mock() as m:
            resurl = client.DEFAULT_SERVER + '/v2/network/asdf'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict("2.4.0"))
            m.post(client.DEFAULT_SERVER + '/v2/network/asCX',
                   request_headers={'Connection': 'close'},
                   status_code=1,
                   text=resurl)
            net = NiceCXNetwork()
            net.create_node('bob')
            res = net.upload_to(client.DEFAULT_SERVER, 'bob', 'warnerbrandis',
                                user_agent='jeez')
            self.assertEqual(res, resurl)
            decode_txt = m.last_request.text.read().decode('UTF-8')
            self.assertEqual(m.last_request.headers['User-Agent'],
                             client.userAgent + ' jeez')
            self.assertTrue('Content-Disposition: form-data; name='
                            '"CXNetworkStream"; filename='
                            '"filename"' in decode_txt)
            self.assertTrue('Content-Type: application/'
                            'octet-stream' in decode_txt)
            self.assertTrue('{"nodes": [{"@id": 0, "n": "bob", "r": "bob"}]},'
                            ' {"status": [{"error": "", "success": '
                            'true}]}]' in decode_txt)

    def test_update_to_success(self):
        with requests_mock.mock() as m:
            resurl = client.DEFAULT_SERVER + '/v2/network/asdf'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict("2.4.0"))
            m.put(client.DEFAULT_SERVER + '/v2/network/asCX/abcd',
                   request_headers={'Connection': 'close'},
                   status_code=1,
                   text=resurl)
            net = NiceCXNetwork()
            net.create_node('bob')
            res = net.update_to('abcd', client.DEFAULT_SERVER, 'bob', 'warnerbrandis',
                                user_agent='jeez')
            self.assertEqual(res, resurl)
            decode_txt = m.last_request.text.read().decode('UTF-8')
            self.assertEqual(m.last_request.headers['User-Agent'],
                             client.userAgent + ' jeez')
            self.assertTrue('Content-Disposition: form-data; name='
                            '"CXNetworkStream"; filename='
                            '"filename"' in decode_txt)
            self.assertTrue('Content-Type: application/'
                            'octet-stream' in decode_txt)
            self.assertTrue('{"nodes": [{"@id": 0, "n": "bob", "r": "bob"}]},'
                            ' {"status": [{"error": "", "success": '
                            'true}]}]' in decode_txt)

    def test_apply_style_from_network_wrong_types(self):
        mynet = NiceCXNetwork()

        try:
            mynet.apply_style_from_network(None)
            self.fail('Expected TypeError')
        except TypeError as e:
            self.assertEqual('Object passed in is None', str(e))

        try:
            mynet.apply_style_from_network(str('hi'))
            self.fail('Expected TypeError')
        except TypeError as e:
            self.assertEqual('Object passed in is not NiceCXNetwork', str(e))

    def test_apply_style_from_network_valid(self):
        darkcx = ndex2.create_nice_cx_from_file(TestNiceCXNetwork.DARKTHEME_FILE)
        wntcx = ndex2.create_nice_cx_from_file(TestNiceCXNetwork.WNT_SIGNAL_FILE)

        darkcx.apply_style_from_network(wntcx)
