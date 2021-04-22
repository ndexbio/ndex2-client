# -*- coding: utf-8 -*-

"""Tests for `DefaultNetworkXFactory` class."""

import os
import unittest

import networkx
import ndex2
from ndex2.exceptions import NDExError
from ndex2.nice_cx_network import LegacyNetworkXVersionTwoPlusFactory
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
class TestLegacyNetworkXVersionTwoPlusFactory(unittest.TestCase):

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

    def test_none_passed_into_get_graph(self):
        fac = LegacyNetworkXVersionTwoPlusFactory()
        try:
            fac.get_graph(None)
            self.fail('Expected NDExError')
        except NDExError as ne:
            self.assertEqual('Input network is None', str(ne))

    @unittest.skipIf(NETWORKX_MAJOR_VERSION < 2,
                     'test only works with networkx 2+ installed')
    def test_empty_network_passed_in_with_various_legacy_modes(self):
        net = NiceCXNetwork()
        fac = LegacyNetworkXVersionTwoPlusFactory()
        g = fac.get_graph(net)
        self.assertTrue(isinstance(g, networkx.Graph))
        self.assertEqual(0, len(g))
        self.assertEqual(0, g.number_of_edges())

    @unittest.skipIf(NETWORKX_MAJOR_VERSION < 2,
                     'test only works with networkx 2+ installed')
    def test_one_node_no_edge_network(self):
        net = NiceCXNetwork()
        net.create_node('first')
        net.set_name('bob')
        fac = LegacyNetworkXVersionTwoPlusFactory()
        g = fac.get_graph(net)
        self.assertEqual('bob', g.graph['name'])
        self.assertEqual(1, len(g))
        self.assertEqual(0, g.number_of_edges())
        self.assertTrue('first' in g)
        nodelist = g.nodes(data=True)
        self.assertEqual('first', nodelist['first']['represents'])

    @unittest.skipIf(NETWORKX_MAJOR_VERSION < 2,
                     'test only works with networkx 2+ installed')
    def test_two_node_one_edge_network(self):
        net = NiceCXNetwork()
        net.create_node('first')
        net.create_node('second')
        net.create_edge(edge_source=0, edge_target=1)
        net.set_name('bob')
        fac = LegacyNetworkXVersionTwoPlusFactory()
        g = fac.get_graph(net)
        self.assertEqual('bob', g.graph['name'])
        self.assertEqual(2, len(g))
        self.assertEqual(1, g.number_of_edges())
        self.assertTrue('first' in g)
        self.assertTrue('second' in g)
        edgelist = list(g.edges(data=True))

        self.assertTrue(('first' == edgelist[0][0]
                         and 'second' == edgelist[0][1]) or
                        ('second' == edgelist[0][0]
                         and 'first' == edgelist[0][1]))
        self.assertEqual(None, edgelist[0][2]['interaction'])

    @unittest.skipIf(NETWORKX_MAJOR_VERSION < 2,
                     'test only works with networkx 2+ installed')
    def test_glypican_network_legacyfalse(self):
        net = ndex2\
            .create_nice_cx_from_file(TestLegacyNetworkXVersionTwoPlusFactory
                                      .GLYPICAN_FILE)
        fac = LegacyNetworkXVersionTwoPlusFactory()
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
        self.assertTrue('MDK' in g)
        self.assertTrue('GPC2' in g)
        nodelist = list(g.nodes(data=True))
        edgelist = list(g.edges(data=True))

        mdk = -1
        for i in range(0, len(nodelist)):
            if nodelist[i][0] == 'MDK':
                mdk = i
                break
        self.assertEqual('MDK', nodelist[mdk][0])
        self.assertEqual('Protein', nodelist[mdk][1]['type'])
        aliaslist = nodelist[mdk][1]['alias']
        self.assertEqual(2, len(aliaslist))
        self.assertTrue('uniprot knowledgebase:Q2LEK4' in aliaslist)
        self.assertTrue('uniprot knowledgebase:Q9UCC7' in aliaslist)

        gp = -1
        for i in range(0, len(nodelist)):
            if nodelist[i][0] == 'GPC2':
                gp = i
                break
        self.assertEqual('GPC2', nodelist[gp][0])
        self.assertEqual('Protein', nodelist[gp][1]['type'])
        aliaslist = nodelist[gp][1]['alias']
        self.assertEqual(1, len(aliaslist))
        self.assertTrue('uniprot knowledgebase:Q8N158' in aliaslist)

        self.assertTrue(('MDK' == edgelist[0][0] and 'GPC2',
                         edgelist[0][1]) or
                        ('GPC2' == edgelist[0][0] and 'MDK',
                         edgelist[0][1]))
        self.assertEqual('in-complex-with', edgelist[0][2]['interaction'])
        self.assertEqual('false', edgelist[0][2]['directed'])

        # check coordinates
        self.assertTrue((g.pos[0][0] + 398.3) < 1.0)
        self.assertTrue((g.pos[0][1] - 70.71) < 1.0)
        self.assertTrue((g.pos[1][0] + 353.49) < 1.0)
        self.assertTrue((g.pos[1][1] - 70.71) < 1.0)

    @unittest.skipIf(NETWORKX_MAJOR_VERSION < 2,
                     'test only works with networkx 2+ installed: ' +
                     networkx.__version__)
    def test_darktheme_network(self):
        net = ndex2\
            .create_nice_cx_from_file(TestLegacyNetworkXVersionTwoPlusFactory
                                      .DARKTHEME_FILE)
        fac = LegacyNetworkXVersionTwoPlusFactory()
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
        self.assertTrue('STAT3' in g)
        self.assertTrue('MAX' in g)

        nodelist = list(g.nodes(data=True))
        edgelist = list(g.edges(data=True))

        statthree = -1
        for i in range(0, len(nodelist)):
            if nodelist[i][0] == 'STAT3':
                statthree = i
                break

        self.assertEqual('STAT3', nodelist[statthree][0])
        self.assertEqual('protein', nodelist[statthree][1]['type'])
        self.assertEqual('uniprot:P40763',
                         nodelist[statthree][1]['represents'])

        stat_edge = -2
        for i in range(0, len(edgelist)):
            if edgelist[i][0] == 'STAT3' and edgelist[i][1] == 'JAK1/' \
                                                               'STAT1/STAT3':
                stat_edge = i
                break
            if edgelist[i][0] == 'JAK1/STAT1/' \
                                 'STAT3' and edgelist[i][1] == 'STAT3':
                stat_edge = i
                break
        self.assertTrue(stat_edge >= 0)
        self.assertEqual('form complex', edgelist[stat_edge][2]['interaction'])
        self.assertEqual('true', edgelist[stat_edge][2]['directed'])
        self.assertEqual('"pubmed:15284024"',
                         edgelist[stat_edge][2]['citation'])

        # check coordinates
        self.assertTrue((g.pos[1655][0] + 90.96) < 1.0)
        self.assertTrue((g.pos[1655][1] - 145.72) < 1.0)
