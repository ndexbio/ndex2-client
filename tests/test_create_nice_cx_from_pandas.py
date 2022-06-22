# -*- coding: utf-8 -*-

"""Tests for :py:func:`ndex2.create_nice_cx_from_pandas`"""

import os
import unittest
import json
import networkx as nx
import ndex2
import pandas as pd


SKIP_REASON = 'NDEX2_TEST_SERVER environment variable detected, ' \
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

    def test_create_nice_cx_from_pandas_with_none(self):
        try:
            ndex2.create_nice_cx_from_pandas(None)
            self.fail('AssertionError')
        except AttributeError as e:
            self.assertTrue('NoneType' in str(e))

    def test_create_nice_cx_from_pandas_with_emptystr(self):
        try:
            ndex2.create_nice_cx_from_pandas('')
            self.fail('Expected Exception')
        except AttributeError as e:
            self.assertTrue('object has no' in str(e))

    def test_create_nice_cx_from_pandas_with_invalidstr(self):
        try:
            ndex2.create_nice_cx_from_pandas('invalid')
            self.fail('Expected Exception')
        except AttributeError as e:
            self.assertTrue('object has no' in str(e))

    def test_create_nice_cx_from_networkx_roundtrip_no_attrs(self):
        net = ndex2.nice_cx_network.NiceCXNetwork()
        node_one = net.create_node('Node 1')
        node_two = net.create_node('Node 2')
        net.create_edge(edge_source=node_one, edge_target=node_two)
        net_df = net.to_pandas_dataframe(include_attributes=True)
        net_roundtrip = ndex2.create_nice_cx_from_pandas(net_df,
                                                         source_field='source',
                                                         target_field='target')
        self.assertEqual('created from pandas by '
                         'ndex2.create_nice_cx_from_pandas()',
                         net_roundtrip.get_name())
        self.assertEqual(1, len(net_roundtrip.get_edges()))
        self.assertEqual(2, len(net_roundtrip.get_nodes()))
        self.assertEqual((0, {'@id': 0,
                              's': 0, 't': 1,
                              'i': 'interacts-with'}),
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
        net_df = net.to_pandas_dataframe(include_attributes=True)
        net_roundtrip = ndex2.create_nice_cx_from_pandas(net_df,
                                                         source_field='source',
                                                         target_field='target',
                                                         edge_interaction='interaction',
                                                         edge_attr=['somestrfield'],
                                                         source_node_attr=['source_somestrfield'])
        self.assertEqual('created from pandas by '
                         'ndex2.create_nice_cx_from_pandas()',
                         net_roundtrip.get_name())
        self.assertEqual(1, len(net_roundtrip.get_edges()))
        self.assertEqual(2, len(net_roundtrip.get_nodes()))

        self.assertEqual((0, {'@id': 0,
                              's': 0, 't': 1,
                              'i': 'breaks'}),
                         list(net_roundtrip.get_edges())[0], '\n\n' + str(net_df.head()))

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
                                               'source_somestrfield')
        self.assertEqual({'po': 0,
                          'n': 'source_somestrfield',
                          'v': 'hi', 'd': 'string'}, n_a)

        n_a = net_roundtrip.get_edge_attribute(node_one,
                                               'somestrfield')
        self.assertEqual({'po': 0,
                          'n': 'somestrfield',
                          'v': 'bye', 'd': 'string'}, n_a)

    def test_create_nice_cx_from_pandas_with_sif(self):
        data = {'source': ['Node 1', 'Node 2'],
                'target': ['Node 2', 'Node 3'],
                'interaction': ['helps', 'hurts']}
        df = pd.DataFrame.from_dict(data)
        net = ndex2.create_nice_cx_from_pandas(df)
        self.assertEqual(2, len(net.get_edges()))
        self.assertEqual(3, len(net.get_nodes()))
        for node_id, node in net.get_nodes():
                self.assertEqual({'@id': node_id,
                                  'n': 'Node ' + str(node_id+1),
                                  'r': 'Node ' + str(node_id+1)}, node)
        for edge_id, edge in net.get_edges():
            if edge_id == 0:
                self.assertEqual({'@id': 0,
                                  's': 0,
                                  't': 1,
                                  'i': 'helps'}, edge)
            elif edge_id == 1:
                self.assertEqual({'@id': 1,
                                  's': 1,
                                  't': 2,
                                  'i': 'hurts'}, edge)
            else:
                self.fail('Unexpected edge: ' + str(edge))
