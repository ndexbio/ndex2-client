import unittest
import os
import json
import tempfile
import shutil

import networkx as nx
from ndex2 import constants

from ndex2.cx2 import CX2Network, convert_value, NoStyleCXToCX2NetworkFactory
from ndex2.cx2 import NetworkXToCX2NetworkFactory
from ndex2.cx2 import CX2NetworkPandasDataFrameFactory
from ndex2.exceptions import NDExAlreadyExists, NDExError
from ndex2.exceptions import NDExInvalidCX2Error, NDExNotFoundError


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

    def test_demo_cx2_loaded(self):
        self.cx2_obj.create_from_raw_cx2(self.sample_file)
        node721found = False
        for node_id, node_obj in self.cx2_obj.get_nodes().items():
            if node_obj['v']['name'] == '721':
                self.assertEqual({'Size': 4,
                                  'align_fdr': 0.0,
                                  'align_goID': 'GO:0071007',
                                  'align_score': 0.459948,
                                  'annot': 'U2-type catalytic step 2 spliceosome',
                                  'annot_source': 'CC',
                                  'cc_overlap': '3/30;3/61;3/115;2/21;2/60',
                                  'genes': 'SNRPB2,CDC40,CCDC12,SNRPA1,',
                                  'jaccard': 0.5, 'name': '721',
                                  'overlap': '3/5'}, node_obj['v'])
                node721found = True

        self.assertTrue(node721found)

    def test_create_from_raw_cx2_from_list(self):
        with open(self.sample_file, 'r') as f:
            data_list = json.load(f)
        self.cx2_obj.create_from_raw_cx2(data_list)
        self.assertIsNotNone(self.cx2_obj.get_attribute_declarations())
        self.assertGreater(len(self.cx2_obj.get_nodes()), 0)

    def test_invalid_input_create_from_raw_cx2(self):
        with self.assertRaises(NDExInvalidCX2Error):
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

    def test_get_cx2network_from_cx_file_no_cartesian_layout(self):
        cl = NoStyleCXToCX2NetworkFactory()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cx_file_no_layout = os.path.join(current_dir, 'data', 'glypican2.cx')
        nx = cl.get_cx2network(cx_file_no_layout)

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

    def test_add_node_without_attributes(self):
        self.cx2_obj.add_node(1, x=10, y=20, z=30)
        self.assertEqual(self.cx2_obj.get_node(1), {"id": 1, "v": {}, "x": 10, "y": 20, "z": 30})

    def test_add_node_without_any_argument(self):
        self.cx2_obj.add_node()
        self.assertEqual(self.cx2_obj.get_node(0), {"id": 0, "v": {}, "x": None, "y": None, "z": None})

    def test_add_node_with_existing_id(self):
        self.cx2_obj.add_node(1)
        with self.assertRaises(NDExAlreadyExists):
            self.cx2_obj.add_node(1)

    def test_add_node_without_coordinates(self):
        self.cx2_obj.add_node(1, attributes={"name": "Node1"})
        self.assertEqual(self.cx2_obj.get_node(1), {"id": 1, "v": {"name": "Node1"}, "x": None, "y": None, "z": None})

    def test_add_node_with_string_id(self):
        self.cx2_obj.add_node("1", attributes={"name": "Node1"})
        self.assertEqual(self.cx2_obj.get_node(1), {"id": 1, "v": {"name": "Node1"}, "x": None, "y": None, "z": None})

    def test_add_node_with_invalid_string_id(self):
        with self.assertRaises(NDExInvalidCX2Error):
            self.cx2_obj.add_node("invalid")

    def test_add_multiple_nodes_without_id(self):
        self.cx2_obj.add_node()
        self.cx2_obj.add_node()
        self.assertEqual(self.cx2_obj.get_node(0), {"id": 0, "v": {}, "x": None, "y": None, "z": None})
        self.assertEqual(self.cx2_obj.get_node(1), {"id": 1, "v": {}, "x": None, "y": None, "z": None})

    def test_remove_node_not_found(self):
        try:
            net = CX2Network()
            net.remove_node(1)
            self.fail('Expected Exception')
        except NDExNotFoundError as ne:
            self.assertEqual('Node 1 does not exist.', str(ne))

    def test_remove_node_none_passed_in(self):
        try:
            net = CX2Network()
            net.remove_node(None)
            self.fail('Expected Exception')
        except NDExNotFoundError as ne:
            self.assertEqual('None is an invalid node id.', str(ne))

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

    def test_add_edge_without_attributes(self):
        self.cx2_obj.add_edge(1, 1, 2)
        self.assertEqual(self.cx2_obj.get_edge(1), {"id": 1, "s": 1, "t": 2, "v": {}})

    def test_add_edge_without_any_argument(self):
        with self.assertRaises(NDExError):
            self.cx2_obj.add_edge()

    def test_add_edge_without_id(self):
        self.cx2_obj.add_edge(source=1, target=2)
        self.assertEqual(self.cx2_obj.get_edge(0), {"id": 0, "s": 1, "t": 2, "v": {}})

    def test_add_edge_with_existing_id(self):
        self.cx2_obj.add_edge(edge_id=1, source=1, target=1)
        with self.assertRaises(NDExAlreadyExists):
            self.cx2_obj.add_edge(edge_id=1, source=1, target=1)

    def test_add_edge_without_source(self):
        with self.assertRaises(NDExError):
            self.cx2_obj.add_edge(edge_id=1, target="1")

    def test_add_edge_without_target(self):
        with self.assertRaises(NDExError):
            self.cx2_obj.add_edge(edge_id=1, source=1)

    def test_add_edge_with_string_source_and_target(self):
        self.cx2_obj.add_edge(edge_id=1, source="1", target="2")
        self.assertEqual(self.cx2_obj.get_edge(1), {"id": 1, "s": 1, "t": 2, "v": {}})

    def test_add_edge_with_invalid_string_source(self):
        with self.assertRaises(NDExInvalidCX2Error):
            self.cx2_obj.add_edge(edge_id=1, source="invalid", target=1)

    def test_add_edge_with_invalid_string_target(self):
        with self.assertRaises(NDExInvalidCX2Error):
            self.cx2_obj.add_edge(edge_id=1, source=1, target="invalid")

    def test_add_multiple_edges_without_id(self):
        self.cx2_obj.add_edge(source=1, target=2)
        self.cx2_obj.add_edge(source=2, target=3)
        self.assertEqual(self.cx2_obj.get_edge(0), {"id": 0, "s": 1, "t": 2, "v": {}})
        self.assertEqual(self.cx2_obj.get_edge(1), {"id": 1, "s": 2, "t": 3, "v": {}})

    def test_remove_edge_none_passed_in(self):
        try:
            net = CX2Network()
            net.remove_edge(None)
            self.fail('Expected Exception')
        except NDExNotFoundError as ne:
            self.assertEqual('None is an invalid edge id.', str(ne))

    def test_remove_edge_not_found(self):
        try:
            net = CX2Network()
            net.remove_edge(1)
            self.fail('Expected Exception')
        except NDExNotFoundError as ne:
            self.assertEqual('Edge 1 does not exist.', str(ne))

    def test_remove_edge(self):
        self.cx2_obj.add_edge(1, 1, 2, attributes={"interaction": "link"})
        self.cx2_obj.remove_edge(1)
        self.assertIsNone(self.cx2_obj.get_edge(1))

    def test_update_edge(self):
        self.cx2_obj.set_attribute_declarations({"edges": {"interaction": {"a": "i", "d": "string"}}})
        self.cx2_obj.add_edge(1, 1, 2, attributes={"i": "link"})
        self.cx2_obj.update_edge(1, attributes={"i": "updated_link"})
        self.assertEqual(self.cx2_obj.get_edge(1), {"id": 1, "s": 1, "t": 2, "v": {"interaction": "updated_link"}})

    def test_set_network_attributes_none_passed(self):
        net = CX2Network()
        try:
            net.set_network_attributes(None)
            self.fail('Expected Exception')
        except NDExError as ne:
            self.assertEqual('network_attrs is None', str(ne))

    def test_add_network_attribute(self):
        net = CX2Network()
        net.add_node(0, attributes={'name': 'node0'})
        net.add_node(1, attributes={'name': 'node1'})
        net.add_edge(0, source=0, target=1, attributes={'foo': 1})
        netname = 'CX2Network test network'
        net.set_network_attributes({'name': netname,
                                    'description': 'Created by test_update_network_with_client() in '
                                                   'test_integration_cx2network.py integration test in ndex2-client'})
        net.add_network_attribute('new_attribute', 'value_of_attribute')
        self.assertEqual(len(net.get_network_attributes()), 3)

    def test_remove_network_attribute(self):
        net = CX2Network()
        net.add_node(0, attributes={'name': 'node0'})
        net.add_node(1, attributes={'name': 'node1'})
        net.add_edge(0, source=0, target=1, attributes={'foo': 1})
        netname = 'CX2Network test network'
        net.set_network_attributes({'name': netname,
                                    'description': 'Created by test_update_network_with_client() in '
                                                   'test_integration_cx2network.py integration test in ndex2-client'})
        net.remove_network_attribute('description')
        self.assertEqual(len(net.get_network_attributes()), 1)

    def test_creating_network_without_setting_attribute_declarations(self):
        net = CX2Network()
        net.add_node(0, attributes={'name': 'node0'})
        net.add_node(1, attributes={'name': 'node1'})
        net.add_edge(0, source=0, target=1, attributes={'foo': 1})
        netname = 'CX2Network test network'
        net.set_network_attributes({'name': netname,
                                    'description': 'Created by test_update_network_with_client() in '
                                                   'test_integration_cx2network.py integration test in ndex2-client'})
        self.assertEqual(net.get_attribute_declarations(), {'edges': {'foo': {'d': 'integer'}},
                                                            'networkAttributes': {'description': {'d': 'string'},
                                                                                  'name': {'d': 'string'}},
                                                            'nodes': {'name': {'d': 'string'}}})
        self.assertEqual(len(net.get_attribute_declarations()), 3)

    def test_to_cx_without_preset_status(self):
        net = CX2Network()
        net.add_node(0, attributes={'name': 'node0'})
        net.add_node(1, attributes={'name': 'node1'})
        net.add_edge(0, source=0, target=1, attributes={'foo': 1})
        netname = 'CX2Network test network'
        net.set_network_attributes({'name': netname,
                                    'description': 'Created by test_update_network_with_client() in '
                                                   'test_integration_cx2network.py integration test in ndex2-client'})
        self.assertTrue('status' in net.to_cx2()[-1])

    def test_get_next_id_without_aspect_id(self):
        self.assertEqual(self.cx2_obj._get_next_id('nodes'), 0)
        self.assertEqual(self.cx2_obj._get_next_id('nodes'), 1)

    def test_get_next_id_with_aspect_id(self):
        self.assertEqual(self.cx2_obj._get_next_id('nodes', 5), 5)
        self.assertEqual(self.cx2_obj._get_next_id('nodes'), 6)

    def test_check_and_cast_id_with_integer(self):
        self.assertEqual(self.cx2_obj._check_and_cast_id(5), 5)

    def test_check_and_cast_id_with_string(self):
        self.assertEqual(self.cx2_obj._check_and_cast_id("5"), 5)

    def test_check_and_cast_id_with_invalid_string(self):
        with self.assertRaises(NDExInvalidCX2Error):
            self.cx2_obj._check_and_cast_id("invalid")

    def test_check_and_cast_id_with_invalid_type(self):
        with self.assertRaises(NDExInvalidCX2Error):
            self.cx2_obj._check_and_cast_id(5.5)

    def test_integer_type(self):
        self.assertEqual(self.cx2_obj._get_cx2_type(100), "integer")

    def test_long_type_positive(self):
        self.assertEqual(self.cx2_obj._get_cx2_type(2 ** 31), "long")

    def test_long_type_negative(self):
        self.assertEqual(self.cx2_obj._get_cx2_type(-2 ** 31 - 1), "long")

    def test_double_type(self):
        self.assertEqual(self.cx2_obj._get_cx2_type(10.5), "double")

    def test_boolean_type(self):
        self.assertEqual(self.cx2_obj._get_cx2_type(True), "boolean")

    def test_list_of_integers(self):
        self.assertEqual(self.cx2_obj._get_cx2_type([1, 2, 3]), "list_of_integer")

    def test_list_of_floats(self):
        self.assertEqual(self.cx2_obj._get_cx2_type([1.2, 2.3]), "list_of_double")

    def test_list_of_strings(self):
        self.assertEqual(self.cx2_obj._get_cx2_type(["foo", "bar"]), "list_of_string")

    def test_list_of_booleans(self):
        self.assertEqual(self.cx2_obj._get_cx2_type([True, False]), "list_of_boolean")

    def test_convert_value_with_invalid_list_of_and_string(self):
        with self.assertRaises(NDExInvalidCX2Error):
            convert_value('list_of_', 'hi')

    def test_convert_value_with_list_of_string_and_string(self):
        with self.assertRaises(NDExInvalidCX2Error):
            convert_value('list_of_string', 'hi')

    def test_convert_value_with_invalid_list_of_and_number(self):
        with self.assertRaises(NDExInvalidCX2Error):
            convert_value('list_of_', 7)

    def test_convert_value_with_unrecognized_data_type(self):
        with self.assertRaises(NDExInvalidCX2Error):
            convert_value('banana', 7)
        with self.assertRaises(NDExInvalidCX2Error):
            convert_value('banana', [1, 2, 3])

    def test_convert_value_with_valid_data_types(self):
        self.assertEqual(convert_value('string', 123), '123')
        self.assertEqual(convert_value('integer', '123'), 123)
        self.assertEqual(convert_value('double', '123.45'), 123.45)
        self.assertEqual(convert_value('boolean', 'true'), True)
        self.assertEqual(convert_value('list_of_integer', [1, 2, 3]), [1, 2, 3])

    def test_get_cx2network_with_graph(self):
        factory = NetworkXToCX2NetworkFactory()
        g = nx.Graph()
        g.add_node(1, x=100, y=200, z=300, label="Node1")
        g.add_node(2, label="Node2")
        g.add_edge(1, 2, weight=1.5)
        g.graph['name'] = 'Test Graph'

        cx2network = factory.get_cx2network(g)

        self.assertEqual(len(cx2network.get_nodes()), 2)
        node1 = cx2network.get_node(1)
        self.assertEqual(node1['x'], 100)
        self.assertEqual(node1['y'], 200)
        self.assertEqual(node1['z'], 300)
        self.assertEqual(node1['v']['label'], 'Node1')
        node2 = cx2network.get_node(2)
        self.assertIsNone(node2['x'])
        self.assertIsNone(node2['y'])
        self.assertIsNone(node2['z'])
        self.assertEqual(node2['v']['label'], 'Node2')

        self.assertEqual(len(cx2network.get_edges()), 1)
        edge = next(iter(cx2network.get_edges().values()))
        self.assertEqual(edge['s'], 1)
        self.assertEqual(edge['t'], 2)
        self.assertEqual(edge['v']['weight'], 1.5)

        self.assertEqual(cx2network.get_network_attributes()['name'], 'Test Graph')

    def test_conversion_to_dataframe(self):
        network = CX2Network()
        network.add_node(node_id=1)
        network.add_node(node_id=2)
        network.add_edge(source=1, target=2, attributes={'edge_attr': 'a'})
        factory = CX2NetworkPandasDataFrameFactory()
        df = factory.get_dataframe(network)

        self.assertEqual(len(df), 1)
        self.assertTrue((df['source_id'] == 1).any())
        self.assertTrue((df['target_id'] == 2).any())
        self.assertTrue((df['edge_attr'] == 'a').any())

    def test_get_nodelist_table(self):
        network = CX2Network()
        network.add_node(node_id=1, attributes={'attr1': 'value1', 'attr2': 10}, x=0.1, y=0.2, z=0.3)
        network.add_node(node_id=2, attributes={'attr1': 'value2', 'attr2': 20}, x=0.4, y=0.5, z=0.6)

        factory = CX2NetworkPandasDataFrameFactory()
        df = factory.get_nodelist_table(network)

        self.assertEqual(len(df), 2)

        self.assertTrue(1 in df.index)
        self.assertTrue(2 in df.index)

        self.assertEqual(df.at[1, 'attr1'], 'value1')
        self.assertEqual(df.at[1, 'attr2'], 10)
        self.assertAlmostEqual(df.at[1, 'x'], 0.1)
        self.assertAlmostEqual(df.at[1, 'y'], 0.2)
        self.assertAlmostEqual(df.at[1, 'z'], 0.3)

        self.assertEqual(df.at[2, 'attr1'], 'value2')
        self.assertEqual(df.at[2, 'attr2'], 20)
        self.assertAlmostEqual(df.at[2, 'x'], 0.4)
        self.assertAlmostEqual(df.at[2, 'y'], 0.5)
        self.assertAlmostEqual(df.at[2, 'z'], 0.6)

    def test_remove_network_attribute_passing_none(self):
        try:
            network = CX2Network()
            network.remove_network_attribute(None)
            self.fail('Expected Exception')
        except NDExNotFoundError as ne:
            self.assertEqual('None is an invalid key', str(ne))

    def test_remove_network_attribute_not_found(self):
        try:
            network = CX2Network()
            network.remove_network_attribute('foo')
            self.fail('Expected Exception')
        except NDExNotFoundError as ne:
            self.assertEqual('Network attribute \'foo\' does not exist.', str(ne))

    def test_add_node_attribute(self):
        self.cx2_obj.add_node(1)
        self.cx2_obj.add_node_attribute(node_id=1, key='color', value='red')
        node = self.cx2_obj.get_node(1)
        self.assertIn('color', node['v'])
        self.assertEqual(node['v']['color'], 'red')

        self.cx2_obj.add_node_attribute(node_id=1, key='color', value='blue')
        node = self.cx2_obj.get_node(1)
        self.assertEqual(node['v']['color'], 'blue')

        self.cx2_obj.add_node_attribute(node_id=1, key='size', value=10, datatype='integer')
        node = self.cx2_obj.get_node(1)
        self.assertIn('size', node['v'])
        self.assertEqual(node['v']['size'], 10)

    def test_add_node_attribute_for_nonexistent_node(self):
        with self.assertRaises(NDExError):
            self.cx2_obj.add_node_attribute(node_id=999, key='nonexistent', value='value')

    def test_add_edge_attribute(self):
        self.cx2_obj.add_node(1)
        self.cx2_obj.add_node(2)
        self.cx2_obj.add_edge(edge_id=1, source=1, target=2)
        self.cx2_obj.add_edge_attribute(edge_id=1, key='weight', value=1.5)
        edge = self.cx2_obj.get_edge(1)
        self.assertIn('weight', edge['v'])
        self.assertEqual(edge['v']['weight'], 1.5)
        # Test updating the attribute
        self.cx2_obj.add_edge_attribute(edge_id=1, key='weight', value=2.5)
        edge = self.cx2_obj.get_edge(1)
        self.assertEqual(edge['v']['weight'], 2.5)
        # Test adding attribute with datatype
        self.cx2_obj.add_edge_attribute(edge_id=1, key='label', value='edge1', datatype='string')
        edge = self.cx2_obj.get_edge(1)
        self.assertIn('label', edge['v'])
        self.assertEqual(edge['v']['label'], 'edge1')
        # Test for non-existing edge
        with self.assertRaises(NDExError):
            self.cx2_obj.add_edge_attribute(edge_id=999, key='nonexistent', value='value')

    def test_get_default_value(self):
        # Set up some attribute declarations with default values
        self.cx2_obj.set_attribute_declarations({
            'nodes': {
                'color': {'d': 'string', 'v': 'red'},  # 'd' for datatype, 'v' for default value
                'size': {'d': 'integer', 'v': 10}
            },
            'edges': {
                'weight': {'d': 'double', 'v': 1.0}
            }
        })

        # Test retrieving default values for node attributes
        default_color = self.cx2_obj.get_default_value('nodes', 'color')
        self.assertEqual(default_color, 'red')

        default_size = self.cx2_obj.get_default_value('nodes', 'size')
        self.assertEqual(default_size, 10)

        # Test retrieving default value for edge attribute
        default_weight = self.cx2_obj.get_default_value('edges', 'weight')
        self.assertEqual(default_weight, 1.0)

        # Test retrieving default value when aspect name is incorrect
        default_nonexistent_aspect = self.cx2_obj.get_default_value('nonexistent_aspect', 'color')
        self.assertIsNone(default_nonexistent_aspect)

        # Test retrieving default value when attribute name does not exist
        default_nonexistent_attribute = self.cx2_obj.get_default_value('nodes', 'nonexistent_attribute')
        self.assertIsNone(default_nonexistent_attribute)

    def test_get_alias(self):
        # Set up some attribute declarations with aliases
        self.cx2_obj.set_attribute_declarations({
            'nodes': {
                'color': {'d': 'string', 'a': 'clr'},  # 'd' for datatype, 'a' for alias
                'size': {'d': 'integer', 'a': 'sz'}
            },
            'edges': {
                'weight': {'d': 'double', 'a': 'wt'}
            }
        })

        # Test retrieving alias for node attributes
        alias_color = self.cx2_obj.get_alias('nodes', 'color')
        self.assertEqual(alias_color, 'clr')

        alias_size = self.cx2_obj.get_alias('nodes', 'size')
        self.assertEqual(alias_size, 'sz')

        # Test retrieving alias for edge attribute
        alias_weight = self.cx2_obj.get_alias('edges', 'weight')
        self.assertEqual(alias_weight, 'wt')

        # Test retrieving alias when aspect name is incorrect
        alias_nonexistent_aspect = self.cx2_obj.get_alias('nonexistent_aspect', 'color')
        self.assertIsNone(alias_nonexistent_aspect)

        # Test retrieving alias when attribute name does not exist
        alias_nonexistent_attribute = self.cx2_obj.get_alias('nodes', 'nonexistent_attribute')
        self.assertIsNone(alias_nonexistent_attribute)

    def test_set_node_attribute(self):
        self.cx2_obj.add_node(1)

        # Set a new attribute for the node
        self.cx2_obj.set_node_attribute(node_id=1, attribute='color', value='red')
        node = self.cx2_obj.get_node(1)
        self.assertIn('color', node['v'])
        self.assertEqual(node['v']['color'], 'red')

        # Update the existing attribute of the node
        self.cx2_obj.set_node_attribute(node_id=1, attribute='color', value='blue')
        node = self.cx2_obj.get_node(1)
        self.assertEqual(node['v']['color'], 'blue')

        # Set another attribute for the node
        self.cx2_obj.set_node_attribute(node_id=1, attribute='size', value=10)
        node = self.cx2_obj.get_node(1)
        self.assertIn('size', node['v'])
        self.assertEqual(node['v']['size'], 10)

        # Attempt to set an attribute for a non-existing node
        with self.assertRaises(NDExError):
            self.cx2_obj.set_node_attribute(node_id=999, attribute='nonexistent', value='value')

    def test_remove_specific_node_attribute(self):
        self.cx2_obj.add_node(1, attributes={'color': 'red', 'size': 'small'})
        self.cx2_obj.add_node(2, attributes={'color': 'blue', 'size': 'large'})

        # Removing 'color' attribute from node 1
        self.cx2_obj.remove_node_attribute(1, 'color')

        node1 = self.cx2_obj.get_node(1)
        node2 = self.cx2_obj.get_node(2)

        self.assertNotIn('color', node1['v'])
        self.assertIn('size', node1['v'])
        self.assertIn('color', node2['v'])  # Node 2 should still have its 'color' attribute

    def test_remove_specific_edge_attribute(self):
        self.cx2_obj.add_node(1)
        self.cx2_obj.add_node(2)
        self.cx2_obj.add_edge(1, 1, 2, attributes={'weight': 1.5, 'label': 'edge1'})
        self.cx2_obj.add_edge(2, 2, 1, attributes={'weight': 2.5, 'label': 'edge2'})

        # Removing 'weight' attribute from edge 1
        self.cx2_obj.remove_edge_attribute(1, 'weight')

        edge1 = self.cx2_obj.get_edge(1)
        edge2 = self.cx2_obj.get_edge(2)

        self.assertNotIn('weight', edge1['v'])
        self.assertIn('label', edge1['v'])
        self.assertIn('weight', edge2['v'])  # Edge 2 should still have its 'weight' attribute

    def test_remove_node_attribute_nonexistent_node(self):
        with self.assertRaises(NDExNotFoundError) as context:
            self.cx2_obj.remove_node_attribute(999, 'color')
        self.assertEqual('Node 999 does not exist.', str(context.exception))

    def test_remove_edge_attribute_nonexistent_edge(self):
        with self.assertRaises(NDExNotFoundError) as context:
            self.cx2_obj.remove_edge_attribute(999, 'weight')
        self.assertEqual('Edge 999 does not exist.', str(context.exception))

    def test_set_name_for_network(self):
        test_name = "Test Network Name"
        self.cx2_obj.set_name(test_name)
        self.assertEqual(self.cx2_obj.get_network_attributes()['name'], test_name)

    def test_cleanup_attribute_declarations(self):
        self.cx2_obj.add_node(1, attributes={'color': 'red', 'shape': 'circle'})
        self.cx2_obj.add_node(2, attributes={'color': 'blue', 'shape': 'square'})
        self.cx2_obj.add_edge(1, 1, 2, attributes={'weight': 1.5, 'type': 'dashed'})

        self.cx2_obj.remove_node_attribute(1, 'color')
        self.cx2_obj.remove_node_attribute(2, 'color')
        self.cx2_obj.remove_edge_attribute(1, 'weight')

        self.cx2_obj._cleanup_attribute_declarations()

        self.assertNotIn('color', self.cx2_obj.get_attribute_declarations().get(constants.NODES_ASPECT, {}))
        self.assertIn('shape', self.cx2_obj.get_attribute_declarations().get(constants.NODES_ASPECT, {}))
        self.assertNotIn('weight', self.cx2_obj.get_attribute_declarations().get(constants.EDGES_ASPECT, {}))
        self.assertIn('type', self.cx2_obj.get_attribute_declarations().get(constants.EDGES_ASPECT, {}))

    def test_apply_style_from_network(self):
        main_network = CX2Network()
        style_network = CX2Network()

        visual_properties = {'background': 'white'}
        node_bypasses = {1: {'color': 'red'}, 2: {'color': 'blue'}}
        edge_bypasses = {1: {'width': 2.0}}

        style_network.set_visual_properties(visual_properties)
        for node_id, bypass in node_bypasses.items():
            style_network.add_node_bypass(node_id, bypass)
        for edge_id, bypass in edge_bypasses.items():
            style_network.add_edge_bypass(edge_id, bypass)

        main_network.apply_style_from_network(style_network)

        self.assertEqual(main_network.get_visual_properties(), visual_properties)
        self.assertEqual(main_network.get_node_bypasses(), node_bypasses)
        self.assertEqual(main_network.get_edge_bypasses(), edge_bypasses)

        with self.assertRaises(TypeError) as context:
            main_network.apply_style_from_network(None)
        self.assertEqual(str(context.exception), 'Object passed in is None')

        with self.assertRaises(TypeError) as context:
            main_network.apply_style_from_network("Not a CX2Network")
        self.assertEqual(str(context.exception), 'Object passed in is not CX2Network')

    def test_opaque_aspect_operations(self):
        self.cx2_obj.set_opaque_aspect('aspect1', 'value1')
        self.assertIn({'aspect1': 'value1'}, self.cx2_obj.get_opaque_aspects())

        aspect_value = self.cx2_obj.get_opaque_aspect('aspect1')
        self.assertEqual(aspect_value, 'value1')

        non_existing_aspect_value = self.cx2_obj.get_opaque_aspect('non_existing_aspect')
        self.assertIsNone(non_existing_aspect_value)

        self.cx2_obj.set_opaque_aspect('aspect1', 'updated_value1')
        self.assertIn({'aspect1': 'updated_value1'}, self.cx2_obj.get_opaque_aspects())

        self.cx2_obj.set_opaque_aspect('aspect2', 'value2')
        self.assertIn({'aspect2': 'value2'}, self.cx2_obj.get_opaque_aspects())


if __name__ == '__main__':
    unittest.main()
