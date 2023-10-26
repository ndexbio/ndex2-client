import json

from ndex2 import create_nice_cx_from_raw_cx, create_nice_cx_from_file
from ndex2.exceptions import NDExInvalidCX2Error, NDExAlreadyExists, NDExError
from ndex2.nice_cx_network import NiceCXNetwork
from itertools import zip_longest


def convert_value(dtype, value):
    """
    Converts a value to its appropriate data type based on its declared type.

    :param dtype: Declared data type for the value.
    :type dtype: str
    :param value: Value to be converted.
    :type value: any
    """
    try:
        if dtype == "integer" or dtype == "long":
            return int(value)
        elif dtype == "double":
            return float(value)
        elif dtype == "boolean":
            if isinstance(value, bool):
                return value
            else:
                return True if value.lower() == 'true' else False
        elif dtype.startswith("list_of_"):
            elem_type = dtype.split("_")[2]
            return [convert_value(elem_type, v) for v in value]
        else:
            return value
    except ValueError as err:
        raise NDExInvalidCX2Error('Declared value of attribute data does not match the actual value type: ' + str(err))


class CX2Network(object):
    """
    A representation of the CX2 (Cytoscape Exchange) network format.

    This class provides functionality to read, process, and write data in the CX2 format.
    It facilitates the structured access and manipulation of network data elements such as nodes, edges,
    attributes, and visual properties.

    The class maintains internal data structures that hold network data and provides methods to:

    1. Load data from raw CX2 files.

    2. Generate the CX2 representation of the current state.

    3. Write the current state to a CX2 formatted file.

    Attributes:
        - ``attribute_declarations``
            A dictionary representing the declarations of attributes for network elements.
        - ``network_attribute``
            A dictionary storing global attributes of the network.
        - ``nodes``
            A dictionary of nodes.
        - ``edges``
            A dictionary of edges.
        - ``aliases``
            A dictionary that maps aspect names (like "nodes" or "edges") to their alias declarations.
        - ``default_values``
            A dictionary that maps aspect names to their default attribute values.
        - ``visual_properties``
            A list storing visual properties of the network.
        - ``node_bypasses``
            A dictionary of node-specific visual properties that bypass default styles.
        - ``edge_bypasses``
            A dictionary of edge-specific visual properties that bypass default styles.
        - ``opaque_aspects``
            A list of other aspects in the CX2 format which don't have a defined structure in this class.
        - ``status``
            A dictionary representing the network's status.
    """

    def __init__(self):
        self._attribute_declarations = {}
        self._network_attributes = {}
        self._nodes = {}
        self._edges = {}
        self._visual_properties = []
        self._node_bypasses = {}
        self._edge_bypasses = {}
        self._opaque_aspects = []
        self._status = {}
        self._int_id_generator = {'nodes': 0, 'edges': 0}

    def _get_next_id(self, aspect, aspect_id=None):
        """
        Retrieves the next available ID for a given aspect (e.g., 'nodes' or 'edges') and increments the ID counter.
        If aspect_id is passed, it updates the next available ID for a given aspect (e.g., 'nodes' or 'edges').
        It sets the ID to the larger of the current ID or the provided aspect_id, then increments by 1.

        :param aspect: The aspect for which the ID needs to be generated.
                       Expected values include 'nodes' or 'edges'.
        :type aspect: str
        :param aspect_id: The suggested ID for the given aspect.
                          The actual ID set might be this value + 1 or higher depending on the current state.
        :type aspect_id: int
        :return: The next available ID for the given aspect.
        :rtype: int
        """
        if aspect_id is not None:
            validated_aspect_id = self._check_and_cast_id(aspect_id)
            self._int_id_generator[aspect] = max(validated_aspect_id, self._int_id_generator[aspect])
        return_id = self._int_id_generator[aspect]
        self._int_id_generator[aspect] += 1
        return return_id

    @staticmethod
    def _check_and_cast_id(aspect_id):
        """
        Validates and converts a given aspect ID to an integer. The aspect ID can be either an integer or
        a string representation of an integer. If the aspect ID is neither, or if the string cannot be
        converted to an integer, an NDExInvalidCX2Error is raised.

        :param aspect_id: The aspect ID to be validated and converted.
        :type aspect_id: int or str
        :return: The aspect ID as an integer.
        :rtype: int
        :raises NDExInvalidCX2Error: If the aspect ID is neither an integer nor a string that can be
                                     converted to an integer.
        """
        if isinstance(aspect_id, int):
            return aspect_id
        elif isinstance(aspect_id, str):
            try:
                aspect_id = int(aspect_id)
                return aspect_id
            except ValueError:
                pass
        raise NDExInvalidCX2Error(f'IDs of nodes, edges and the source and target of edges must be integer or long. '
                                  f'Got {aspect_id}')

    def get_attribute_declarations(self):
        """
        Retrieves the attribute declarations.

        :return: The attribute declarations.
        :rtype: dict
        """
        return self._attribute_declarations

    def _generate_attribute_declarations_for_aspect(self, aspect, attributes, aliases):
        """
        Generates attribute declarations for a given aspect of the network.

        This method examines the provided attributes and, if they are not already
        declared, adds them to the attribute declarations for the specified aspect.

        :param aspect: The aspect of the network (e.g., 'nodes', 'edges') for which
                       attribute declarations are to be generated.
        :type aspect: str
        :param attributes: A dictionary of attributes where keys are attribute names
                           and values are the corresponding attribute values.
        :type attributes: dict
        :param aliases: A dictionary mapping aspect names to their alias declarations.
                        This is used to ensure that attributes that are aliases are not
                        added to the attribute declarations.
        :type aliases: dict
        """
        if aspect not in self.get_attribute_declarations().keys():
            self._attribute_declarations[aspect] = {}
        if attributes is not None:
            for attr, value in attributes.items():
                if (attr not in self.get_attribute_declarations()[aspect].keys() and attr not in aliases.values()
                        and attr not in aliases.keys()):
                    self.get_attribute_declarations()[aspect][attr] = {
                        "d": type(value).__name__
                    }

    def set_attribute_declarations(self, value):
        """
        Sets the attribute declarations.

        :param value: The attribute declarations to set.
        :type value: dict
        """
        self._attribute_declarations = value

    def get_network_attributes(self):
        """
        Retrieves the network attributes.

        :return: The network attributes.
        :rtype: dict
        """
        return self._network_attributes

    def set_network_attributes(self, network_attrs):
        """
        Sets the network attributes after processing them using declared types in attribute declarations.

        :param network_attrs: The network attributes to set.
        :type network_attrs: dict
        """
        processed_network_attrs = {}
        for key, value in network_attrs.items():
            declared_type = self.get_declared_type('networkAttributes', key)
            processed_network_attrs[key] = convert_value(declared_type, value)
        self._generate_attribute_declarations_for_aspect('networkAttributes', processed_network_attrs, {})
        self._network_attributes = processed_network_attrs

    def add_network_attribute(self, key, value):
        declared_type = self.get_declared_type('networkAttributes', key)
        converted_value = convert_value(declared_type, value)
        self._network_attributes[key] = converted_value
        self._generate_attribute_declarations_for_aspect('networkAttributes', {key: converted_value}, {})

    def remove_network_attribute(self, key):
        if key in self._network_attributes:
            del self._network_attributes[key]

    def get_name(self):
        """
        Retrieves the network name.

        :return: Network name
        :rtype: str
        """
        return self.get_network_attributes().get('name', None)

    def get_nodes(self):
        """
        Retrieves the nodes in the network.

        :return: Nodes in the network.
        :rtype: dict
        """
        return self._nodes

    def add_node(self, node_id=None, attributes=None, x=None, y=None, z=None):
        """
        Adds a node to the network.

        :param node_id: ID of the node to add.
        :type node_id: int or str
        :param attributes: Attributes of the node.
        :type attributes: dict, optional
        :param x: X-coordinate of the node.
        :type x: float, optional
        :param y: Y-coordinate of the node.
        :type y: float, optional
        :param z: Z-coordinate of the node.
        :type z: float, optional
        """
        if node_id in self.get_nodes().keys():
            raise NDExAlreadyExists(f"Node with ID {node_id} already exists.")
        else:
            node_id = self._get_next_id('nodes', node_id)
        processed_attributes = self._process_attributes('nodes', attributes)
        node = {
            "id": node_id,
            "v": processed_attributes,
            "x": x,
            "y": y,
            "z": z
        }
        self._nodes[node_id] = node
        return node_id

    def get_node(self, node_id):
        """
        Retrieves a node based on its ID.

        :param node_id: ID of the node to retrieve.
        :type node_id: int or str
        :return: Node with the given ID or None if not found.
        :rtype: dict or None
        """
        return self._nodes.get(node_id, None)

    def remove_node(self, node_id):
        """
        Removes a node and checks for dangling edges (edges without both source and target).

        :param node_id: ID of the node to remove.
        :type node_id: int or str
        """
        if node_id in self._nodes:
            del self._nodes[node_id]

        edges_to_remove = [edge_id for edge_id, edge in self._edges.items() if
                           edge["s"] == node_id or edge["t"] == node_id]
        for edge_id in edges_to_remove:
            self.remove_edge(edge_id)

    def update_node(self, node_id, attributes=None, x=None, y=None, z=None):
        """
        Updates the attributes of a node.

        :param node_id: ID of the node to update.
        :type node_id: int or str
        :param attributes: Attributes to update.
        :type attributes: dict, optional
        :param x: X-coordinate to update.
        :type x: float, optional
        :param y: Y-coordinate to update.
        :type y: float, optional
        :param z: Z-coordinate to update.
        :type z: float, optional
        """
        if node_id not in self._nodes:
            raise NDExError(f"Node with ID {node_id} does not exist.")

        if attributes:
            processed_attributes = self._process_attributes('nodes', attributes)
            self._nodes[node_id]["v"].update(processed_attributes)
        if x is not None:
            self._nodes[node_id]["x"] = x
        if y is not None:
            self._nodes[node_id]["y"] = y
        if z is not None:
            self._nodes[node_id]["z"] = z

    def get_edges(self):
        """
        Retrieves the edges in the network.

        :return: Edges in the network.
        :rtype: dict
        """
        return self._edges

    def add_edge(self, edge_id=None, source=None, target=None, attributes=None):
        """
        Adds an edge to the network.

        :param edge_id: ID of the edge to add.
        :type edge_id: int or str
        :param source: Source node of the edge.
        :type source: int or str
        :param target: Target node of the edge.
        :type target: int or str
        :param attributes: Attributes of the edge.
        :type attributes: dict, optional
        """
        if source is None or target is None:
            raise NDExError("Edge must have source and target")
        if edge_id in self.get_edges().keys():
            raise NDExAlreadyExists(f"Edge with ID {edge_id} already exists.")
        else:
            edge_id = self._get_next_id('edges', edge_id)
        processed_attributes = self._process_attributes('edges', attributes)
        edge = {
            "id": edge_id,
            "s": self._check_and_cast_id(source),
            "t": self._check_and_cast_id(target),
            "v": processed_attributes
        }
        self._edges[edge_id] = edge
        return edge_id

    def get_edge(self, edge_id):
        """
        Retrieves an edge based on its ID.

        :param edge_id: ID of the edge to retrieve.
        :type edge_id: int or str
        :return: Edge with the given ID or None if not found.
        :rtype: dict or None
        """
        return self._edges.get(edge_id, None)

    def remove_edge(self, edge_id):
        """
        Removes an edge from the network based on its ID.

        :param edge_id: ID of the edge to remove.
        :type edge_id: int or str
        """
        if edge_id in self._edges:
            del self._edges[edge_id]

    def update_edge(self, edge_id, attributes=None):
        """
        Updates the attributes of an edge.

        :param edge_id: ID of the edge to update.
        :type edge_id: int or str
        :param attributes: New attributes for the edge.
        :type attributes: dict, optional
        """
        if edge_id not in self._edges:
            raise NDExError(f"Edge with ID {edge_id} does not exist.")

        if attributes:
            processed_attributes = self._process_attributes('edges', attributes)
            self._edges[edge_id]["v"].update(processed_attributes)

    def get_visual_properties(self):
        """
        Retrieves the visual properties of the network.

        :return: The visual properties of the network.
        :rtype: dict
        """
        return self._visual_properties

    def set_visual_properties(self, value):
        """
        Sets the visual properties for the network.

        :param value: New visual properties for the network.
        :type value: dict
        """
        self._visual_properties = value

    def get_node_bypasses(self):
        """
        Retrieves the node-specific visual property bypasses.

        :return: The node-specific visual property bypasses.
        :rtype: dict
        """
        return self._node_bypasses

    def add_node_bypass(self, node_id, value):
        """
        Adds a node-specific visual property bypass.

        :param node_id: ID of the node.
        :type node_id: str
        :param value: Visual property bypass value.
        :type value: Any
        """
        self._node_bypasses[node_id] = value

    def get_edge_bypasses(self):
        """
        Retrieves the edge-specific visual property bypasses.

        :return: The edge-specific visual property bypasses.
        :rtype: dict
        """
        return self._edge_bypasses

    def add_edge_bypass(self, edge_id, value):
        """
        Adds an edge-specific visual property bypass.

        :param edge_id: ID of the edge.
        :type edge_id: str
        :param value: Visual property bypass value.
        :type value: Any
        """
        self._edge_bypasses[edge_id] = value

    def get_opaque_aspects(self):
        """
        Retrieves the opaque aspects of the network.

        :return: The opaque aspects of the network.
        :rtype: list
        """
        return self._opaque_aspects

    def set_opaque_aspects(self, value):
        """
        Sets the opaque aspects for the network.

        :param value: New opaque aspects for the network.
        :type value: list
        """
        self._opaque_aspects = value

    def add_opaque_aspect(self, aspect):
        """
        Adds an opaque aspect to the list of opaque aspects.

        :param aspect: The opaque aspect to add.
        :type aspect: dict
        """
        self._opaque_aspects.append(aspect)

    def get_status(self):
        """
        Retrieves the status of the network.

        :return: The status of the network.
        :rtype: list
        """
        return self._status

    def set_status(self, value):
        """
        Sets the status for the network.

        :param value: New status for the network.
        :type value: dict
        """
        self._status = value

    def get_declared_type(self, aspect_name, attribute_name):
        """
        Retrieves the declared data type for a given aspect's attribute.

        :param aspect_name: The name of the aspect (e.g., 'nodes', 'edges').
        :type aspect_name: str
        :param attribute_name: The attribute whose declared data type needs to be retrieved.
        :type attribute_name: str
        :return: The declared data type or 'string' if not found.
        :rtype: str
        """
        return self.get_attribute_declarations().get(aspect_name, {}).get(attribute_name, {}).get('d', 'string')

    def get_alias(self, aspect_name, attribute_name):
        """
        Retrieves alias for a given aspect's attribute.

        :param aspect_name: The name of the aspect (e.g., 'nodes', 'edges').
        :type aspect_name: str
        :param attribute_name: The attribute whose declared data type needs to be retrieved.
        :type attribute_name: str
        :return: The alias or None if not found.
        :rtype: str
        """
        return self.get_attribute_declarations().get(aspect_name, {}).get(attribute_name, {}).get('a', None)

    def get_aliases(self, aspect):
        """
        Retrieves aliases for a given aspect's attributes.

        :param aspect: The name of the aspect (e.g., 'nodes', 'edges').
        :type aspect: str
        :return: Dictionary mapping aliases to attribute names.
        :rtype: dict
        """
        aliases = {}
        if self.get_attribute_declarations():
            declarations = self.get_attribute_declarations().get(aspect, {})
            for key, details in declarations.items():
                alias = details.get("a", None)
                if alias:
                    aliases[alias] = key
        return aliases

    def get_default_value(self, aspect_name, attribute_name):
        """
        Retrieves default value for a given aspect's attribute.

        :param aspect_name: The name of the aspect (e.g., 'nodes', 'edges').
        :type aspect_name: str
        :param attribute_name: The attribute whose declared data type needs to be retrieved.
        :type attribute_name: str
        :return: The default value or None if not found.
        :rtype: str
        """
        return self.get_attribute_declarations().get(aspect_name, {}).get(attribute_name, {}).get('v', None)

    def get_default_values(self, aspect):
        """
        Retrieves default values for a given aspect's attributes.

        :param aspect: The name of the aspect (e.g., 'nodes', 'edges').
        :type aspect: str
        :return: Dictionary mapping attribute names to their default values.
        :rtype: dict
        """
        default_values = {}
        if self.get_attribute_declarations():
            declarations = self.get_attribute_declarations().get(aspect, {})
            for key, details in declarations.items():
                default_value = details.get("v", None)
                if default_value:
                    default_values[key] = default_value
        return default_values

    def create_from_raw_cx2(self, cx2_data):
        """
        Loads and processes a raw CX2 data into structured data within the instance.

        :param cx2_data: Path to the CX2 file or a list representing CX2 data to be processed.
        :type cx2_data: str or list
        """
        if not cx2_data:
            raise NDExError('CX2 is empty')

        if isinstance(cx2_data, str):
            with open(cx2_data, 'r') as cx2_file:
                raw_data = json.load(cx2_file)
        elif isinstance(cx2_data, list):
            raw_data = cx2_data
        else:
            raise NDExInvalidCX2Error("Invalid input. The input parameter 'cx2_data' should be a file path (str) or a "
                                      "list.")

        for section in raw_data:
            if 'attributeDeclarations' in section:
                self.set_attribute_declarations(section['attributeDeclarations'][0])

            elif 'networkAttributes' in section:
                self.set_network_attributes(section['networkAttributes'][0])

            elif 'nodes' in section:
                for node in section['nodes']:
                    if "id" not in node:
                        raise NDExInvalidCX2Error('CX2 is not properly designed. Node requires id.')
                    self.add_node(node["id"], node.get("v", None), node.get("x", None), node.get("y", None),
                                  node.get("z", None))

            elif 'edges' in section:
                for edge in section['edges']:
                    if "id" not in edge or "s" not in edge or "t" not in edge:
                        raise NDExInvalidCX2Error('CX2 is not properly designed. Edge requires id, source (s) and '
                                                  'target (t).')
                    self.add_edge(edge["id"], edge["s"], edge["t"], edge.get("v", None))

            elif "visualProperties" in section:
                self.set_visual_properties(section["visualProperties"][0])
            elif "nodeBypasses" in section:
                for nodeBypass in section["nodeBypasses"]:
                    self.add_node_bypass(nodeBypass["id"], nodeBypass["v"])
            elif "edgeBypasses" in section:
                for edgeBypass in section["edgeBypasses"]:
                    self.add_edge_bypass(edgeBypass["id"], edgeBypass["v"])
            elif "metaData" in section or "CXVersion" in section:
                pass
            elif "status" in section:
                self.set_status(section["status"][0])
            else:
                self.add_opaque_aspect(section)

    def write_as_raw_cx2(self, output_path):
        """
        Writes data from CX2Network object to a raw CX2 formatted JSON file.

        :param output_path: Destination file path for the CX2 formatted output.
        :type output_path: str
        """

        with open(output_path, 'w') as output_file:
            output_data = self.to_cx2()
            json.dump(output_data, output_file, indent=4)

    def _get_meta_data(self):
        meta_data = []
        if self.get_attribute_declarations():
            meta_data.append({"elementCount": 1, "name": "attributeDeclarations"})
        if self.get_network_attributes():
            meta_data.append({"elementCount": 1, "name": "networkAttributes"})
        if self.get_nodes():
            meta_data.append({"elementCount": len(self.get_nodes()), "name": "nodes"})
        if self.get_edges():
            meta_data.append({"elementCount": len(self.get_edges()), "name": "edges"})
        if self.get_visual_properties():
            meta_data.append({"elementCount": 1, "name": "visualProperties"})
        if self.get_node_bypasses():
            meta_data.append({"elementCount": len(self.get_node_bypasses()), "name": "nodeBypasses"})
        if self.get_edge_bypasses():
            meta_data.append({"elementCount": len(self.get_edge_bypasses()), "name": "edgeBypasses"})
        for opaque_aspect in self.get_opaque_aspects():
            aspect_name = list(opaque_aspect.keys())[0]
            aspect_count = len(opaque_aspect[aspect_name])
            meta_data.append({"elementCount": aspect_count, "name": aspect_name})
        return meta_data

    @staticmethod
    def _clean_aspect_data(data_list, fields_to_check):
        """
        Cleans the given data list by removing unnecessary fields and adding specific ones.

        :param data_list: List of data dictionaries (nodes or edges).
        :param fields_to_check: List of fields to check in each data dictionary.
        :return: List of cleaned data dictionaries.
        """
        cleaned_data = []

        for item in data_list:
            clean_item = {k: v for k, v in item.items() if k not in fields_to_check}

            for field in fields_to_check:
                if field in item and item[field] is not None:
                    if field != 'v' or len(item[field]) > 0:
                        clean_item[field] = item[field]

            cleaned_data.append(clean_item)

        return cleaned_data

    def to_cx2(self):
        """
        Generates the CX2 representation of the current state of the instance.

        This method constructs a list structure representing the current state of the network
        in the CX2 format.

        :return: A list representing the CX2 formatted data of the current network state.
        :rtype: list
        """
        output_data = [
            {
                "CXVersion": "2.0",
                "hasFragments": False
            },
            {"metaData": self._get_meta_data()}]

        if self._attribute_declarations:
            filtered_attribute_declarations = {k: v for k, v in self.get_attribute_declarations().items()
                                               if v is not None and v != {}}
            output_data.append({"attributeDeclarations": [filtered_attribute_declarations]})

        if self._network_attributes:
            output_data.append({"networkAttributes": [self.get_network_attributes()]})

        nodes_list = self._replace_with_alias(list(self.get_nodes().values()), 'nodes')
        output_nodes = self._clean_aspect_data(nodes_list, ['x', 'y', 'z', 'v'])
        output_data.append({
            "nodes": output_nodes
        })

        edges_list = self._replace_with_alias(list(self.get_edges().values()), 'edges')
        output_edges = self._clean_aspect_data(edges_list, ['v'])
        output_data.append({
            "edges": output_edges
        })

        if self._visual_properties:
            output_data.append({"visualProperties": [self.get_visual_properties()]})

        if self._node_bypasses:
            output_node_bypasses = [{"id": k, "v": v} for k, v in self.get_node_bypasses().items()]
            output_data.append({"nodeBypasses": output_node_bypasses})

        if self._edge_bypasses:
            output_edge_bypasses = [{"id": k, "v": v} for k, v in self.get_edge_bypasses().items()]
            output_data.append({"edgeBypasses": output_edge_bypasses})

        output_data.extend(self._opaque_aspects)

        if self._status:
            output_data.append({"status": [self._status]})

        return output_data

    def _process_attributes(self, aspect_name, attributes):
        """
        Process the attributes for the given aspect by assigning default or declared values,
        converting them to declared types, and using full names instead of aliases.

        :param aspect_name: Name of the aspect (e.g., 'nodes', 'edges') for which attributes are being processed.
        :type aspect_name: str
        :param attributes: Dictionary of attributes to be processed.
        :type attributes: dict
        """
        processed_attrs = {}
        aliases = self.get_aliases(aspect_name)
        default_values = self.get_default_values(aspect_name)

        for key, default_value in default_values.items():
            actual_key = aliases.get(key, key)
            declared_type = self.get_declared_type(aspect_name, actual_key)
            processed_attrs[actual_key] = convert_value(declared_type, default_value)

        if attributes is not None:
            for key, value in attributes.items():
                actual_key = aliases.get(key, key)
                declared_type = self.get_declared_type(aspect_name, actual_key)
                if value is not None:
                    processed_attrs[actual_key] = convert_value(declared_type, value)

        self._generate_attribute_declarations_for_aspect(aspect_name, processed_attrs, aliases)
        return processed_attrs

    def _replace_with_alias(self, aspect_list, aspect_name):
        """
        Replaces attribute names in a data list with their corresponding aliases, if available.

        :param aspect_list: List of data items (e.g., nodes or edges) with attributes.
        :type aspect_list: list
        :param aspect_name: Name of the aspect (e.g., 'nodes', 'edges') for which aliases are to be applied.
        :type aspect_name: str
        """
        new_data = []
        aliases = self.get_aliases(aspect_name)

        reverse_aliases = {v: k for k, v in aliases.items()}

        for item in aspect_list:
            new_item = item.copy()
            if 'v' in new_item:
                for attr in list(new_item['v'].keys()):
                    if attr in reverse_aliases:
                        new_item['v'][reverse_aliases[attr]] = new_item['v'].pop(attr)
            new_data.append(new_item)

        return new_data


