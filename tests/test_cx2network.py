import unittest
import os
import json
import tempfile
import shutil
from ndex2.cx2 import CX2Network, convert_value, NoStyleCXToCX2NetworkFactory


class TestCX2Network(unittest.TestCase):

    def setUp(self):
        self.cx2_obj = CX2Network()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.sample_file = os.path.join(current_dir, 'data', 'demo.cx2')
        self.cx_file = os.path.join(current_dir, 'data', 'glypican2.cx')

    def test_create_from_raw_cx2_from_file(self):
        self.cx2_obj.create_from_raw_cx2(self.sample_file)
        self.assertIsNotNone(self.cx2_obj.get_attribute_declarations())
        self.assertGreater(len(self.cx2_obj.get_nodes()), 0)

    def test_create_from_raw_cx2_from_list(self):
        with open(self.sample_file, 'r') as f:
            data_list = json.load(f)
        self.cx2_obj.create_from_raw_cx2(data_list)
        self.assertIsNotNone(self.cx2_obj.get_attribute_declarations())
        self.assertGreater(len(self.cx2_obj.get_nodes()), 0)

    def test_invalid_input_create_from_raw_cx2(self):
        with self.assertRaises(ValueError):
            self.cx2_obj.create_from_raw_cx2(12345)

    def test_write_as_raw_cx2(self):
        temp_dir = tempfile.mkdtemp()

        try:
            test_out = os.path.join(temp_dir, 'test_output.cx2')
            self.cx2_obj.create_from_raw_cx2(self.sample_file)

            self.cx2_obj.write_as_raw_cx2(test_out)
            self.assertTrue(os.path.exists(test_out))

            with open(test_out, 'r') as f:
                data = json.load(f)
                self.assertIn("CXVersion", data[0])
        finally:
            shutil.rmtree(temp_dir)

    def test_to_cx2(self):
        self.cx2_obj.create_from_raw_cx2(self.sample_file)
        cx2_data = self.cx2_obj.to_cx2()

        self.assertIsInstance(cx2_data, list)
        self.assertIn("CXVersion", cx2_data[0])

        aspect_names = [list(item.keys())[0] for item in cx2_data]
        self.assertIn("attributeDeclarations", aspect_names)
        self.assertIn("nodes", aspect_names)
        self.assertIn("edges", aspect_names)

    def test_convert_value(self):
        self.assertEqual(convert_value("integer", "42"), 42)
        self.assertEqual(convert_value("double", "42.42"), 42.42)
        self.assertEqual(convert_value("boolean", "true"), True)

    def test_replace_with_alias(self):
        self.cx2_obj._attribute_declarations = {
            'nodes': {
                'original1': {'a': 'alias1'}
            }
        }
        data = [{'id': 1, 'v': {'original1': 'value1'}}]
        transformed_data = self.cx2_obj._replace_with_alias(data, 'nodes')
        self.assertEqual(transformed_data[0]['v']['alias1'], 'value1')

    def test_process_attributes_with_default_values_not_used(self):
        self.cx2_obj.set_attribute_declarations({"nodes": {"annot": {"d": "string", "v": "example"}}})
        attributes = {"id": 1, "v": {"annot": "ex"}}
        processed = self.cx2_obj._process_attributes("nodes", attributes["v"])
        self.assertEqual(processed.get("annot"), "ex")

    def test_process_attributes_with_default_values_and_no_attribute_in_node(self):
        self.cx2_obj.set_attribute_declarations({"nodes": {"annot": {"d": "string", "v": "example"}}})
        attributes = {"id": 1, "v": {}}
        processed = self.cx2_obj._process_attributes("nodes", attributes["v"])
        self.assertEqual(processed.get("annot"), "example")

    def test_process_attributes_with_default_values_and_attribute_none(self):
        self.cx2_obj.set_attribute_declarations({"nodes": {"annot": {"d": "string", "v": "example"}}})
        attributes = {"id": 1, "v": {"annot": None}}
        processed = self.cx2_obj._process_attributes("nodes", attributes["v"])
        self.assertEqual(processed.get("annot"), "example")

    def test_translate_network_attributes_to_cx2(self):
        factory = NoStyleCXToCX2NetworkFactory()
        network_attributes = [{"n": "name1", "v": "value1"}, {"n": "name2", "v": "value2"}]
        result = factory._translate_network_attributes_to_cx2(network_attributes)
        expected_result = {"name1": "value1", "name2": "value2"}
        self.assertEqual(expected_result, result)

    def test_generate_attribute_declarations(self):
        factory = NoStyleCXToCX2NetworkFactory()
        network_attributes = [{"n": "name1", "v": "value1"}, {"n": "name2", "v": "value2"}]
        nodes = {1: {"n": "node1", "r": "rep1"}, 2: {"n": "node2", "r": "rep2"}}
        node_attributes = {1: [{"n": "attr1", "d": "string"}, {"n": "attr2", "d": "string"}]}
        edges = {1: {"s": 1, "t": 2, "i": "interaction1"}}
        edge_attributes = {1: [{"n": "e_attr1", "d": "string"}, {"n": "e_attr2", "d": "string"}]}

        result = factory._generate_attribute_declarations(network_attributes, nodes, node_attributes, edges,
                                                          edge_attributes)
        expected_result = {
            "networkAttributes": {"name1": {"d": "string"}, "name2": {"d": "string"}},
            "nodes": {
                "name": {"a": "n", "d": "string"},
                "represents": {"a": "r", "d": "string"},
                "attr1": {"d": "string"},
                "attr2": {"d": "string"}
            },
            "edges": {
                "interaction": {"a": "i", "d": "string"},
                "e_attr1": {"d": "string"},
                "e_attr2": {"d": "string"}
            }
        }
        self.assertEqual(expected_result, result)

    def test_process_attributes_for_cx2(self):
        factory = NoStyleCXToCX2NetworkFactory()
        node = {"@id": 1, "n": "name_val", "r": "represents_val"}
        attributes = {1: [{"n": "attr1", "v": "value1"}, {"n": "attr2", "v": "value2"}]}
        expected_keys = ["n", "r"]

        result = factory._process_attributes_for_cx2(node, attributes, expected_keys)
        expected_result = {"n": "name_val", "r": "represents_val", "attr1": "value1", "attr2": "value2"}
        self.assertEqual(expected_result, result)

    def test_get_cx2network_from_cx_file(self):
        cl = NoStyleCXToCX2NetworkFactory()
        nx = cl.get_cx2network(self.cx_file)

        self.assertEqual('Glypican 2 network', nx.get_network_attributes()['name'])
        self.assertEqual(2, len(list(nx.get_nodes())))
        self.assertEqual(1, len(list(nx.get_edges())))
        self.assertEqual(type(nx), CX2Network)
        self.assertTrue('edges' in nx.get_attribute_declarations().keys())
        self.assertTrue('nodes' in nx.get_attribute_declarations().keys())
        self.assertTrue('represents' in nx.get_attribute_declarations()['nodes'])
        self.assertEqual(type(nx.get_edges()[0]['v']['directed']), bool)

    def test_add_node(self):
        self.cx2_obj.add_node(1, attributes={"name": "Node1"}, x=10, y=20, z=30)
        self.assertEqual(self.cx2_obj.get_node(1), {"id": 1, "v": {"name": "Node1"}, "x": 10, "y": 20, "z": 30})

    def test_remove_node(self):
        self.cx2_obj.add_node(1, attributes={"name": "Node1"}, x=10, y=20, z=30)
        self.cx2_obj.add_edge(1, 1, 2, attributes={"interaction": "link"})
        self.cx2_obj.remove_node(1)
        self.assertIsNone(self.cx2_obj.get_node(1))
        self.assertIsNone(self.cx2_obj.get_edge(1))

    def test_update_node(self):
        self.cx2_obj.add_node(1, attributes={"name": "Node1"}, x=10, y=20, z=30)
        self.cx2_obj.update_node(1, attributes={"name": "UpdatedNode"}, x=11, y=21)
        self.assertEqual(self.cx2_obj.get_node(1), {"id": 1, "v": {"name": "UpdatedNode"}, "x": 11, "y": 21, "z": 30})

    def test_add_edge(self):
        self.cx2_obj.set_attribute_declarations({"edges": {"interaction": {"a": "i", "d": "string"}}})
        self.cx2_obj.add_edge(1, 1, 2, attributes={"i": "link"})
        self.assertEqual(self.cx2_obj.get_edge(1), {"id": 1, "s": 1, "t": 2, "v": {"interaction": "link"}})

    def test_remove_edge(self):
        self.cx2_obj.add_edge(1, 1, 2, attributes={"interaction": "link"})
        self.cx2_obj.remove_edge(1)
        self.assertIsNone(self.cx2_obj.get_edge(1))

    def test_update_edge(self):
        self.cx2_obj.set_attribute_declarations({"edges": {"interaction": {"a": "i", "d": "string"}}})
        self.cx2_obj.add_edge(1, 1, 2, attributes={"i": "link"})
        self.cx2_obj.update_edge(1, attributes={"i": "updated_link"})
        self.assertEqual(self.cx2_obj.get_edge(1), {"id": 1, "s": 1, "t": 2, "v": {"interaction": "updated_link"}})


if __name__ == '__main__':
    unittest.main()