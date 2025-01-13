import os
import unittest
import networkx as nx
from ndex2.cx2 import CX2NetworkXFactory, CX2Network
from ndex2.cx2 import NetworkXToCX2NetworkFactory


class TestCX2NetworkXFactory(unittest.TestCase):

    def get_networkx_major_version(self, networkx_version=nx.__version__):
        """
        Gets major version of networkx library

        :param networkx_version: raw version of networkx library
        :type networkx_version: str
        :return: major version of networkx assuming it will be in format of
                 MAJOR.MINOR or MAJOR.MINOR.PATCH...
                 or 0 if there was a problem
        :rtype: int
        """
        if networkx_version is None:
            return 0
        netx_ver_str = str(networkx_version)
        period_pos = netx_ver_str.find('.')
        if period_pos == -1:
            return 0
        try:
            return int(netx_ver_str[0:period_pos])
        except ValueError:
            return 0

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

        if (self.get_networkx_major_version()) == 1:
            self.assertEqual(len(graph.nodes()), 6)
            self.assertEqual(len(graph.edges()), 6)
        else:
            self.assertEqual(len(graph.nodes), 6)
            self.assertEqual(len(graph.edges), 6)

    def test_graph_creation_with_existing_graph(self):
        existing_graph = nx.MultiDiGraph()
        graph = self.factory.get_graph(self.cx2network, existing_graph)
        self.assertIs(graph, existing_graph)
        if (self.get_networkx_major_version()) == 1:
            self.assertEqual(len(graph.nodes()), 6)
            self.assertEqual(len(graph.edges()), 6)
        else:
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

    def test_empty_graph(self):
        """Test conversion of an empty NetworkX graph."""
        empty_graph = nx.MultiDiGraph()
        factory = NetworkXToCX2NetworkFactory()
        cx2_network = factory.get_cx2network(empty_graph)
        self.assertEqual(len(cx2_network.get_nodes()), 0)
        self.assertEqual(len(cx2_network.get_edges()), 0)

    def test_single_node_graph(self):
        """Test conversion of a graph with a single node."""
        single_node_graph = nx.MultiDiGraph()
        single_node_graph.add_node(1, name="Node1")
        factory = NetworkXToCX2NetworkFactory()
        cx2_network = factory.get_cx2network(single_node_graph)
        self.assertEqual(len(cx2_network.get_nodes()), 1)
        self.assertEqual(len(cx2_network.get_edges()), 0)
        node = cx2_network.get_node(1)
        self.assertIsNotNone(node)
        self.assertEqual(node["v"]["name"], "Node1")

    def test_graph_with_multiple_edges(self):
        """Test conversion of a graph with multiple edges between the same nodes."""
        graph = nx.MultiDiGraph()
        graph.add_edge(1, 2, interaction="activates")
        graph.add_edge(1, 2, interaction="inhibits")
        factory = NetworkXToCX2NetworkFactory()
        cx2_network = factory.get_cx2network(graph)
        self.assertEqual(len(cx2_network.get_edges()), 2)
        edges = list(cx2_network.get_edges().values())
        self.assertIn("activates", [e["v"]["interaction"] for e in edges])
        self.assertIn("inhibits", [e["v"]["interaction"] for e in edges])

    def test_graph_with_string_node_ids(self):
        """Test conversion of a graph with non-integer node IDs."""
        graph = nx.MultiDiGraph()
        graph.add_node("A")
        graph.add_node("B")
        graph.add_edge("A", "B", interaction="interacts-with")
        factory = NetworkXToCX2NetworkFactory()
        cx2_network = factory.get_cx2network(graph)
        self.assertEqual(len(cx2_network.get_nodes()), 2)
        self.assertEqual(len(cx2_network.get_edges()), 1)
        self.assertEqual(cx2_network.get_node(0)["v"]["name"], "A")

    def test_graph_with_layout_coordinates(self):
        """Test conversion of a graph with layout coordinates."""
        graph = nx.MultiDiGraph()
        graph.add_node(1, name="Node1", x=0.5, y=1.5, z=2.5)
        factory = NetworkXToCX2NetworkFactory()
        cx2_network = factory.get_cx2network(graph)
        node = cx2_network.get_node(1)
        self.assertEqual(node["x"], 0.5)
        self.assertEqual(node["y"], 1.5)
        self.assertEqual(node["z"], 2.5)

    def test_invalid_input_type(self):
        """Test passing an invalid input type."""
        with self.assertRaises(TypeError):
            factory = NetworkXToCX2NetworkFactory()
            factory.get_cx2network("invalid_type")

    def test_none_input(self):
        """Test passing None as input."""
        with self.assertRaises(Exception) as context:
            factory = NetworkXToCX2NetworkFactory()
            factory.get_cx2network(None)
        self.assertIn("Networkx input is empty", str(context.exception))

    def test_get_layout_from_pos(self):
        """Test the get_layout_from_pos parameter."""
        # Create a graph with position data
        graph = nx.MultiDiGraph()
        graph.add_node(1, name="Node1")
        graph.add_node(2, name="Node2")
        graph.add_edge(1, 2, interaction="interacts-with")

        # Add position information to the graph
        graph.pos = {
            1: (1.0, 2.0),
            2: (3.0, 4.0)
        }
        graph.zpos = {
            1: 5.0,
            2: 6.0
        }

        # Test with get_layout_from_pos=True
        factory = NetworkXToCX2NetworkFactory()
        cx2_network_with_layout = factory.get_cx2network(graph, get_layout_from_pos=True)

        node_1_with_layout = cx2_network_with_layout.get_node(1)
        node_2_with_layout = cx2_network_with_layout.get_node(2)

        # Ensure layout coordinates are extracted from graph.pos and graph.zpos
        self.assertEqual(node_1_with_layout["x"], 1.0)
        self.assertEqual(node_1_with_layout["y"], -2.0)  # Y-coordinates are inverted
        self.assertEqual(node_1_with_layout["z"], 5.0)
        self.assertEqual(node_2_with_layout["x"], 3.0)
        self.assertEqual(node_2_with_layout["y"], -4.0)
        self.assertEqual(node_2_with_layout["z"], 6.0)

    def test_empty_cx2_network(self):
        """Test conversion of an empty CX2Network to a NetworkX graph."""
        cx2_network = CX2Network()
        factory = CX2NetworkXFactory()
        graph = factory.get_graph(cx2_network)
        self.assertEqual(len(graph.nodes), 0)
        self.assertEqual(len(graph.edges), 0)

    def test_single_node_cx2_network(self):
        """Test conversion of a CX2Network with a single node to a NetworkX graph."""
        cx2_network = CX2Network()
        cx2_network.add_node(1, attributes={'name': 'Node1'})
        factory = CX2NetworkXFactory()
        graph = factory.get_graph(cx2_network)
        self.assertEqual(len(graph.nodes), 1)
        self.assertEqual(len(graph.edges), 0)
        self.assertIn(1, graph.nodes)
        self.assertEqual(graph.nodes[1]['name'], 'Node1')

    def test_nodes_with_layout_and_store_layout_in_pos(self):
        """Test storing layout in graph.pos and graph.zpos with store_layout_in_pos=True."""
        cx2_network = CX2Network()
        cx2_network.add_node(1, x=1.0, y=2.0, z=3.0)
        cx2_network.add_node(2, x=4.0, y=5.0, z=6.0)
        factory = CX2NetworkXFactory()
        graph = factory.get_graph(cx2_network, store_layout_in_pos=True)
        self.assertIn(1, graph.pos)
        self.assertIn(2, graph.pos)
        self.assertEqual(graph.pos[1], (1.0, -2.0))  # Y-coordinates inverted
        self.assertEqual(graph.zpos[1], 3.0)

    def test_nodes_with_layout_not_stored_in_pos(self):
        """Test layout coordinates are not stored in graph.pos when store_layout_in_pos=False."""
        cx2_network = CX2Network()
        cx2_network.add_node(1, x=1.0, y=2.0, z=3.0)
        factory = CX2NetworkXFactory()
        graph = factory.get_graph(cx2_network, store_layout_in_pos=False)
        self.assertNotIn(1, graph.pos)
        self.assertEqual(graph.nodes[1]['x'], 1.0)
        self.assertEqual(graph.nodes[1]['y'], 2.0)
        self.assertEqual(graph.nodes[1]['z'], 3.0)

    def test_edges_and_attributes(self):
        """Test conversion of edges and their attributes."""
        cx2_network = CX2Network()
        cx2_network.add_node(1, attributes={'name': 'Node1'})
        cx2_network.add_node(2, attributes={'name': 'Node2'})
        cx2_network.add_edge(source=1, target=2, attributes={'interaction': 'activates'})
        factory = CX2NetworkXFactory()
        graph = factory.get_graph(cx2_network)
        self.assertEqual(len(graph.edges), 1)
        self.assertTrue(graph.has_edge(1, 2))
        self.assertEqual(graph[1][2][0]['interaction'], 'activates')


if __name__ == '__main__':
    unittest.main()
