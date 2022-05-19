# -*- coding: utf-8 -*-

"""Tests for :py:func:`ndex2.create_nice_cx_from_networkx`"""

import os
import unittest
import json
import networkx as nx
import ndex2


SKIP_REASON = 'NDEX2_TEST_USER environment variable detected, ' \
              'skipping for integration tests'


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestCreateNiceCXNetworkFromNetworkX(unittest.TestCase):

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

    def test_create_nice_cx_from_networkx_with_none(self):
        try:
            ndex2.create_nice_cx_from_networkx(None)
            self.fail('Expected Exception')
        except Exception as e:
            self.assertEqual('Networkx input is empty', str(e))

    def test_create_nice_cx_from_networkx_with_emptystr(self):
        try:
            ndex2.create_nice_cx_from_networkx('')
            self.fail('Expected Exception')
        except AttributeError as e:
            self.assertTrue('object has no' in str(e))

    def test_create_nice_cx_from_networkx_with_invalidstr(self):
        try:
            ndex2.create_nice_cx_from_networkx('invalid')
            self.fail('Expected Exception')
        except AttributeError as e:
            self.assertTrue('object has no' in str(e))

    def test_create_nice_cx_from_networkx_roundtrip_no_attrs(self):
        net = ndex2.nice_cx_network.NiceCXNetwork()
        node_one = net.create_node('Node 1')
        node_two = net.create_node('Node 2')
        net.create_edge(edge_source=node_one, edge_target=node_two)
        netx_net = net.to_networkx(mode='default')
        net_roundtrip = ndex2.create_nice_cx_from_networkx(netx_net)
        self.assertEqual('created from networkx by '
                         'ndex2.create_nice_cx_networkx()',
                         net_roundtrip.get_name())
        self.assertEqual(1, len(net_roundtrip.get_edges()))
        self.assertEqual(2, len(net_roundtrip.get_nodes()))
        self.assertEqual((0, {'@id': 0,
                              's': 0, 't': 1,
                              'i': 'neighbor-of'}),
                         list(net_roundtrip.get_edges())[0])

        for node_id, node_obj in net_roundtrip.get_nodes():
            if node_id == 0:
                self.assertEqual({'@id': 0,
                                  'n': 'Node 1',
                                  'r': 'Node 1'}, node_obj)
            elif node_id == 1:
                self.assertEqual({'@id': 1,
                                  'n': 'Node 2',
                                  'r': 'Node 2'}, node_obj)
            else:
                self.fail('Invalid node: ' + str(node_obj))

    def test_create_nice_cx_from_networkx_roundtrip_with_attrs(self):
        net = ndex2.nice_cx_network.NiceCXNetwork()
        node_one = net.create_node('Node 1')
        node_two = net.create_node('Node 2')
        net.set_node_attribute(node_one, 'somestrfield', 'hi')

        edge_one = net.create_edge(edge_source=node_one, edge_target=node_two,
                                   edge_interaction='breaks')
        net.set_edge_attribute(edge_one, 'somestrfield', 'bye')
        net.set_opaque_aspect(ndex2.constants.CARTESIAN_LAYOUT_ASPECT,
                              [{'node': node_one, 'x': 1.0, 'y': 2.0},
                               {'node': node_two, 'x': 3.0, 'y': 4.0}])

        net.set_name('mynetwork')
        netx_net = net.to_networkx(mode='default')
        net_roundtrip = ndex2.create_nice_cx_from_networkx(netx_net)

        self.assertEqual(netx_net.pos[0], (1.0, -2.0))
        self.assertEqual(netx_net.pos[1], (3.0, -4.0))

        self.assertEqual('mynetwork', net_roundtrip.get_name())
        self.assertEqual(1, len(net_roundtrip.get_edges()))
        self.assertEqual(2, len(net_roundtrip.get_nodes()))

        self.assertEqual((0, {'@id': 0,
                              's': 0, 't': 1,
                              'i': 'breaks'}),
                         list(net_roundtrip.get_edges())[0])

        for node_id, node_obj in net_roundtrip.get_nodes():
            if node_id == 0:
                self.assertEqual({'@id': 0,
                                  'n': 'Node 1',
                                  'r': 'Node 1'}, node_obj)
            elif node_id == 1:
                self.assertEqual({'@id': 1,
                                  'n': 'Node 2',
                                  'r': 'Node 2'}, node_obj)
            else:
                self.fail('Invalid node: ' + str(node_obj))

        n_a = net_roundtrip.get_node_attribute(node_one,
                                               'somestrfield')
        self.assertEqual({'po': 0,
                          'n': 'somestrfield',
                          'v': 'hi', 'd': 'string'}, n_a)

        n_a = net_roundtrip.get_edge_attribute(node_one,
                                               'somestrfield')
        self.assertEqual({'po': 0,
                          'n': 'somestrfield',
                          'v': 'bye', 'd': 'string'}, n_a)

    def test_create_nice_cx_from_networkx_roundtrip_glypican(self):

        net = ndex2.create_nice_cx_from_file(TestCreateNiceCXNetworkFromNetworkX.GLYPICAN_FILE)
        netx_net = net.to_networkx(mode='default')
        net_roundtrip = ndex2.create_nice_cx_from_networkx(netx_net)
        self.assertEqual(2, len(net_roundtrip.get_nodes()))
        self.assertEqual(1, len(net_roundtrip.get_edges()))
        self.assertEqual('Glypican 2 network', net_roundtrip.get_name())
        edge = net_roundtrip.get_edge(0)
        self.assertEqual({'@id': 0, 's': 1, 't': 0,
                          'i': 'in-complex-with'},
                         edge)
        e_a = net_roundtrip.get_edge_attribute(edge['@id'],
                                               'directed')

        # currently DefaultNetworkXFactory blindly
        # migrates the value from NiceCXNetwork to
        # networkx, since values are strings that is
        # what the value is set to so during roundtrip
        # a string is set as the datatype
        self.assertEqual({'po': 0, 'n': 'directed',
                          'v': 'false', 'd': 'string'}, e_a)

        n_a = net_roundtrip.get_node_attribute(0, 'type')
        self.assertEqual({'po': 0, 'n': 'type',
                          'v': 'Protein', 'd': 'string'}, n_a)
        n_a = net_roundtrip.get_node_attribute(1, 'type')
        self.assertEqual({'po': 1, 'n': 'type',
                          'v': 'Protein', 'd': 'string'}, n_a)

        n_a = net_roundtrip.get_node_attribute(0, 'alias')
        self.assertEqual({"po": 0, "n": "alias",
                          "v": ["uniprot knowledgebase:Q2LEK4",
                                "uniprot knowledgebase:Q9UCC7"],
                          "d": "list_of_string"}, n_a)

        n_a = net_roundtrip.get_node_attribute(1, 'alias')
        self.assertEqual({"po": 1, "n": "alias",
                          "v": ["uniprot knowledgebase:Q8N158"],
                          "d": "list_of_string"}, n_a)

        cart = net_roundtrip.get_opaque_aspect(ndex2.constants.CARTESIAN_LAYOUT_ASPECT)

        self.assertEqual(2, len(cart))
        self.assertEqual(0, cart[0]['node'])
        self.assertEqual(-398.3511334928659, cart[0]['x'])
        self.assertEqual(70.71067799518471, cart[0]['y'])

        self.assertEqual(1, cart[1]['node'])
        self.assertEqual(-353.49370090105185, cart[1]['x'])
        self.assertEqual(70.71067822788493, cart[1]['y'])





