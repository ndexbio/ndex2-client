import json


class CX2Network(object):
    """
    Represents the CX2 network format, allowing for reading, processing, and writing of CX2 data.
    """

    def __init__(self):
        """
        Initializes an empty CX2Network instance with default data structures.
        """
        self.attribute_declarations = None
        self.network_attribute = {}
        self.nodes = {}
        self.edges = {}
        self.aliases = {"nodes": {}, "edges": {}}
        self.default_values = {"nodes": {}, "edges": {}}
        self.visual_properties = []
        self.node_bypasses = {}
        self.edge_bypasses = {}
        self.opaque_aspects = []
        self.status = {}

    def create_from_raw_cx2(self, cx2_file_path):
        """
        Loads and processes a raw CX2 file into structured data within the instance.

        :param cx2_file_path: Path to the CX2 file to be processed.
        :type cx2_file_path: str
        """
        with open(cx2_file_path, 'r') as cx2_file:
            raw_data = json.load(cx2_file)

        for section in raw_data:
            if 'attributeDeclarations' in section:
                self.attribute_declarations = section['attributeDeclarations'][0]
                for aspect, declarations in self.attribute_declarations.items():
                    for key, details in declarations.items():
                        alias = details.get("a", None)
                        if alias and aspect in ["nodes", "edges"]:
                            self.aliases[aspect][alias] = key
                        default_value = details.get("v", None)
                        if default_value and aspect in ["nodes", "edges"]:
                            self.default_values[aspect][key] = default_value

            elif 'networkAttributes' in section:
                for attr in section['networkAttributes']:
                    for key, value in attr.items():
                        declared_type = (self.attribute_declarations['networkAttributes'].get(key, {})
                                         .get('d', 'string'))
                        self.network_attribute[key] = self._convert_value(declared_type, value)

            elif 'nodes' in section:
                for node in section['nodes']:
                    new_node = {
                        "id": node["id"],
                        "v": self._process_attributes('nodes', node["v"]),
                        "x": node.get("x", None),
                        "y": node.get("y", None),
                        "z": node.get("z", None)
                    }
                    self.nodes[node["id"]] = new_node

            elif 'edges' in section:
                for edge in section['edges']:
                    new_edge = {
                        "id": edge["id"],
                        "s": edge["s"],
                        "t": edge["t"],
                        "v": self._process_attributes('edges', edge["v"])
                    }
                    self.edges[edge["id"]] = new_edge

            elif "visualProperties" in section:
                self.visual_properties = section["visualProperties"][0]
            elif "nodeBypasses" in section:
                for nodeBypass in section["nodeBypasses"]:
                    self.node_bypasses[nodeBypass["id"]] = nodeBypass["v"]
            elif "edgeBypasses" in section:
                for edgeBypass in section["edgeBypasses"]:
                    self.edge_bypasses[edgeBypass["id"]] = edgeBypass["v"]
            elif "metaData" in section or "CXVersion" in section:
                pass
            elif "status" in section:
                self.status = section["status"]
            else:
                self.opaque_aspects.append(section)

    def write_as_raw_cx2(self, output_path):
        """
        Writes data from CX2Network object to a raw CX2 formatted JSON file.

        :param output_path: Destination file path for the CX2 formatted output.
        :type output_path: str
        """
        output_data = [{
            "CXVersion": "2.0",
            "hasFragments": False
        }]
        meta_data = [
            {"elementCount": 1, "name": "attributeDeclarations"},
            {"elementCount": 1, "name": "networkAttributes"},
            {"elementCount": len(self.nodes), "name": "nodes"},
            {"elementCount": len(self.edges), "name": "edges"},
            {"elementCount": 1, "name": "visualProperties"},
            {"elementCount": len(self.node_bypasses), "name": "nodeBypasses"},
            {"elementCount": len(self.edge_bypasses), "name": "edgeBypasses"},
        ]
        for opaque_aspect in self.opaque_aspects:
            aspect_name = list(opaque_aspect.keys())[0]
            aspect_count = len(opaque_aspect[aspect_name])
            meta_data.append({"elementCount": aspect_count, "name": aspect_name})
        output_data.append({"metaData": meta_data})

        output_data.append({"attributeDeclarations": [self.attribute_declarations]})
        output_data.append({"networkAttributes": [self.network_attribute]})

        nodes_list = self._replace_with_alias(list(self.nodes.values()), 'nodes')
        edges_list = self._replace_with_alias(list(self.edges.values()), 'edges')

        output_nodes = []
        for node in nodes_list:
            clean_node = {k: v for k, v in node.items() if k not in ['x', 'y', 'z']}
            if 'x' in node and node['x'] is not None:
                clean_node['x'] = node['x']
            if 'y' in node and node['y'] is not None:
                clean_node['y'] = node['y']
            if 'z' in node and node['z'] is not None:
                clean_node['z'] = node['z']
            output_nodes.append(clean_node)

        output_data.append({
            "nodes": output_nodes
        })

        output_data.append({
            "edges": edges_list
        })

        if self.visual_properties:
            output_data.append({"visualProperties": [self.visual_properties]})

        if self.node_bypasses:
            output_node_bypasses = [{"id": k, "v": v} for k, v in self.node_bypasses.items()]
            output_data.append({"nodeBypasses": output_node_bypasses})

        if self.edge_bypasses:
            output_edge_bypasses = [{"id": k, "v": v} for k, v in self.edge_bypasses.items()]
            output_data.append({"edgeBypasses": output_edge_bypasses})

        output_data.extend(self.opaque_aspects)

        if self.status:
            output_data.append({"status": self.status})

        with open(output_path, 'w') as output_file:
            json.dump(output_data, output_file, indent=4)

    def _process_attributes(self, aspect_name, attributes):
        """
        Processes attributes based on declared types and aliases for the given aspect.

        :param aspect_name: Name of the aspect (e.g., 'nodes', 'edges') for which attributes are being processed.
        :type aspect_name: str
        :param attributes: Dictionary of attributes to be processed.
        :type attributes: dict
        """
        processed_attrs = {}

        # Initially populate with default values
        for key, default_value in self.default_values[aspect_name].items():
            actual_key = self.aliases[aspect_name].get(key, key)
            processed_attrs[actual_key] = default_value

        for key, value in attributes.items():
            actual_key = self.aliases[aspect_name].get(key, key)
            declared_type = self.attribute_declarations[aspect_name].get(actual_key, {}).get('d', 'string')
            if value is not None:
                processed_attrs[actual_key] = self._convert_value(declared_type, value)

        return processed_attrs

    def _convert_value(self, dtype, value):
        """
        Converts a value to its appropriate data type based on its declared type.

        :param dtype: Declared data type for the value.
        :type dtype: str
        :param value: Value to be converted.
        :type value: any
        """
        if dtype == "integer":
            return int(value)
        elif dtype == "double" or dtype == "long":
            return float(value)
        elif dtype == "boolean":
            return bool(value)
        elif dtype.startswith("list_of_"):
            elem_type = dtype.split("_")[2]
            return [self._convert_value(elem_type, v) for v in value]
        else:
            return value

    def _replace_with_alias(self, data_list, aspect):
        """
        Replaces attribute names in a data list with their corresponding aliases, if available.

        :param data_list: List of data items (e.g., nodes or edges) with attributes.
        :type data_list: list
        :param aspect: Name of the aspect (e.g., 'nodes', 'edges') for which aliases are to be applied.
        :type aspect: str
        """
        new_data = []

        reverse_aliases = {v: k for k, v in self.aliases[aspect].items()}

        for item in data_list:
            new_item = item.copy()
            if 'v' in new_item:
                for attr in list(new_item['v'].keys()):
                    if attr in reverse_aliases:
                        new_item['v'][reverse_aliases[attr]] = new_item['v'].pop(attr)
            new_data.append(new_item)

        return new_data