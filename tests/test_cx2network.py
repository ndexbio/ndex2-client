import unittest
import os
import json
from ndex2.cx2 import CX2Network


class TestCX2Network(unittest.TestCase):
    def setUp(self):
        self.cx2_obj = CX2Network()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.sample_file = os.path.join(current_dir, 'data', 'demo.cx2')

    def tearDown(self):
        if os.path.exists('test_output.cx2'):
            os.remove('test_output.cx2')

    def test_create_from_raw_cx2_from_file(self):
        self.cx2_obj.create_from_raw_cx2(self.sample_file)
        self.assertIsNotNone(self.cx2_obj.attribute_declarations)
        self.assertGreater(len(self.cx2_obj.nodes), 0)

    def test_create_from_raw_cx2_from_list(self):
        with open(self.sample_file, 'r') as f:
            data_list = json.load(f)

        self.cx2_obj.create_from_raw_cx2(data_list)
        self.assertIsNotNone(self.cx2_obj.attribute_declarations)
        self.assertGreater(len(self.cx2_obj.nodes), 0)

    def test_invalid_input_create_from_raw_cx2(self):
        with self.assertRaises(ValueError):
            self.cx2_obj.create_from_raw_cx2(12345)

    def test_write_as_raw_cx2(self):
        self.cx2_obj.create_from_raw_cx2(self.sample_file)
        self.cx2_obj.write_as_raw_cx2('test_output.cx2')
        self.assertTrue(os.path.exists('test_output.cx2'))

        with open('test_output.cx2', 'r') as f:
            data = json.load(f)
            self.assertIn("CXVersion", data[0])

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
        self.assertEqual(self.cx2_obj._convert_value("integer", "42"), 42)
        self.assertEqual(self.cx2_obj._convert_value("double", "42.42"), 42.42)
        self.assertEqual(self.cx2_obj._convert_value("boolean", "true"), True)

    def test_replace_with_alias(self):
        self.cx2_obj.aliases['nodes'] = {'alias1': 'original1'}
        data = [{'id': 1, 'v': {'original1': 'value1'}}]
        transformed_data = self.cx2_obj._replace_with_alias(data, 'nodes')
        self.assertEqual(transformed_data[0]['v']['alias1'], 'value1')

    def test_process_attributes_with_default_values_not_used(self):
        self.cx2_obj.attribute_declarations = {"nodes": {"annot": {"d": "string", "v": "example"}}}
        self.cx2_obj.default_values = {"nodes": {"annot": "example"}}
        attributes = {"id": 1, "v": {"annot": "ex"}}
        processed = self.cx2_obj._process_attributes("nodes", attributes["v"])
        self.assertEqual(processed.get("annot"), "ex")

    def test_process_attributes_with_default_values_and_no_attribute_in_node(self):
        self.cx2_obj.attribute_declarations = {"nodes": {"annot": {"d": "string", "v": "example"}}}
        self.cx2_obj.default_values = {"nodes": {"annot": "example"}}
        attributes = {"id": 1, "v": {}}
        processed = self.cx2_obj._process_attributes("nodes", attributes["v"])
        self.assertEqual(processed.get("annot"), "example")

    def test_process_attributes_with_default_values_and_attribute_none(self):
        self.cx2_obj.attribute_declarations = {"nodes": {"annot": {"d": "string", "v": "example"}}}
        self.cx2_obj.default_values = {"nodes": {"annot": "example"}}
        attributes = {"id": 1, "v": {"annot": None}}
        processed = self.cx2_obj._process_attributes("nodes", attributes["v"])
        self.assertEqual(processed.get("annot"), "example")


if __name__ == '__main__':
    unittest.main()
