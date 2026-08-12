import unittest
import tempfile
import os
from ndex2.cx2 import CX2Network, SIFToCX2NetworkFactory, CX2NetworkSIFFactory
from ndex2.exceptions import NDExError, NDExInvalidCX2Error
from ndex2 import constants


class TestSIFToCX2NetworkFactory(unittest.TestCase):
    """Test SIF to CX2Network conversion"""

    def setUp(self):
        self.factory = SIFToCX2NetworkFactory()

    def test_basic_sif_conversion(self):
        """Test basic SIF conversion with tab delimiters"""
        sif_content = "GeneA\tactivates\tGeneB\tGeneC\nGeneD\tinhibits\tGeneE"

        cx2_network = self.factory.get_cx2network(sif_content)

        # Check nodes
        nodes = cx2_network.get_nodes()
        self.assertEqual(len(nodes), 5)  # GeneA, GeneB, GeneC, GeneD, GeneE

        # Check edges
        edges = cx2_network.get_edges()
        self.assertEqual(len(edges), 3)  # GeneA->GeneB, GeneA->GeneC, GeneD->GeneE

        # Verify node names
        node_names = {}
        for node_id, node in nodes.items():
            name = node.get(constants.ASPECT_VALUES, {}).get(constants.NODE_NAME_EXPANDED)
            node_names[node_id] = name

        # Verify edge interactions
        edge_interactions = {}
        for edge_id, edge in edges.items():
            interaction = edge.get(constants.ASPECT_VALUES, {}).get(constants.EDGE_INTERACTION_EXPANDED)
            source_id = edge.get(constants.EDGE_SOURCE)
            target_id = edge.get(constants.EDGE_TARGET)
            edge_interactions[(source_id, target_id)] = interaction

        # Check specific interactions
        gene_a_id = [k for k, v in node_names.items() if v == 'GeneA'][0]
        gene_b_id = [k for k, v in node_names.items() if v == 'GeneB'][0]
        gene_c_id = [k for k, v in node_names.items() if v == 'GeneC'][0]
        gene_d_id = [k for k, v in node_names.items() if v == 'GeneD'][0]
        gene_e_id = [k for k, v in node_names.items() if v == 'GeneE'][0]

        self.assertEqual(edge_interactions.get((gene_a_id, gene_b_id)), 'activates')
        self.assertEqual(edge_interactions.get((gene_a_id, gene_c_id)), 'activates')
        self.assertEqual(edge_interactions.get((gene_d_id, gene_e_id)), 'inhibits')

    def test_space_delimited_sif(self):
        """Test SIF conversion with space delimiters"""
        sif_content = "GeneA activates GeneB\nGeneC inhibits GeneD"

        cx2_network = self.factory.get_cx2network(sif_content)

        nodes = cx2_network.get_nodes()
        edges = cx2_network.get_edges()

        self.assertEqual(len(nodes), 4)
        self.assertEqual(len(edges), 2)

    def test_isolated_nodes(self):
        """Test SIF with isolated nodes"""
        sif_content = "GeneA\tactivates\tGeneB\nGeneC\nGeneD\tinhibits\tGeneE"

        cx2_network = self.factory.get_cx2network(sif_content)

        nodes = cx2_network.get_nodes()
        edges = cx2_network.get_edges()

        self.assertEqual(len(nodes), 5)  # GeneA, GeneB, GeneC, GeneD, GeneE
        self.assertEqual(len(edges), 2)  # GeneA->GeneB, GeneD->GeneE

    def test_self_edges(self):
        """Test SIF with self-edges"""
        sif_content = "GeneA\tactivates\tGeneA\nGeneB\tinhibits\tGeneB"

        cx2_network = self.factory.get_cx2network(sif_content)

        nodes = cx2_network.get_nodes()
        edges = cx2_network.get_edges()

        self.assertEqual(len(nodes), 2)  # GeneA, GeneB
        self.assertEqual(len(edges), 2)  # GeneA->GeneA, GeneB->GeneB

    def test_file_input(self):
        """Test SIF conversion from file"""
        sif_content = "GeneA\tactivates\tGeneB\nGeneC\tinhibits\tGeneD"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.sif', delete=False) as f:
            f.write(sif_content)
            temp_file = f.name

        try:
            cx2_network = self.factory.get_cx2network(temp_file)

            nodes = cx2_network.get_nodes()
            edges = cx2_network.get_edges()

            self.assertEqual(len(nodes), 4)
            self.assertEqual(len(edges), 2)
        finally:
            os.unlink(temp_file)

    def test_empty_input(self):
        """Test empty input handling"""
        with self.assertRaises(NDExError):
            self.factory.get_cx2network(None)

        with self.assertRaises(NDExError):
            self.factory.get_cx2network("")

    def test_invalid_sif_format(self):
        """Test invalid SIF format handling"""
        with self.assertRaises(NDExError):
            self.factory.get_cx2network("\t\t")  # Empty source node

        # Test with malformed line that has too few parts for an interaction
        with self.assertRaises(NDExInvalidCX2Error):
            self.factory.get_cx2network("GeneA\tinteraction")  # Has interaction but no target

    def test_comments_and_empty_lines(self):
        """Test handling of comments and empty lines"""
        sif_content = "# This is a comment\n\nGeneA\tactivates\tGeneB\n# Another comment\nGeneC\tinhibits\tGeneD"

        cx2_network = self.factory.get_cx2network(sif_content)

        nodes = cx2_network.get_nodes()
        edges = cx2_network.get_edges()

        self.assertEqual(len(nodes), 4)
        self.assertEqual(len(edges), 2)

    def test_default_interaction(self):
        """Test default interaction type"""
        sif_content = "GeneA\t\tGeneB\nGeneC\t\tGeneD"  # Empty interaction

        cx2_network = self.factory.get_cx2network(sif_content, default_interaction='interacts-with')

        edges = cx2_network.get_edges()
        for edge_id, edge in edges.items():
            interaction = edge.get(constants.ASPECT_VALUES, {}).get(constants.EDGE_INTERACTION_EXPANDED)
            self.assertEqual(interaction, 'interacts-with')


