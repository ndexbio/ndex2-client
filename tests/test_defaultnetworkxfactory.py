# -*- coding: utf-8 -*-

"""Tests for `DefaultNetworkXFactory` class."""

import os
import unittest

import networkx
import ndex2
from ndex2.exceptions import NDExError
from ndex2.nice_cx_network import DefaultNetworkXFactory
from ndex2.nice_cx_network import NetworkXFactory
from ndex2.nice_cx_network import NiceCXNetwork

SKIP_REASON = 'NDEX2_TEST_USER environment variable detected, ' \
              'skipping for integration tests'


NETWORKX_MAJOR_VERSION = 0
netx_ver_str = str(networkx.__version__)
period_pos = netx_ver_str.index('.')
if period_pos != -1:
    try:
        NETWORKX_MAJOR_VERSION = int(netx_ver_str[0:period_pos])
    except ValueError:
        pass


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestDefaultNetworkXFactory(unittest.TestCase):

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

    def test_get_networkx_major_version(self):

        # try with no arg
        res = NetworkXFactory.get_networkx_major_version()
        self.assertTrue(res > 0)

        # try passing none
        res = NetworkXFactory.get_networkx_major_version(networkx_version=None)
        self.assertEqual(0, res)

        # try passing empty string
        res = NetworkXFactory.get_networkx_major_version(networkx_version='')
        self.assertEqual(0, res)

        # try passing string with no period
        res = NetworkXFactory.get_networkx_major_version(networkx_version='12')
        self.assertEqual(0, res)

        # try passing with only period
        res = NetworkXFactory.get_networkx_major_version(networkx_version='.')
        self.assertEqual(0, res)

        # try passing with non numeric value
        res = NetworkXFactory.get_networkx_major_version(networkx_version='fo')
        self.assertEqual(0, res)

        # try passing 1.11
        res = NetworkXFactory.get_networkx_major_version(networkx_version='1.11')
        self.assertEqual(1, res)

        # try passing 12.4.1b1
        res = NetworkXFactory.get_networkx_major_version(networkx_version='12.4.1b1')
        self.assertEqual(12, res)

    def test_none_passed_into_get_graph(self):
        fac = DefaultNetworkXFactory()
        try:
            fac.get_graph(None)
            self.fail('Expected NDExError')
        except NDExError as ne:
            self.assertEqual('input network is None', str(ne))

    def test_empty_network_passed_in_with_various_legacy_modes(self):
        net = NiceCXNetwork()
        fac = DefaultNetworkXFactory()
        g = fac.get_graph(net)
        self.assertTrue(isinstance(g, networkx.MultiGraph))
        self.assertEqual(0, len(g))
        self.assertEqual(0, g.number_of_edges())

        fac = DefaultNetworkXFactory(legacymode=True)
        g = fac.get_graph(net)
        self.assertTrue(isinstance(g, networkx.Graph))
        self.assertEqual(0, len(g))
        self.assertEqual(0, g.number_of_edges())

        fac = DefaultNetworkXFactory(legacymode=False)
        g = fac.get_graph(net)
        self.assertTrue(isinstance(g, networkx.MultiGraph))
        self.assertEqual(0, len(g))
        self.assertEqual(0, g.number_of_edges())

        fac = DefaultNetworkXFactory(legacymode=None)
        g = fac.get_graph(net)
        self.assertTrue(isinstance(g, networkx.MultiGraph))
        self.assertEqual(0, len(g))
        self.assertEqual(0, g.number_of_edges())

        try:
            DefaultNetworkXFactory(legacymode='blah')
            self.fail('Expected NDExError')
        except NDExError as ne:
            self.assertEqual('blah not a valid value for '
                             'legacymode parameter', str(ne))

    def test_one_node_no_edge_network(self):
        net = NiceCXNetwork()
        net.create_node('first')
        net.set_name('bob')
        fac = DefaultNetworkXFactory()
        g = fac.get_graph(net)
        self.assertEqual('bob', g.graph['name'])
        self.assertEqual(1, len(g))
        self.assertEqual(0, g.number_of_edges())
        self.assertTrue(0 in g)
        nodelist = g.nodes(data=True)
        if NETWORKX_MAJOR_VERSION >= 2:
            self.assertEqual('first', nodelist[0]['name'])
        else:
            self.assertEqual('first', nodelist[0][1]['name'])

        # TODO Fix Issue #51
        # network name is not properly set.
        # see https://github.com/ndexbio/ndex2-client/issues/51
        # net_two = ndex2.create_nice_cx_from_networkx(g)
        # self.assertEqual('bob', net_two.get_name())

    def test_one_node_no_edge_network_legacytrue(self):
        net = NiceCXNetwork()
        net.create_node('first')
        net.set_name('bob')
        fac = DefaultNetworkXFactory(legacymode=True)
        g = fac.get_graph(net)
        self.assertEqual('bob', g.graph['name'])
        self.assertEqual(1, len(g))
        self.assertEqual(0, g.number_of_edges())
        self.assertTrue(0 in g)

        if NETWORKX_MAJOR_VERSION >= 2:
            nodelist = list(g.nodes(data=True))
        else:
            nodelist = g.nodes(data=True)

        self.assertEqual('first', nodelist[0][1]['name'])

    def test_two_node_one_edge_network(self):
        net = NiceCXNetwork()
        net.create_node('first')
        net.create_node('second')
        net.create_edge(edge_source=0, edge_target=1)
        net.set_name('bob')
        fac = DefaultNetworkXFactory()
        g = fac.get_graph(net)
        self.assertEqual('bob', g.graph['name'])
        self.assertEqual(2, len(g))
        self.assertEqual(1, g.number_of_edges())
        self.assertTrue(0 in g)

        if NETWORKX_MAJOR_VERSION >= 2:
            nodelist = list(g.nodes(data=True))
            edgelist = list(g.edges(data=True))
        else:
            nodelist = g.nodes(data=True)
            edgelist = g.edges(data=True)

        self.assertEqual('first', nodelist[0][1]['name'])
        self.assertEqual('second', nodelist[1][1]['name'])
        self.assertEqual(0, edgelist[0][0])
        self.assertEqual(1, edgelist[0][1])
        self.assertEqual(None, edgelist[0][2]['interaction'])

    def test_glypican_network_legacyfalse_and_multigraph_passed_in(self):
        net = ndex2.create_nice_cx_from_file(TestDefaultNetworkXFactory
                                             .GLYPICAN_FILE)
        fac = DefaultNetworkXFactory()
        g = fac.get_graph(net, networkx_graph=networkx.MultiGraph())
        self.assertEqual('Glypican 2 network', g.graph['name'])
        self.assertEqual('', g.graph['reference'])
        self.assertEqual('Mirko von Elstermann', g.graph['author'])
        self.assertEqual('Jorge Filmus', g.graph['reviewers'])
        self.assertEqual('glypican_2pathway', g.graph['labels'])
        self.assertEqual('APR-2018', g.graph['version'])
        self.assertEqual('human', g.graph['organism'])

        self.assertEqual('<i>Glypican 2 network</i> was derived from '
                         'the latest BioPAX3 version of the Pathway '
                         'Interaction Database (PID) curated by NCI/Nature. '
                         'The BioPAX was first converted to Extended Binary '
                         'SIF (EBS) by the PAXTools v5 utility. It was then '
                         'processed to remove redundant edges, to add a '
                         '\'directed flow\' layout, and to add a graphic '
                         'style using Cytoscape Visual Properties. This '
                         'network can be found in searches using its original '
                         'PID accession id, present in the \'labels\' '
                         'property.', g.graph['description'])

        self.assertEqual(2, len(g))
        self.assertEqual(1, g.number_of_edges())
        self.assertTrue(0 in g)
        self.assertTrue(1 in g)
        if NETWORKX_MAJOR_VERSION >= 2:
            nodelist = list(g.nodes(data=True))
            edgelist = list(g.edges(data=True))
        else:
            nodelist = g.nodes(data=True)
            edgelist = g.edges(data=True)

        self.assertEqual('MDK', nodelist[0][1]['name'])
        self.assertEqual('Protein', nodelist[0][1]['type'])
        aliaslist = nodelist[0][1]['alias']
        self.assertEqual(2, len(aliaslist))
        self.assertTrue('uniprot knowledgebase:Q2LEK4' in aliaslist)
        self.assertTrue('uniprot knowledgebase:Q9UCC7' in aliaslist)

        self.assertEqual('GPC2', nodelist[1][1]['name'])
        self.assertEqual('Protein', nodelist[1][1]['type'])
        aliaslist = nodelist[1][1]['alias']
        self.assertEqual(1, len(aliaslist))
        self.assertTrue('uniprot knowledgebase:Q8N158' in aliaslist)

        self.assertEqual(0, edgelist[0][0])
        self.assertEqual(1, edgelist[0][1])
        self.assertEqual('in-complex-with', edgelist[0][2]['interaction'])
        self.assertEqual('false', edgelist[0][2]['directed'])

        # check coordinates
        self.assertTrue((g.pos[0][0] + 398.3) < 1.0)
        self.assertTrue((g.pos[0][1] - 70.71) < 1.0)
        self.assertTrue((g.pos[1][0] + 353.49) < 1.0)
        self.assertTrue((g.pos[1][1] - 70.71) < 1.0)

    def test_glypican_network_legacyfalse(self):
        net = ndex2.create_nice_cx_from_file(TestDefaultNetworkXFactory
                                             .GLYPICAN_FILE)
        fac = DefaultNetworkXFactory()
        g = fac.get_graph(net)
        self.assertEqual('Glypican 2 network', g.graph['name'])
        self.assertEqual('', g.graph['reference'])
        self.assertEqual('Mirko von Elstermann', g.graph['author'])
        self.assertEqual('Jorge Filmus', g.graph['reviewers'])
        self.assertEqual('glypican_2pathway', g.graph['labels'])
        self.assertEqual('APR-2018', g.graph['version'])
        self.assertEqual('human', g.graph['organism'])

        self.assertEqual('<i>Glypican 2 network</i> was derived from '
                         'the latest BioPAX3 version of the Pathway '
                         'Interaction Database (PID) curated by NCI/Nature. '
                         'The BioPAX was first converted to Extended Binary '
                         'SIF (EBS) by the PAXTools v5 utility. It was then '
                         'processed to remove redundant edges, to add a '
                         '\'directed flow\' layout, and to add a graphic '
                         'style using Cytoscape Visual Properties. This '
                         'network can be found in searches using its original '
                         'PID accession id, present in the \'labels\' '
                         'property.', g.graph['description'])

        self.assertEqual(2, len(g))
        self.assertEqual(1, g.number_of_edges())
        self.assertTrue(0 in g)
        self.assertTrue(1 in g)
        if NETWORKX_MAJOR_VERSION >= 2:
            nodelist = list(g.nodes(data=True))
            edgelist = list(g.edges(data=True))
        else:
            nodelist = g.nodes(data=True)
            edgelist = g.edges(data=True)

        self.assertEqual('MDK', nodelist[0][1]['name'])
        self.assertEqual('Protein', nodelist[0][1]['type'])
        aliaslist = nodelist[0][1]['alias']
        self.assertEqual(2, len(aliaslist))
        self.assertTrue('uniprot knowledgebase:Q2LEK4' in aliaslist)
        self.assertTrue('uniprot knowledgebase:Q9UCC7' in aliaslist)

        self.assertEqual('GPC2', nodelist[1][1]['name'])
        self.assertEqual('Protein', nodelist[1][1]['type'])
        aliaslist = nodelist[1][1]['alias']
        self.assertEqual(1, len(aliaslist))
        self.assertTrue('uniprot knowledgebase:Q8N158' in aliaslist)
        self.assertEqual(1, edgelist[0][0])
        self.assertEqual(0, edgelist[0][1])
        self.assertEqual('in-complex-with', edgelist[0][2]['interaction'])
        self.assertEqual('false', edgelist[0][2]['directed'])

        # check coordinates
        self.assertTrue((g.pos[0][0] + 398.3) < 1.0)
        self.assertTrue((g.pos[0][1] - 70.71) < 1.0)
        self.assertTrue((g.pos[1][0] + 353.49) < 1.0)
        self.assertTrue((g.pos[1][1] - 70.71) < 1.0)

    def test_glypican_network_legacymode_true(self):
        net = ndex2.create_nice_cx_from_file(TestDefaultNetworkXFactory
                                             .GLYPICAN_FILE)
        fac = DefaultNetworkXFactory(legacymode=True)
        g = fac.get_graph(net)
        self.assertTrue(isinstance(g, networkx.Graph))
        self.assertEqual('Glypican 2 network', g.graph['name'])
        self.assertEqual('', g.graph['reference'])
        self.assertEqual('Mirko von Elstermann', g.graph['author'])
        self.assertEqual('Jorge Filmus', g.graph['reviewers'])
        self.assertEqual('glypican_2pathway', g.graph['labels'])
        self.assertEqual('APR-2018', g.graph['version'])
        self.assertEqual('human', g.graph['organism'])

        self.assertEqual('<i>Glypican 2 network</i> was derived from '
                         'the latest BioPAX3 version of the Pathway '
                         'Interaction Database (PID) curated by NCI/Nature. '
                         'The BioPAX was first converted to Extended Binary '
                         'SIF (EBS) by the PAXTools v5 utility. It was then '
                         'processed to remove redundant edges, to add a '
                         '\'directed flow\' layout, and to add a graphic '
                         'style using Cytoscape Visual Properties. This '
                         'network can be found in searches using its original '
                         'PID accession id, present in the \'labels\' '
                         'property.', g.graph['description'])

        self.assertEqual(2, len(g))
        self.assertEqual(1, g.number_of_edges())
        self.assertTrue(0 in g)
        self.assertTrue(1 in g)

        if NETWORKX_MAJOR_VERSION >= 2:
            nodelist = list(g.nodes(data=True))
            edgelist = list(g.edges(data=True))
        else:
            nodelist = g.nodes(data=True)
            edgelist = g.edges(data=True)

        self.assertEqual('MDK', nodelist[0][1]['name'])
        self.assertEqual('Protein', nodelist[0][1]['type'])
        aliaslist = nodelist[0][1]['alias']
        self.assertEqual(2, len(aliaslist))
        self.assertTrue('uniprot knowledgebase:Q2LEK4' in aliaslist)
        self.assertTrue('uniprot knowledgebase:Q9UCC7' in aliaslist)

        self.assertEqual('GPC2', nodelist[1][1]['name'])
        self.assertEqual('Protein', nodelist[1][1]['type'])
        aliaslist = nodelist[1][1]['alias']
        self.assertEqual(1, len(aliaslist))
        self.assertTrue('uniprot knowledgebase:Q8N158' in aliaslist)

        self.assertEqual(0, edgelist[0][0])
        self.assertEqual(1, edgelist[0][1])
        self.assertEqual('in-complex-with', edgelist[0][2]['interaction'])
        self.assertEqual('false', edgelist[0][2]['directed'])

        # check coordinates
        self.assertTrue((g.pos[0][0] + 398.3) < 1.0)
        self.assertTrue((g.pos[0][1] - 70.71) < 1.0)
        self.assertTrue((g.pos[1][0] + 353.49) < 1.0)
        self.assertTrue((g.pos[1][1] - 70.71) < 1.0)

    def test_darktheme_network_legacyfalse(self):
        net = ndex2.create_nice_cx_from_file(TestDefaultNetworkXFactory
                                             .DARKTHEME_FILE)
        fac = DefaultNetworkXFactory()
        g = fac.get_graph(net)
        self.assertEqual('Dark theme final version', g.graph['name'])
        self.assertTrue('Perfetto L.,' in g.graph['reference'])
        self.assertEqual('Theodora Pavlidou', g.graph['author'])
        self.assertEqual('SIGNOR-EGF', g.graph['labels'])
        self.assertEqual('18-Jan-2019', g.graph['version'])
        self.assertEqual('Human, 9606, Homo sapiens', g.graph['organism'])
        self.assertEqual('SIGNOR-EGF', g.graph['labels'])
        self.assertTrue('epidermal growth factor' in g.graph['description'])

        self.assertEqual(34, len(g))
        self.assertEqual(116, g.number_of_edges())
        self.assertTrue(1655 in g)
        self.assertTrue(1622 in g)

        if NETWORKX_MAJOR_VERSION >= 2:
            nodelist = list(g.nodes(data=True))
            edgelist = list(g.edges(data=True))
        else:
            nodelist = g.nodes(data=True)
            edgelist = g.edges(data=True)

        stat_three_index = -1
        for i in range(0, len(nodelist)):
            if nodelist[i][1]['name'] == 'STAT3':
                stat_three_index = i
                break
        self.assertEqual('STAT3', nodelist[stat_three_index][1]['name'])
        self.assertEqual('protein', nodelist[stat_three_index][1]['type'])
        self.assertEqual('uniprot:P40763',
                         nodelist[stat_three_index][1]['represents'])

        sixteenfiftyfiveedge = -1
        for i in range(len(edgelist)):
            if edgelist[i][0] == 1655 and edgelist[i][1] == 1654:
                sixteenfiftyfiveedge = i
                break

        self.assertTrue((1655 == edgelist[sixteenfiftyfiveedge][0] and
                        1654 == edgelist[sixteenfiftyfiveedge][1]) or
                        (1654 == edgelist[sixteenfiftyfiveedge][0] and
                         1655 == edgelist[sixteenfiftyfiveedge][1]))

        self.assertEqual('form complex',
                         edgelist[sixteenfiftyfiveedge][2]['interaction'])
        self.assertEqual('true', edgelist[sixteenfiftyfiveedge][2]['directed'])
        self.assertEqual('"pubmed:15284024"',
                         edgelist[sixteenfiftyfiveedge][2]['citation'])

        # check coordinates
        self.assertTrue((g.pos[1655][0] + 90.96) < 1.0)
        self.assertTrue((g.pos[1655][1] - 145.72) < 1.0)

    def test_darktheme_network_legacytrue(self):
        net = ndex2\
            .create_nice_cx_from_file(TestDefaultNetworkXFactory
                                      .DARKTHEME_FILE)
        fac = DefaultNetworkXFactory(legacymode=True)
        g = fac.get_graph(net)
        self.assertEqual('Dark theme final version', g.graph['name'])
        self.assertTrue('Perfetto L.,' in g.graph['reference'])
        self.assertEqual('Theodora Pavlidou', g.graph['author'])
        self.assertEqual('SIGNOR-EGF', g.graph['labels'])
        self.assertEqual('18-Jan-2019', g.graph['version'])
        self.assertEqual('Human, 9606, Homo sapiens', g.graph['organism'])
        self.assertEqual('SIGNOR-EGF', g.graph['labels'])
        self.assertTrue('epidermal growth factor' in g.graph['description'])

        self.assertEqual(34, len(g))
        self.assertEqual(50, g.number_of_edges())
        self.assertTrue(1655 in g)
        self.assertTrue(1622 in g)

        if NETWORKX_MAJOR_VERSION >= 2:
            nodelist = list(g.nodes(data=True))
            edgelist = list(g.edges(data=True))
        else:
            nodelist = g.nodes(data=True)
            edgelist = g.edges(data=True)

        stat_three_index = -1
        for i in range(0, len(nodelist)):
            if nodelist[i][1]['name'] == 'STAT3':
                stat_three_index = i
                break
        self.assertEqual('STAT3', nodelist[stat_three_index][1]['name'])
        self.assertEqual('protein', nodelist[stat_three_index][1]['type'])
        self.assertTrue('represents' not in nodelist[stat_three_index][1])

        sixteenfiftyfiveedge = -1
        for i in range(len(edgelist)):
            if edgelist[i][0] == 1655 and edgelist[i][1] == 1654:
                sixteenfiftyfiveedge = i
                break

        self.assertTrue((1655 == edgelist[sixteenfiftyfiveedge][0] and
                         1654 == edgelist[sixteenfiftyfiveedge][1]) or
                        (1654 == edgelist[sixteenfiftyfiveedge][0] and
                         1655 == edgelist[sixteenfiftyfiveedge][1]))

        self.assertEqual('form complex',
                         edgelist[sixteenfiftyfiveedge][2]['interaction'])
        self.assertEqual('true', edgelist[sixteenfiftyfiveedge][2]['directed'])
        self.assertEqual('"pubmed:15284024"',
                         edgelist[sixteenfiftyfiveedge][2]['citation'])

        # check coordinates
        self.assertTrue((g.pos[1655][0] + 90.96) < 1.0)
        self.assertTrue((g.pos[1655][1] - 145.72) < 1.0)
