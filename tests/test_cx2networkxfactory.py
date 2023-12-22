import os
import unittest
import networkx as nx
from ndex2.cx2 import CX2NetworkXFactory, CX2Network
from ndex2.cx2 import NetworkXToCX2NetworkFactory


class TestCX2NetworkXFactory(unittest.TestCase):

    def get_node_matching_name(self, cx2net=None, name=None):
        """
        Gets 1st node matching name

        :param cx2net:
        :param name:
        :return:
        """
        for node_id, node_obj in cx2net.get_nodes().items():
            if 'v' not in node_obj:
                continue
            if 'name' not in node_obj['v']:
                continue
            if node_obj['v']['name'] == name:
                return node_obj
        return None

    def get_edge_matching_name(self, cx2net=None, name=None):
        """

        :param cx2net:
        :param name:
        :return:
        """
        for edge_id, edge_obj in cx2net.get_edges().items():
            if 'v' not in edge_obj:
                continue
            if 'name' not in edge_obj['v']:
                continue
            if edge_obj['v']['name'] == name:
                return edge_obj
        return None

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

    def test_roundtrip(self):
        graph = self.factory.get_graph(self.cx2network)
        fac = NetworkXToCX2NetworkFactory()
        rt_cx2net = fac.get_cx2network(graph)

        for node_name in ['721', '737', '747', '751', '753', '764']:
            rt_node = self.get_node_matching_name(cx2net=rt_cx2net, name=node_name)
            orig_node = self.get_node_matching_name(cx2net=self.cx2network, name=node_name)
            import json
            print('\nComparing original node with node roundtripped through networkx\n')
            print(json.dumps(orig_node, indent=2))
            print('------------------------\n')
            print(json.dumps(rt_node, indent=2))
            print(rt_node)
            print('\n\n\n\n\n\n\n\n\n\n\n')
            self.assertEqual(rt_node['v'], orig_node['v'])
            self.assertAlmostEqual(rt_node['x'], orig_node['x'], 0.001)
            self.assertAlmostEqual(rt_node['y'], orig_node['y'], 0.001)
            self.assertEqual(rt_node['z'], orig_node['z'])

        for edge_name in ['753 (interacts with) 751',
                          '747 (interacts with) 721',
                          '751 (interacts with) 721',
                          '751 (interacts with) 737',
                          '764 (interacts with) 747',
                          '764 (interacts with) 753']:
            orig_edge = self.get_edge_matching_name(cx2net=self.cx2network, name=edge_name)
            rt_edge = self.get_edge_matching_name(cx2net=rt_cx2net, name=edge_name)
            self.assertIsNotNone(orig_edge, edge_name)
            self.assertIsNotNone(rt_edge)
            self.assertEqual(rt_edge['v'], orig_edge['v'])


if __name__ == '__main__':
    unittest.main()