class TestCX2NetworkSIFFactory(unittest.TestCase):
    """Test CX2Network to SIF conversion"""

    def setUp(self):
        self.factory = CX2NetworkSIFFactory()

    def test_basic_cx2_to_sif(self):
        """Test basic CX2Network to SIF conversion"""
        cx2_network = CX2Network()

        # Add nodes
        node1 = cx2_network.add_node(attributes={constants.NODE_NAME_EXPANDED: 'GeneA'})
        node2 = cx2_network.add_node(attributes={constants.NODE_NAME_EXPANDED: 'GeneB'})
        node3 = cx2_network.add_node(attributes={constants.NODE_NAME_EXPANDED: 'GeneC'})

        # Add edges
        cx2_network.add_edge(source=node1, target=node2,
                             attributes={constants.EDGE_INTERACTION_EXPANDED: 'activates'})
        cx2_network.add_edge(source=node1, target=node3,
                             attributes={constants.EDGE_INTERACTION_EXPANDED: 'activates'})

        sif_content = self.factory.get_sif(cx2_network)

        # Check that the output contains expected lines
        lines = sif_content.strip().split('\n')
        self.assertEqual(len(lines), 1)  # One line with multiple targets

        # Check the line format
        expected_line = "GeneA\tactivates\tGeneB\tGeneC"
        self.assertEqual(lines[0], expected_line)

    def test_multiple_interactions(self):
        """Test CX2Network with multiple interaction types"""
        cx2_network = CX2Network()

        # Add nodes
        node1 = cx2_network.add_node(attributes={constants.NODE_NAME_EXPANDED: 'GeneA'})
        node2 = cx2_network.add_node(attributes={constants.NODE_NAME_EXPANDED: 'GeneB'})
        node3 = cx2_network.add_node(attributes={constants.NODE_NAME_EXPANDED: 'GeneC'})

        # Add edges with different interactions
        cx2_network.add_edge(source=node1, target=node2,
                             attributes={constants.EDGE_INTERACTION_EXPANDED: 'activates'})
        cx2_network.add_edge(source=node1, target=node3,
                             attributes={constants.EDGE_INTERACTION_EXPANDED: 'inhibits'})

        sif_content = self.factory.get_sif(cx2_network)

        lines = sif_content.strip().split('\n')
        self.assertEqual(len(lines), 2)  # Two lines with different interactions

        # Check that both interactions are present
        self.assertTrue(any('activates' in line for line in lines))
        self.assertTrue(any('inhibits' in line for line in lines))

    def test_isolated_nodes(self):
        """Test CX2Network with isolated nodes"""
        cx2_network = CX2Network()

        # Add nodes
        node1 = cx2_network.add_node(attributes={constants.NODE_NAME_EXPANDED: 'GeneA'})
        node2 = cx2_network.add_node(attributes={constants.NODE_NAME_EXPANDED: 'GeneB'})
        node3 = cx2_network.add_node(attributes={constants.NODE_NAME_EXPANDED: 'GeneC'})

        # Add only one edge
        cx2_network.add_edge(source=node1, target=node2,
                             attributes={constants.EDGE_INTERACTION_EXPANDED: 'activates'})

        sif_content = self.factory.get_sif(cx2_network)

        lines = sif_content.strip().split('\n')
        self.assertEqual(len(lines), 2)  # One interaction line + one isolated node

        # Check that isolated node is present
        self.assertTrue(any('GeneC' in line and '\t' not in line for line in lines))

    def test_self_edges(self):
        """Test CX2Network with self-edges"""
        cx2_network = CX2Network()

        # Add node
        node1 = cx2_network.add_node(attributes={constants.NODE_NAME_EXPANDED: 'GeneA'})

        # Add self-edge
        cx2_network.add_edge(source=node1, target=node1,
                             attributes={constants.EDGE_INTERACTION_EXPANDED: 'activates'})

        sif_content = self.factory.get_sif(cx2_network)

        lines = sif_content.strip().split('\n')
        self.assertEqual(len(lines), 1)

        # Check self-edge format
        expected_line = "GeneA\tactivates\tGeneA"
        self.assertEqual(lines[0], expected_line)

    def test_default_interaction(self):
        """Test CX2Network with default interaction"""
        cx2_network = CX2Network()

        # Add nodes
        node1 = cx2_network.add_node(attributes={constants.NODE_NAME_EXPANDED: 'GeneA'})
        node2 = cx2_network.add_node(attributes={constants.NODE_NAME_EXPANDED: 'GeneB'})

        # Add edge without interaction
        cx2_network.add_edge(source=node1, target=node2, attributes={})

        sif_content = self.factory.get_sif(cx2_network, default_interaction='interacts-with')

        lines = sif_content.strip().split('\n')
        self.assertEqual(len(lines), 1)

        # Check default interaction
        expected_line = "GeneA\tinteracts-with\tGeneB"
        self.assertEqual(lines[0], expected_line)

    def test_file_output(self):
        """Test SIF output to file"""
        cx2_network = CX2Network()

        # Add nodes and edge
        node1 = cx2_network.add_node(attributes={constants.NODE_NAME_EXPANDED: 'GeneA'})
        node2 = cx2_network.add_node(attributes={constants.NODE_NAME_EXPANDED: 'GeneB'})
        cx2_network.add_edge(source=node1, target=node2,
                             attributes={constants.EDGE_INTERACTION_EXPANDED: 'activates'})

        with tempfile.NamedTemporaryFile(mode='w', suffix='.sif', delete=False) as f:
            temp_file = f.name

        try:
            # Write to file
            self.factory.get_sif(cx2_network, output_file=temp_file)

            # Read back and verify
            with open(temp_file, 'r') as f:
                content = f.read().strip()

            expected_content = "GeneA\tactivates\tGeneB"
            self.assertEqual(content, expected_content)
        finally:
            os.unlink(temp_file)

    def test_empty_network(self):
        """Test empty CX2Network"""
        cx2_network = CX2Network()

        sif_content = self.factory.get_sif(cx2_network)

        # Should return empty string
        self.assertEqual(sif_content.strip(), "")

    def test_none_input(self):
        """Test None input handling"""
        with self.assertRaises(NDExError):
            self.factory.get_sif(None)

    def test_invalid_input_type(self):
        """Test invalid input type handling"""
        with self.assertRaises(NDExError):
            self.factory.get_sif("not a network")


