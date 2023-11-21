import os
import unittest
import networkx as nx
from ndex2.cx2 import CX2NetworkXFactory, CX2Network


class TestCX2NetworkXFactory(unittest.TestCase):

    def setUp(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.sample_file = os.path.join(current_dir, 'data', 'demo.cx2')
        self.cx2network = CX2Network()
        self.cx2network.create_from_raw_cx2(self.sample_file)
        self.factory = CX2NetworkXFactory()

    def test_graph_creation_without_existing_graph(self):
        graph = self.factory.get_graph(self.cx2network)
        self.assertIsInstance(graph, nx.MultiDiGraph)
        self.assertEqual(len(graph.nodes), 6)
        self.assertEqual(len(graph.edges), 6)

    def test_graph_creation_with_existing_graph(self):
        existing_graph = nx.MultiDiGraph()
        graph = self.factory.get_graph(self.cx2network, existing_graph)
        self.assertIs(graph, existing_graph)
        self.assertEqual(len(graph.nodes), 6)
        self.assertEqual(len(graph.edges), 6)

    def test_node_attributes(self):
        graph = self.factory.get_graph(self.cx2network)
        for node_id, node_data in graph.nodes(data=True):
            self.assertIn('name', node_data)

    def test_edge_attributes(self):
        graph = self.factory.get_graph(self.cx2network)
        for _, _, edge_data in graph.edges(data=True):
            self.assertIn('interaction', edge_data)

    def test_network_attributes(self):
        graph = self.factory.get_graph(self.cx2network)
        self.assertIn('name', graph.graph)
        self.assertEqual(graph.graph['name'], 'DLoc Hierarchy demo')


if __name__ == '__main__':
    unittest.main()
