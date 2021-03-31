#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `nice_cx_network` package."""

import os
import unittest
import sys
import warnings

import requests_mock
from ndex2 import client
from ndex2.nice_cx_network import NiceCXNetwork
from ndex2.exceptions import NDExError
from ndex2 import constants
import ndex2


SKIP_REASON = 'NDEX2_TEST_USER environment variable detected, ' \
              'skipping for integration tests'


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestNiceCXNetwork(unittest.TestCase):

    TEST_DIR = os.path.dirname(__file__)
    WNT_SIGNAL_FILE = os.path.join(TEST_DIR, 'data', 'wntsignaling.cx')
    DARKTHEME_FILE = os.path.join(TEST_DIR, 'data', 'darkthemefinal.cx')
    DARKTHEMENODE_FILE = os.path.join(TEST_DIR, 'data',
                                      'darkthemefinalwithnodevis.cx')
    GLYPICAN_FILE = os.path.join(TEST_DIR, 'data', 'glypican2.cx')

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

    def test_is_python_three_or_greater(self):
        isThree = False

        if sys.version_info.major >= 3:
            isThree = True

        self.assertEqual(isThree, NiceCXNetwork._is_python_three_or_greater())

    def test_add_edge(self):
        net_cx = NiceCXNetwork()
        try:
            net_cx.add_edge()
            self.fail('Expected Warning')
        except Warning as we:
            self.assertTrue('add_edge() is deprecated' in str(we))

    def test_add_node(self):
        net_cx = NiceCXNetwork()
        try:
            net_cx.add_node()
            self.fail('Expected Warning')
        except Warning as we:
            self.assertTrue('add_node() is deprecated' in str(we))

    def test_add_opaque_aspect_invalid_type(self):
        net_cx = NiceCXNetwork()
        try:
            net_cx.add_opaque_aspect('foo', 'invalid data')
            self.fail('Expected Exception')
        except Exception as e:
            self.assertEqual('Provided input was not of type list.', str(e))

    def test_add_opaque_aspect_success(self):
        net_cx = NiceCXNetwork()
        data = ['hi']
        net_cx.add_opaque_aspect('hi', data)
        res = net_cx.get_opaque_aspect('hi')
        self.assertEqual(data, res)

    def test_add_opaque_aspect_with_dict_with_error(self):
        net_cx = NiceCXNetwork()
        data = {'error': '', 'hi': 'blah'}
        net_cx.add_opaque_aspect('hi', data)
        res = net_cx.get_opaque_aspect('hi')
        self.assertEqual(None, res)

    def test_add_opaque_aspect_with_dict(self):
        net_cx = NiceCXNetwork()
        data = {'hi': 'blah'}
        net_cx.add_opaque_aspect('hi', data)
        res = net_cx.get_opaque_aspect('hi')
        self.assertEqual([data], res)

    def test_add_opaque_aspect_element(self):
        try:
            net_cx = NiceCXNetwork()
            net_cx.add_opaque_aspect_element('foo')
            self.fail('Expected Exception')
        except Exception as e:
            self.assertTrue('add_opaque_aspect_element() is '
                            'deprecated' in str(e))

    def test_get_name(self):
        net_cx = NiceCXNetwork()
        self.assertEqual(None, net_cx.get_name())

        net_cx.set_name('name1')
        self.assertEqual('name1', net_cx.get_name())

        net_cx.set_name('name2')
        self.assertEqual('name2', net_cx.get_name())

        net_cx.set_name(None)
        self.assertEqual(None, net_cx.get_name())


    def test_create_edge_with_int_for_edge_ids(self):
        net = NiceCXNetwork()
        net.create_edge(edge_source=0, edge_target=1)
        res = net.get_edge(0)
        self.assertEqual(0, res[constants.EDGE_ID])
        self.assertEqual(0, res[constants.EDGE_SOURCE])
        self.assertEqual(1, res[constants.EDGE_TARGET])

    def test_create_edge_with_node_dict_passed_in_for_edge_ids(self):
        net = NiceCXNetwork()

        nodeone = net.get_node(net.create_node('node1'))
        nodetwo = net.get_node(net.create_node('node2'))
        edge_id = net.create_edge(edge_source=nodeone,
                                  edge_target=nodetwo)
        res = net.get_edge(edge_id)
        self.assertEqual(edge_id, res[constants.EDGE_ID])
        self.assertEqual(0, res[constants.EDGE_SOURCE])
        self.assertEqual(1, res[constants.EDGE_TARGET])

    def test_create_edge_with_interaction(self):
        net = NiceCXNetwork()
        edge_id = net.create_edge(edge_source=10,
                                  edge_target=20, edge_interaction='blah')

        res = net.get_edge(edge_id)
        self.assertEqual(edge_id, res[constants.EDGE_ID])
        self.assertEqual(10, res[constants.EDGE_SOURCE])
        self.assertEqual(20, res[constants.EDGE_TARGET])
        self.assertEqual('blah', res[constants.EDGE_INTERACTION])

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
        self.assertEqual(res[0][constants.NODE_ATTR_DATATYPE],
                         'list_of_string')

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

    def test_add_network_attribute_duplicate_add(self):
        net = NiceCXNetwork()
        net.add_network_attribute(name='foo',
                                  values=['a', 'b'],
                                  type='list_of_string')
        res = net.get_network_attribute('foo')
        self.assertEqual('list_of_string', res['d'])

        # add duplicate with no type
        net.add_network_attribute(name='foo',
                                  values=['a', 'b'])
        res = net.get_network_attribute('foo')
        self.assertTrue('d' not in res)

        net.add_network_attribute(name='foo',
                                  values=4,
                                  type='integer')
        res = net.get_network_attribute('foo')
        self.assertEqual('integer', res['d'])

    def test_get_network_attribute_names(self):
        net = NiceCXNetwork()

        # try on empty network
        res = list(net.get_network_attribute_names())
        self.assertEqual(0, len(res))

        # try with one network attribute
        net.add_network_attribute('foo')
        res = list(net.get_network_attribute_names())
        self.assertEqual(1, len(res))
        self.assertTrue('foo' in res)

        # try with two network attribute
        net.add_network_attribute('bah', values='some value')
        res = list(net.get_network_attribute_names())
        self.assertEqual(2, len(res))
        self.assertTrue('foo' in res)
        self.assertTrue('bah' in res)

        # try with 52 network attributes
        for x in range(50):
            net.add_network_attribute('attr' + str(x),
                                      values='some value ' + str(x))
        res = list(net.get_network_attribute_names())
        self.assertEqual(52, len(res))
        self.assertTrue('foo' in res)
        self.assertTrue('bah' in res)
        for x in range(50):
            self.assertTrue('attr' + str(x) in res)

    def test_get_nodes(self):
        net = NiceCXNetwork()

        # Verify correct operation on empty network
        res = list(net.get_nodes())
        self.assertEqual(0, len(res))

        # add a node
        net.create_node('foo')
        res = list(net.get_nodes())
        self.assertEqual(1, len(res))
        self.assertEqual(res[0], (0, {'@id': 0, 'n': 'foo', 'r': 'foo'}))

        # add another node
        net.create_node('bar')
        res = list(net.get_nodes())
        self.assertEqual(2, len(res))
        self.assertEqual(res[0], (0, {'@id': 0, 'n': 'foo', 'r': 'foo'}))
        self.assertEqual(res[1], (1, {'@id': 1, 'n': 'bar', 'r': 'bar'}))

    def test_get_edges(self):
        net = NiceCXNetwork()

        # Verify correct operation on empty network
        res = list(net.get_edges())
        self.assertEqual(0, len(res))

        # add an edge
        net.create_edge(edge_source=0, edge_target=1)
        res = list(net.get_edges())
        self.assertEqual(1, len(res))
        self.assertEqual(res[0], (0, {'@id': 0, 's': 0, 't': 1}))

        # add another edge
        net.create_edge(edge_source=1, edge_target=2)
        res = list(net.get_edges())
        self.assertEqual(2, len(res))
        self.assertEqual(res[0], (0, {'@id': 0, 's': 0, 't': 1}))
        self.assertEqual(res[1], (1, {'@id': 1, 's': 1, 't': 2}))

    def test_get_metadata(self):
        net = NiceCXNetwork()

        # verify correct operation on empty network
        res = list(net.get_metadata())
        self.assertEqual(0, len(res))

        net.set_metadata({'foo': 1})
        res = list(net.get_metadata())
        self.assertEqual(1, len(res))
        self.assertEqual(res[0], ('foo', 1))

    def test_get_node_and_edge_items(self):
        net = NiceCXNetwork()

        nodeiter, edgeiter = net._get_node_and_edge_items()
        nodelist = list(nodeiter)
        self.assertEqual(0, len(nodelist))
        edgelist = list(edgeiter)
        self.assertEqual(0, len(edgelist))

        net.create_node('foo')
        net.create_edge(edge_source=0, edge_target=1)

        nodeiter, edgeiter = net._get_node_and_edge_items()
        nodelist = list(nodeiter)
        self.assertEqual(1, len(nodelist))
        self.assertEqual(nodelist[0], (0, {'@id': 0,
                                           'n': 'foo', 'r': 'foo'}))
        edgelist = list(edgeiter)

        self.assertEqual(1, len(edgelist))
        self.assertEqual(edgelist[0], (0, {'@id': 0, 's': 0, 't': 1}))

    def test__str__(self):
        net = NiceCXNetwork()
        self.assertEqual('nodes: 0 \n edges: 0', str(net))
        net.create_node('foo')
        self.assertEqual('nodes: 1 \n edges: 0', str(net))
        net.create_node('foo2')
        net.create_node('foo3')
        self.assertEqual('nodes: 3 \n edges: 0', str(net))

        net.create_edge(edge_source=0, edge_target=1)
        self.assertEqual('nodes: 3 \n edges: 1', str(net))

    def test_upload_to_success(self):
        with requests_mock.mock() as m:
            resurl = client.DEFAULT_SERVER + '/v2/network/asdf'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict("2.4.0"))
            m.post(client.DEFAULT_SERVER + '/v2/network',
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
            self.assertTrue('{"nodes": [{' in decode_txt)
            self.assertTrue('"@id": 0' in decode_txt)
            self.assertTrue('"n": "bob"' in decode_txt)
            self.assertTrue('"r": "bob"' in decode_txt)
            self.assertTrue('{"status": [{"' in decode_txt)
            self.assertTrue('"error": ""' in decode_txt)
            self.assertTrue('"success": true' in decode_txt)

    def test_update_to_success(self):
        with requests_mock.mock() as m:
            resurl = client.DEFAULT_SERVER + '/v2/network/asdf'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict("2.4.0"))
            m.put(client.DEFAULT_SERVER + '/v2/network/abcd',
                  request_headers={'Connection': 'close'},
                  status_code=1,
                  text=resurl)
            net = NiceCXNetwork()
            net.create_node('bob')
            res = net.update_to('abcd', client.DEFAULT_SERVER,
                                'bob', 'warnerbrandis',
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
            self.assertTrue('{"nodes": [{' in decode_txt)
            self.assertTrue('"@id": 0' in decode_txt)
            self.assertTrue('"n": "bob"' in decode_txt)
            self.assertTrue('"r": "bob"' in decode_txt)
            self.assertTrue('{"status": [{"' in decode_txt)
            self.assertTrue('"error": ""' in decode_txt)
            self.assertTrue('"success": true' in decode_txt)

    def test_remove_node_and_edge_specific_visual_properties_with_none(self):
        mynet = NiceCXNetwork()
        res = mynet._remove_node_and_edge_specific_visual_properties(None)
        self.assertEqual(None, res)

    def test_set_visual_properties_aspect_with_none(self):
        mynet = NiceCXNetwork()
        try:
            mynet._set_visual_properties_aspect(None)
            self.fail('Expected TypeError')
        except TypeError as e:
            self.assertEqual('Visual Properties aspect is None', str(e))

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

    def test_apply_style_from_network_no_style(self):
        wntcx = ndex2.create_nice_cx_from_file(TestNiceCXNetwork
                                               .WNT_SIGNAL_FILE)
        wntcx.remove_opaque_aspect(NiceCXNetwork.CY_VISUAL_PROPERTIES)
        darkcx = ndex2.create_nice_cx_from_file(TestNiceCXNetwork
                                                .DARKTHEME_FILE)
        try:
            darkcx.apply_style_from_network(wntcx)
            self.fail('Expected NDexError')
        except NDExError as ne:
            self.assertEqual('No visual style found in network', str(ne))

    def test_apply_style_from_wnt_network_to_dark_network(self):
        darkcx = ndex2.create_nice_cx_from_file(TestNiceCXNetwork
                                                .DARKTHEME_FILE)
        dark_vis_aspect = darkcx.get_opaque_aspect(NiceCXNetwork
                                                   .CY_VISUAL_PROPERTIES)
        self.assertEqual(9, len(dark_vis_aspect))
        wntcx = ndex2.create_nice_cx_from_file(TestNiceCXNetwork
                                               .WNT_SIGNAL_FILE)
        wnt_vis_aspect = wntcx.get_opaque_aspect(NiceCXNetwork
                                                 .CY_VISUAL_PROPERTIES)
        self.assertEqual(3, len(wnt_vis_aspect))

        darkcx.apply_style_from_network(wntcx)
        new_dark_vis_aspect = darkcx.get_opaque_aspect(NiceCXNetwork
                                                       .CY_VISUAL_PROPERTIES)
        self.assertEqual(3, len(new_dark_vis_aspect))

    def test_apply_style_with_node_and_edge_specific_visual_values(self):
        wntcx = ndex2.create_nice_cx_from_file(TestNiceCXNetwork
                                               .WNT_SIGNAL_FILE)
        darkcx = ndex2.create_nice_cx_from_file(TestNiceCXNetwork
                                                .DARKTHEMENODE_FILE)

        wntcx.apply_style_from_network(darkcx)
        wnt_vis_aspect = wntcx.get_opaque_aspect(NiceCXNetwork
                                                 .CY_VISUAL_PROPERTIES)
        self.assertEqual(3, len(wnt_vis_aspect))

    def test_apply_style_on_network_with_old_visual_aspect(self):
        glypy = ndex2.create_nice_cx_from_file(TestNiceCXNetwork.GLYPICAN_FILE)
        wntcx = ndex2.create_nice_cx_from_file(TestNiceCXNetwork
                                               .WNT_SIGNAL_FILE)
        glypy.apply_style_from_network(wntcx)
        glypy_aspect = glypy.get_opaque_aspect(NiceCXNetwork
                                               .CY_VISUAL_PROPERTIES)
        self.assertEqual(3, len(glypy_aspect))

    def test_apply_style_on_network_from_old_visual_aspect_network(self):
        glypy = ndex2.create_nice_cx_from_file(TestNiceCXNetwork.GLYPICAN_FILE)
        wntcx = ndex2.create_nice_cx_from_file(TestNiceCXNetwork
                                               .WNT_SIGNAL_FILE)
        wntcx.apply_style_from_network(glypy)
        wnt_aspect = wntcx.get_opaque_aspect(NiceCXNetwork
                                             .CY_VISUAL_PROPERTIES)
        self.assertEqual(3, len(wnt_aspect))

    def test_to_networkx_no_arg_on_empty_network(self):
        net = NiceCXNetwork()
        g = net.to_networkx()
        self.assertEqual('{}', str(g.graph))

    def test_to_networkx_none_mode_on_empty_network(self):
        net = NiceCXNetwork()
        g = net.to_networkx(mode=None)
        self.assertEqual('{}', str(g.graph))

    def test_to_networkx_legacy_mode_on_empty_network(self):
        net = NiceCXNetwork()
        g = net.to_networkx(mode='legacy')
        self.assertEqual('{}', str(g.graph))

    def test_to_networkx_invalid_mode_on_empty_network(self):
        net = NiceCXNetwork()
        try:
            net.to_networkx(mode='someinvalidmode')
            self.fail('Expected NDExError')
        except NDExError as ne:
            self.assertEqual('someinvalidmode is not a valid mode', str(ne))

    def test_to_networkx_simple_graph_no_arg(self):
        net = NiceCXNetwork()
        net.set_name('mynetwork')
        net.create_node('node0')
        net.create_node('node1')
        net.create_edge(edge_source=0, edge_target=1)
        g = net.to_networkx()
        self.assertEqual(g.graph['name'], 'mynetwork')
        self.assertEqual(2, len(g))

    def test_to_networkx_simple_graph_default_mode(self):
        net = NiceCXNetwork(mode='default')
        net.set_name('mynetwork')
        net.create_node('node0')
        net.create_node('node1')
        net.create_edge(edge_source=0, edge_target=1)
        g = net.to_networkx()
        self.assertEqual(g.graph['name'], 'mynetwork')
        self.assertEqual(2, len(g))