class TestSIFRoundTrip(unittest.TestCase):
    """Test round-trip conversion: SIF -> CX2Network -> SIF"""

    def test_round_trip_basic(self):
        """Test basic round-trip conversion"""
        original_sif = "GeneA\tactivates\tGeneB\tGeneC\nGeneD\tinhibits\tGeneE"

        # SIF -> CX2Network
        sif_factory = SIFToCX2NetworkFactory()
        cx2_network = sif_factory.get_cx2network(original_sif)

        # CX2Network -> SIF
        cx2_factory = CX2NetworkSIFFactory()
        converted_sif = cx2_factory.get_sif(cx2_network)

        # Parse both SIFs and compare
        original_lines = set(original_sif.strip().split('\n'))
        converted_lines = set(converted_sif.strip().split('\n'))

        self.assertEqual(original_lines, converted_lines)

    def test_round_trip_with_isolated_nodes(self):
        """Test round-trip conversion with isolated nodes"""
        original_sif = "GeneA\tactivates\tGeneB\nGeneC\nGeneD\tinhibits\tGeneE"

        # SIF -> CX2Network
        sif_factory = SIFToCX2NetworkFactory()
        cx2_network = sif_factory.get_cx2network(original_sif)

        # CX2Network -> SIF
        cx2_factory = CX2NetworkSIFFactory()
        converted_sif = cx2_factory.get_sif(cx2_network)

        # Parse both SIFs and compare
        original_lines = set(original_sif.strip().split('\n'))
        converted_lines = set(converted_sif.strip().split('\n'))

        self.assertEqual(original_lines, converted_lines)


if __name__ == '__main__':
    unittest.main()