class CX2NetworkFactory(object):
    """
    Base class for Factory classes that create
    :py:class:`~ndex2.cx2.CX2Network` objects
    """

    def __init__(self):
        pass

    def get_cx2network(self, input_data=None) -> CX2Network:
        """
        Creates :py:class:`~ndex2.cx2.CX2Network`

        .. warning::

            Always raises NotImplementedError

        :param input_data: Optional input data for used to generate
                           network
        :raises NotImplementedError: Always raised. Subclasses should implement
        :return: Generated network
        :rtype: :py:class:`~ndex2.cx2.CX2Network`
        """
        raise NotImplementedError('Should be implemented by subclasses')


class NoStyleCXToCX2NetworkFactory(CX2NetworkFactory):
    """
    Creates :py:class:`~ndex2.cx2.CX2Network` network from
    CX data or :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
    """

    def __init__(self):
        super(NoStyleCXToCX2NetworkFactory, self).__init__()

    @staticmethod
    def _translate_network_attributes_to_cx2(network_attributes):
        """
        Translates network attributes into CX2 format.

        :param network_attributes: Attributes to translate.
        :type network_attributes: list
        :return: Translated network attributes.
        :rtype: dict
        """
        return {item['n']: item['v'] for item in network_attributes}

    @staticmethod
    def _generate_attribute_declarations(network_attributes, nodes, node_attributes, edges, edge_attributes):
        """
        Generates attribute declarations based on provided attributes, nodes, and edges.

        :param network_attributes: Network attributes.
        :type network_attributes: list
        :param nodes: Nodes in the network.
        :type nodes: dict
        :param node_attributes: Node attributes.
        :type node_attributes: dict
        :param edges: Edges in the network.
        :type edges: dict
        :param edge_attributes: Edge attributes.
        :type edge_attributes: dict
        :return: Generated attribute declarations.
        :rtype: dict
        """
        attribute_declarations = {
            "networkAttributes": {item['n']: {'d': item.get('d', 'string')} for item in network_attributes},
            "nodes": {},
            "edges": {}
        }

        node_internal_attributes = {key for val in nodes.values() for key in val}
        if 'n' in node_internal_attributes:
            attribute_declarations['nodes']['name'] = {'a': 'n', 'd': 'string'}
        if 'r' in node_internal_attributes:
            attribute_declarations['nodes']['represents'] = {'a': 'r', 'd': 'string'}

        for attr_list in node_attributes.values():
            for attr in attr_list:
                attribute_declarations['nodes'][attr['n']] = {'d': attr.get('d', 'string')}

        edge_internal_attributes = {key for val in edges.values() for key in val}
        if 'i' in edge_internal_attributes:
            attribute_declarations['edges']['interaction'] = {'a': 'i', 'd': 'string'}

        for attr_list in edge_attributes.values():
            for attr in attr_list:
                attribute_declarations['edges'][attr['n']] = {'d': attr.get('d', 'string')}

        return attribute_declarations

    @staticmethod
    def _process_attributes_for_cx2(entity, attributes, expected_keys=None):
        """
        Processes attributes for conversion to CX2 format.

        :param entity: The entity to process attributes for.
        :type entity: dict
        :param attributes: Attributes to process.
        :type attributes: dict
        :param expected_keys: Optional list of expected keys in the entity.
        :type expected_keys: list, optional
        :return: Processed attributes.
        :rtype: dict
        """
        attr_vals = {}
        if expected_keys:
            attr_vals = {key: entity[key] for key in expected_keys if key in entity}
        if attributes.get(entity['@id']):
            attr_vals.update({attr['n']: attr['v'] for attr in attributes[entity['@id']]})
        return attr_vals

    def get_cx2network(self, input_data=None) -> CX2Network:
        """
        Creates :py:class:`~ndex2.cx2.CX2Network` from
        CX data or :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        but does **NOT** convert the style associated with input network

        .. note::

            Style is NOT converted by this call

        :param input_data: Optional input data used to generate network
        :type input_data: str, list or :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        :return: Generated network
        :rtype: :py:class:`~ndex2.cx2.CX2Network`
        """
        if isinstance(input_data, NiceCXNetwork):
            network = input_data
        elif isinstance(input_data, str):
            network = create_nice_cx_from_file(input_data)
        else:
            network = create_nice_cx_from_raw_cx(input_data)

        cx2network_obj = CX2Network()
        cx2network_obj.set_attribute_declarations(
            self._generate_attribute_declarations(
                network.networkAttributes, network.nodes, network.nodeAttributes, network.edges, network.edgeAttributes
            )
        )

        cx2network_obj.set_network_attributes(self._translate_network_attributes_to_cx2(network.networkAttributes))

        for node, layout in zip_longest(network.nodes.values(), network.opaqueAspects.get('cartesianLayout', []),
                                        fillvalue={}):
            attr_val = self._process_attributes_for_cx2(node, network.nodeAttributes, ['n', 'r'])
            cx2network_obj.add_node(node['@id'], attr_val, layout.get('x'), layout.get('y'), layout.get('z'))

        for edge in network.edges.values():
            attr_val = self._process_attributes_for_cx2(edge, network.edgeAttributes, ['i'])
            cx2network_obj.add_edge(edge['@id'], edge['s'], edge['t'], attr_val)

        cx2network_obj.set_status({'error': '', 'success': True})

        return cx2network_obj


class RawCX2NetworkFactory(CX2NetworkFactory):
    """
    Factory class responsible for creating :py:class:`~ndex2.cx2.CX2Network` instances
    directly from raw CX2 formatted data.
    """

    def __init__(self):
        super(RawCX2NetworkFactory, self).__init__()

    def get_cx2network(self, input_data=None) -> CX2Network:
        """
        Converts the provided raw CX2 data into a :py:class:`~ndex2.cx2.CX2Network` object.

        :param input_data: Raw CX2 data to be converted.
        :type input_data: dict or similar mapping type
        :return: A constructed :py:class:`~ndex2.cx2.CX2Network` object from the input data.
        :rtype: :py:class:`~ndex2.cx2.CX2Network`
        """
        cx2network_obj = CX2Network()
        cx2network_obj.create_from_raw_cx2(input_data)
        return cx2network_obj
