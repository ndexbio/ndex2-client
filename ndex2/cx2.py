import json
from copy import deepcopy

import networkx as nx
import pandas as pd

from ndex2 import create_nice_cx_from_raw_cx, create_nice_cx_from_file, constants
from ndex2.exceptions import NDExInvalidCX2Error, NDExAlreadyExists, NDExError, NDExNotFoundError
from ndex2.nice_cx_network import NiceCXNetwork
from itertools import zip_longest
from collections.abc import Iterable


def convert_value(dtype, value):
    """
    Converts a value to its appropriate data type based on its declared type.

    :param dtype: Declared data type for the value.
    :type dtype: str
    :param value: Value to be converted.
    :type value: any
    """
    if dtype not in constants.VALID_ATTRIBUTE_DATATYPES:
        raise NDExInvalidCX2Error(f'Data type {dtype} is invalid in CX2 format')

    if dtype.startswith("list_of_"):
        if not isinstance(value, list):
            raise NDExInvalidCX2Error('Declared value of attribute data does not match the actual value type: '
                                      'list expected')
        elem_type = dtype.split("_")[2]
        if elem_type not in [constants.STRING_DATATYPE, constants.LONG_DATATYPE, constants.INTEGER_DATATYPE,
                             constants.DOUBLE_DATATYPE, constants.BOOLEAN_DATATYPE]:
            raise NDExInvalidCX2Error(f'Data type {dtype} is invalid in CX2 format')
        return [convert_value(elem_type, v) for v in value]

    try:
        if dtype == constants.INTEGER_DATATYPE or dtype == constants.LONG_DATATYPE:
            return int(value)
        elif dtype == constants.DOUBLE_DATATYPE:
            return float(value)
        elif dtype == constants.BOOLEAN_DATATYPE:
            if isinstance(value, bool):
                return value
            else:
                return value.lower() == 'true'
        else:
            return str(value)
    except ValueError as err:
        raise NDExInvalidCX2Error('Declared value of attribute data does not match the actual value type: ' + str(err))


class CX2Network(object):
    """
    A representation of the `CX2 (Cytoscape Exchange) <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)>`__ network format.

    This class provides functionality to read, process, and write data in the `CX2 format <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)/>`__.
    It facilitates the structured access and manipulation of network data elements such as nodes, edges,
    attributes, and visual properties.

    The class maintains internal data structures that hold network data and provides methods to:

    1. Load data from raw `CX2 <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)>`__ files.

    2. Generate the `CX2 <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)>`__ representation of the current state.

    3. Write the current state to a `CX2 <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)>`__ formatted file.

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
            A list of other aspects in the `CX2 format <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)>`__
            which don't have a defined structure in this class.
        - ``status``
            A dictionary representing the network's status.

    .. versionadded:: 3.6.0
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
        self._int_id_generator = {constants.NODES_ASPECT: 0, constants.EDGES_ASPECT: 0}

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
            return_id = validated_aspect_id
        else:
            return_id = self._int_id_generator[aspect]
        self._int_id_generator[aspect] += 1
        return return_id

    @staticmethod
    def _check_and_cast_id(aspect_id):
        """
        Validates and converts a given aspect ID to an integer. The aspect ID can be either an integer or
        a string representation of an integer. If the aspect ID is neither, or if the string cannot be
        converted to an integer, an :py:class:`~ndex2.exceptions.NDExInvalidCX2Error` is raised.

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

    def _get_cx2_type(self, value):
        """
        Converts the type of the provided value to `CX2 <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)>`__ type from Python type. For lists,
        it also determines the type of the list's first element.

        :param value: The value for which the type needs to be determined.
        :type value: int, float, bool, list, or any other supported type.
        :return: The custom `CX2 <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)>`__ type of the value.
        :rtype: str
        :raises ValueError: If the value is of an unsupported type.
        """
        if isinstance(value, bool):
            return constants.BOOLEAN_DATATYPE
        elif isinstance(value, int):
            if 2 ** 31 - 1 >= value >= -2 ** 31:
                return constants.INTEGER_DATATYPE
            else:
                return constants.LONG_DATATYPE
        elif isinstance(value, float):
            return constants.DOUBLE_DATATYPE
        elif isinstance(value, str):
            return constants.STRING_DATATYPE
        elif isinstance(value, list):
            if value:
                inner_type = self._get_cx2_type(value[0])
                return f"list_of_{inner_type}"
        else:
            raise ValueError(f"Unsupported value type: {type(value)}")

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
                        constants.ATTR_DATATYPE: self._get_cx2_type(value)
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
        if key not in self._network_attributes:
            raise NDExNotFoundError(f"Network attribute '{key}' does not exist.")

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
        :raises NDExAlreadyExists: If node with **node_id** already exists
        """
        if node_id in self.get_nodes().keys():
            raise NDExAlreadyExists(f"Node with ID {node_id} already exists.")
        else:
            node_id = self._get_next_id(constants.NODES_ASPECT, node_id)
        processed_attributes = self._process_attributes(constants.NODES_ASPECT, attributes)
        node = {
            constants.ASPECT_ID: node_id,
            constants.ASPECT_VALUES: processed_attributes,
            constants.LAYOUT_X: x,
            constants.LAYOUT_Y: y,
            constants.LAYOUT_Z: z
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
        if node_id not in self._nodes:
            raise NDExNotFoundError(f"Node {node_id} does not exist.")

        del self._nodes[node_id]

        edges_to_remove = [edge_id for edge_id, edge in self._edges.items() if
                           edge[constants.EDGE_SOURCE] == node_id or edge[constants.EDGE_TARGET] == node_id]
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
        :raises NDExError: if node with **node_id** passed in does not exist
        """
        if node_id not in self._nodes:
            raise NDExError(f"Node with ID {node_id} does not exist.")

        if attributes:
            processed_attributes = self._process_attributes(constants.NODES_ASPECT, attributes)
            self._nodes[node_id][constants.ASPECT_VALUES].update(processed_attributes)
        if x is not None:
            self._nodes[node_id][constants.LAYOUT_X] = x
        if y is not None:
            self._nodes[node_id][constants.LAYOUT_Y] = y
        if z is not None:
            self._nodes[node_id][constants.LAYOUT_Z] = z

    def set_node_attribute(self, node_id, attribute, value):
        self.update_node(node_id, {attribute: value})

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
            edge_id = self._get_next_id(constants.EDGES_ASPECT, edge_id)
        processed_attributes = self._process_attributes(constants.EDGES_ASPECT, attributes)
        edge = {
            constants.ASPECT_ID: edge_id,
            constants.EDGE_SOURCE: self._check_and_cast_id(source),
            constants.EDGE_TARGET: self._check_and_cast_id(target),
            constants.ASPECT_VALUES: processed_attributes
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
        if edge_id not in self._edges:
            raise NDExNotFoundError(f"Edge {edge_id} does not exist.")

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
            processed_attributes = self._process_attributes(constants.EDGES_ASPECT, attributes)
            self._edges[edge_id][constants.ASPECT_VALUES].update(processed_attributes)

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

    def get_declared_type(self, aspect_name, attribute_name, attribute_value=None):
        """
        Retrieves the declared data type for a given aspect's attribute.

        :param aspect_name: The name of the aspect (e.g., 'nodes', 'edges').
        :type aspect_name: str
        :param attribute_name: The attribute whose declared data type needs to be retrieved.
        :type attribute_name: str
        :param attribute_value: Actual value that will be used to infer data type if data type
                                has not yet been defined for attribute
        :type attribute_value: str, int, bool, float, list
        :return: The declared data type or 'string' if not found.
        :rtype: str
        """
        declared_type = (self.get_attribute_declarations().get(aspect_name, {}).get(attribute_name, {})
                         .get(constants.ATTR_DATATYPE))
        if declared_type is not None:
            return declared_type
        elif attribute_value is not None:
            return self._get_cx2_type(attribute_value)
        else:
            return constants.STRING_DATATYPE

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
        return self.get_attribute_declarations().get(aspect_name, {}).get(attribute_name, {}).get(
            constants.ASPECT_VALUES, None)

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
                default_value = details.get(constants.ASPECT_VALUES, None)
                if default_value:
                    default_values[key] = default_value
        return default_values

    def create_from_raw_cx2(self, cx2_data):
        """
        Loads and processes a raw `CX2 <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)>`__
        data into structured data within the instance.

        :param cx2_data: Path to the `CX2 <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)>`__
                         file or a list representing `CX2 <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)>`__ data to be processed.
        :type cx2_data: str or list
        :raises NDExError: If **cx2_data** is ``None``
        :raises NDExInvalidCX2Error: If there is an error parsing **cx2_data**
        """
        if not cx2_data:
            raise NDExError('CX2 is empty')

        if isinstance(cx2_data, str):
            with open(cx2_data, constants.NODE_REPRESENTS) as cx2_file:
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

            elif constants.NODES_ASPECT in section:
                for node in section[constants.NODES_ASPECT]:
                    if constants.ASPECT_ID not in node:
                        raise NDExInvalidCX2Error('CX2 is not properly designed. Node requires id.')
                    self.add_node(node[constants.ASPECT_ID], node.get(constants.ASPECT_VALUES, None),
                                  node.get(constants.LAYOUT_X, None),
                                  node.get(constants.LAYOUT_Y, None),
                                  node.get(constants.LAYOUT_Z, None))

            elif constants.EDGES_ASPECT in section:
                for edge in section[constants.EDGES_ASPECT]:
                    if constants.ASPECT_ID not in edge or constants.EDGE_SOURCE not in edge or constants.EDGE_TARGET not in edge:
                        raise NDExInvalidCX2Error('CX2 is not properly designed. Edge requires id, source (s) and '
                                                  'target (t).')
                    self.add_edge(edge[constants.ASPECT_ID], edge[constants.EDGE_SOURCE], edge[constants.EDGE_TARGET],
                                  edge.get(constants.ASPECT_VALUES, None))

            elif "visualProperties" in section:
                self.set_visual_properties(section["visualProperties"][0])
            elif "nodeBypasses" in section:
                for nodeBypass in section["nodeBypasses"]:
                    self.add_node_bypass(nodeBypass[constants.ASPECT_ID], nodeBypass[constants.ASPECT_VALUES])
            elif "edgeBypasses" in section:
                for edgeBypass in section["edgeBypasses"]:
                    self.add_edge_bypass(edgeBypass[constants.ASPECT_ID], edgeBypass[constants.ASPECT_VALUES])
            elif "metaData" in section or "CXVersion" in section:
                pass
            elif "status" in section:
                self.set_status(section["status"][0])
            else:
                self.add_opaque_aspect(section)

    def write_as_raw_cx2(self, output_path):
        """
        Writes data from CX2Network object to a raw `CX2 formatted <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)>`__ JSON file.

        :param output_path: Destination file path for the `CX2 formatted <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)>`__ output.
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
            meta_data.append({"elementCount": len(self.get_nodes()), "name": constants.NODES_ASPECT})
        if self.get_edges():
            meta_data.append({"elementCount": len(self.get_edges()), "name": constants.EDGES_ASPECT})
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
                    if field != constants.ASPECT_VALUES or len(item[field]) > 0:
                        clean_item[field] = item[field]

            cleaned_data.append(clean_item)

        return cleaned_data

    def to_cx2(self):
        """
        Generates the `CX2 <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)>`__ representation of the current state of the instance.

        This method constructs a list structure representing the current state of the network
        in the `CX2 format. <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)>`__

        :return: A list representing the `CX2 <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)>`__ formatted data of the current network state.
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

        nodes_list = self._replace_with_alias(list(self.get_nodes().values()), constants.NODES_ASPECT)
        output_nodes = self._clean_aspect_data(nodes_list, [constants.LAYOUT_X, constants.LAYOUT_Y,
                                                            constants.LAYOUT_Z, constants.ASPECT_VALUES])
        output_data.append({
            constants.NODES_ASPECT: output_nodes
        })

        edges_list = self._replace_with_alias(list(self.get_edges().values()), constants.EDGES_ASPECT)
        output_edges = self._clean_aspect_data(edges_list, [constants.ASPECT_VALUES])
        output_data.append({
            constants.EDGES_ASPECT: output_edges
        })

        if self._visual_properties:
            output_data.append({"visualProperties": [self.get_visual_properties()]})

        if self._node_bypasses:
            output_node_bypasses = [{constants.ASPECT_ID: k, constants.ASPECT_VALUES: v} for k, v in
                                    self.get_node_bypasses().items()]
            output_data.append({"nodeBypasses": output_node_bypasses})

        if self._edge_bypasses:
            output_edge_bypasses = [{constants.ASPECT_ID: k, constants.ASPECT_VALUES: v} for k, v in
                                    self.get_edge_bypasses().items()]
            output_data.append({"edgeBypasses": output_edge_bypasses})

        output_data.extend(self._opaque_aspects)

        if self._status:
            output_data.append({"status": [self._status]})
        else:
            output_data.append({"status": [{'error': '', 'success': True}]})

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
            declared_type = self.get_declared_type(aspect_name, actual_key, default_value)
            processed_attrs[actual_key] = convert_value(declared_type, default_value)

        if attributes is not None:
            for key, value in attributes.items():
                actual_key = aliases.get(key, key)
                declared_type = self.get_declared_type(aspect_name, actual_key, value)
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
            new_item = deepcopy(item)
            if constants.ASPECT_VALUES in new_item:
                for attr in list(new_item[constants.ASPECT_VALUES].keys()):
                    if attr in reverse_aliases:
                        new_item[constants.ASPECT_VALUES][reverse_aliases[attr]] = new_item[
                            constants.ASPECT_VALUES].pop(attr)
            new_data.append(new_item)

        return new_data


class CX2NetworkFactory(object):
    """
    Base class for Factory classes that create
    :py:class:`~ndex2.cx2.CX2Network` objects

    .. versionadded:: 3.6.0

    """

    def __init__(self):
        pass

    def get_cx2network(self, input_data=None) -> CX2Network:
        """
        Defines method that creates :py:class:`~ndex2.cx2.CX2Network`

        .. warning::

            Subclasses should implement, this method always raises :py:class:`NotImplementedError`

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
    `CX <https://cytoscape.org/cx/specification/cytoscape-exchange-format-specification-(version-1)>`__
    data or :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`

    .. versionadded:: 3.6.0
    """

    def __init__(self):
        super(NoStyleCXToCX2NetworkFactory, self).__init__()

    @staticmethod
    def _translate_network_attributes_to_cx2(network_attributes):
        """
        Translates network attributes into `CX2 <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)>`__.

        :param network_attributes: Attributes to translate.
        :type network_attributes: list
        :return: Translated network attributes.
        :rtype: dict
        """
        return {item[constants.ATTR_NAME]: item[constants.ASPECT_VALUES] for item in network_attributes}

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
            "networkAttributes": {item[constants.ATTR_NAME]: {constants.ATTR_DATATYPE: item.get(constants.ATTR_DATATYPE,
                                                                                                constants.STRING_DATATYPE)}
                                  for item in network_attributes},
            constants.NODES_ASPECT: {},
            constants.EDGES_ASPECT: {}
        }

        node_internal_attributes = {key for val in nodes.values() for key in val}
        if constants.NODE_NAME in node_internal_attributes:
            attribute_declarations[constants.NODES_ASPECT]['name'] = \
                {'a': constants.NODE_NAME, constants.ATTR_DATATYPE: constants.STRING_DATATYPE}
        if constants.NODE_REPRESENTS in node_internal_attributes:
            attribute_declarations[constants.NODES_ASPECT]['represents'] = \
                {'a': constants.NODE_REPRESENTS, constants.ATTR_DATATYPE: constants.STRING_DATATYPE}

        for attr_list in node_attributes.values():
            for attr in attr_list:
                attribute_declarations[constants.NODES_ASPECT][attr[constants.ATTR_NAME]] = \
                    {constants.ATTR_DATATYPE: attr.get(constants.ATTR_DATATYPE, constants.STRING_DATATYPE)}

        edge_internal_attributes = {key for val in edges.values() for key in val}
        if constants.EDGE_INTERACTION in edge_internal_attributes:
            attribute_declarations[constants.EDGES_ASPECT]['interaction'] = \
                {'a': constants.EDGE_INTERACTION, constants.ATTR_DATATYPE: constants.STRING_DATATYPE}

        for attr_list in edge_attributes.values():
            for attr in attr_list:
                attribute_declarations[constants.EDGES_ASPECT][attr[constants.ATTR_NAME]] = \
                    {constants.ATTR_DATATYPE: attr.get(constants.ATTR_DATATYPE, constants.STRING_DATATYPE)}

        return attribute_declarations

    @staticmethod
    def _process_attributes_for_cx2(entity, attributes, expected_keys=None):
        """
        Processes attributes for conversion to `CX2 <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)>`__.

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
            attr_vals.update({attr[constants.ATTR_NAME]: attr[constants.ASPECT_VALUES]
                              for attr in attributes[entity['@id']]})
        return attr_vals

    def get_cx2network(self, input_data=None) -> CX2Network:
        """
        Creates :py:class:`~ndex2.cx2.CX2Network` from
        `CX <https://cytoscape.org/cx/specification/cytoscape-exchange-format-specification-(version-1)>`__ data
        or :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        but does **NOT** convert the style associated with input network

        .. note::

            Style is **NOT** converted by this call

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

        for node, layout in zip_longest(network.nodes.values(), network.opaqueAspects.get(
                constants.CARTESIAN_LAYOUT_ASPECT, []),
                                        fillvalue={}):
            attr_val = self._process_attributes_for_cx2(node, network.nodeAttributes,
                                                        [constants.ATTR_NAME, constants.NODE_REPRESENTS])
            cx2network_obj.add_node(node['@id'], attr_val, layout.get(constants.LAYOUT_X),
                                    layout.get(constants.LAYOUT_Y), layout.get(constants.LAYOUT_Z))

        for edge in network.edges.values():
            attr_val = self._process_attributes_for_cx2(edge, network.edgeAttributes, [constants.EDGE_INTERACTION])
            cx2network_obj.add_edge(edge['@id'], edge[constants.EDGE_SOURCE], edge[constants.EDGE_TARGET], attr_val)

        cx2network_obj.set_status({'error': '', 'success': True})

        return cx2network_obj


class RawCX2NetworkFactory(CX2NetworkFactory):
    """
    Factory class responsible for creating :py:class:`~ndex2.cx2.CX2Network` instances
    directly from raw `CX2 <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)>`__.

    .. versionadded:: 3.6.0
    """

    def __init__(self):
        super(RawCX2NetworkFactory, self).__init__()

    def get_cx2network(self, input_data=None) -> CX2Network:
        """
        Converts the provided raw `CX2 <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)>`__
        into a :py:class:`~ndex2.cx2.CX2Network` object.

        :param input_data: Raw `CX2 <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)>`__ to be converted.
        :type input_data: dict or similar mapping type
        :return: A constructed :py:class:`~ndex2.cx2.CX2Network` object from the input data.
        :rtype: :py:class:`~ndex2.cx2.CX2Network`
        """
        cx2network_obj = CX2Network()
        cx2network_obj.create_from_raw_cx2(input_data)
        return cx2network_obj


class NetworkXToCX2NetworkFactory(CX2NetworkFactory):
    """
    Factory class responsible for creating :py:class:`~ndex2.cx2.CX2Network` instances
    from :py:class:`networkx.Graph`

    .. versionadded:: 3.7.0
    """

    def __init__(self):
        super(NetworkXToCX2NetworkFactory, self).__init__()

    def get_cx2network(self, input_data=None):
        """
        Creates :py:class:`~ndex2.cx2.CX2Network` from :py:class:`networkx.Graph`
        object
        :param input_data: Optional input data used to generate network
        :type input_data: :py:class:`networkx.Graph`, :py:class:`networkx.DiGraph`
        :return: Generated network
        :rtype: :py:class:`~ndex2.cx2.CX2Network`
        """
        if input_data is None:
            raise Exception('Networkx input is empty')

        if not isinstance(input_data, (nx.Graph, nx.DiGraph, nx.MultiDiGraph)):
            raise TypeError("input_data must be a networkx.Graph, networkx.DiGraph, or networkx.MultiDiGraph object")

        cx2network_obj = CX2Network()

        for node_id, node_data in input_data.nodes(data=True):
            x = node_data.pop('x', None)
            y = node_data.pop('y', None)
            z = node_data.pop('z', None)
            cx2network_obj.add_node(node_id=node_id, attributes=node_data, x=x, y=y, z=z)

        for source, target, edge_data in input_data.edges(data=True):
            cx2network_obj.add_edge(source=source, target=target, attributes=edge_data)

        for attr_key, attr_value in input_data.graph.items():
            cx2network_obj.add_network_attribute(key=attr_key, value=attr_value)

        return cx2network_obj


class PandasDataFrameToCX2NetworkFactory(CX2NetworkFactory):
    """
    Factory class for converting a Pandas DataFrame into a CX2Network object.

    .. versionadded:: 3.7.0
    """
    def __init__(self):
        """
        Constructor
        """
        super(PandasDataFrameToCX2NetworkFactory, self).__init__()

    def get_cx2network(self, input_data=None) -> CX2Network:
        """
        Converts a given Pandas DataFrame into a CX2Network object. The DataFrame should
        contain columns 'source' and 'target' to represent source node and target node of edge
        , and may contain additional columns for edge and node attributes.

        :param input_data: The Pandas DataFrame to be converted into CX2Network.
        :type input_data: pd.DataFrame
        :return: A CX2Network object :py:class:`~ndex2.cx2.CX2Network`
        :rtype: CX2Network
        :raises NDExError: If the input DataFrame is None or does not have the necessary columns.
        """
        if input_data is None:
            raise Exception('DataFrame input is empty')

        if not isinstance(input_data, pd.DataFrame):
            raise NDExError("Input data must be a Pandas DataFrame")

        cx2network = CX2Network()

        for index, row in input_data.iterrows():
            source = row.get('source')
            target = row.get('target')

            if source is None or target is None:
                raise NDExError("Missing 'source' or 'target' columns in the DataFrame")

            source_attrs = {}
            target_attrs = {}
            edge_attrs = {}
            for col, value in row.items():
                if not isinstance(value, Iterable) and pd.isna(value):
                    continue
                if col.startswith('source_'):
                    source_attrs[col[7:]] = value
                elif col.startswith('target_'):
                    target_attrs[col[7:]] = value
                edge_attrs[col] = value
            if source not in cx2network.get_nodes():
                cx2network.add_node(node_id=source, x=source_attrs.pop('x', None), y=source_attrs.pop('y', None),
                                    z=source_attrs.pop('z', None), attributes=source_attrs)
            if target not in cx2network.get_nodes():
                cx2network.add_node(node_id=target, x=target_attrs.pop('x', None), y=target_attrs.pop('y', None),
                                    z=target_attrs.pop('z', None), attributes=target_attrs)
            cx2network.add_edge(source=source, target=target, attributes=edge_attrs)

        return cx2network


class CX2NetworkXFactory(object):
    """
    A factory class for creating NetworkX Graph objects from CX2Network data.

    .. versionadded:: 3.7.0
    """

    def __init__(self):
        """
        Constructor
        """
        pass

    def get_graph(self, cx2network, networkx_graph=None):
        """
        Creates NetworkX Graph object which can
        be one of the multiple types of Graph objects

        :param cx2network: Network to create networkx graph from
        :type cx2network: :py:class:`~ndex2.cx.CX2Network`
        :param networkx_graph: Empty networkx graph to populate
        :type networkx_graph: :class:`networkx.MultiDiGraph`, :class:`networkx.DiGraph`
        :return: networkx Graph object
        :rtype: :class:`networkx.MultiDiGraph`, :class:`networkx.DiGraph`
        """
        if cx2network is None:
            raise NDExError('input network is None')

        if networkx_graph is None:
            networkx_graph = nx.MultiDiGraph()

        for node_id, node_data in cx2network.get_nodes().items():
            attrs = node_data.get('v', {})
            if 'x' in node_data:
                attrs['x'] = node_data['x']
            if 'y' in node_data:
                attrs['y'] = node_data['y']
            if 'z' in node_data:
                attrs['z'] = node_data['z']
            networkx_graph.add_node(node_id, **attrs)

        for edge_id, edge_data in cx2network.get_edges().items():
            source = edge_data['s']
            target = edge_data['t']
            attrs = edge_data.get('v', {})
            networkx_graph.add_edge(source, target, **attrs)

        for attr, value in cx2network.get_network_attributes().items():
            networkx_graph.graph[attr] = value

        return networkx_graph


class PandasDataFrameFactory:
    """
    Factory class for converting a CX2Network object into a Pandas DataFrame.

    .. versionadded:: 3.7.0
    """
    def __init__(self):
        """
        Constructor
        """
        pass

    def get_dataframe(self, cx2network):
        """
        Converts a given CX2Network object into a Pandas DataFrame. The
        DataFrame will contain columns for 'source' and 'target' nodes
        of each edge, along with other edge and node attributes. Node
        attributes will be prefixed with ``source_`` and ``target_``
        respectively. If coordinates exist on the nodes they will be
        added as
        ``source_x, source_y, source_z, target_x, target_y, target_z``

        :param cx2network: The CX2Network object to be converted into a DataFrame.
        :type cx2network: CX2Network
        :return: A Pandas DataFrame representing the network data from CX2Network.
        :rtype: pd.DataFrame
        :raises NDExError: If the input CX2Network is None or not an instance of CX2Network.
        """
        if cx2network is None:
            raise NDExError('input network is None')

        if not isinstance(cx2network, CX2Network):
            raise NDExError("Input must be a CX2Network object")

        rows = []

        for edge_id, edge in cx2network.get_edges().items():
            row = {}
            source_node_id = edge.get('s')
            target_node_id = edge.get('t')

            row['source'] = source_node_id
            row['target'] = target_node_id

            source_node_attrs = cx2network.get_node(source_node_id)
            target_node_attrs = cx2network.get_node(target_node_id)

            # Add node attributes with prefixes to the row
            for attr_key, attr_value in source_node_attrs.get('v', {}).items():
                row[f'source_{attr_key}'] = attr_value
            for attr_key, attr_value in target_node_attrs.get('v', {}).items():
                row[f'target_{attr_key}'] = attr_value

            # Add coordinates if available
            if 'x' in source_node_attrs:
                row['source_x'] = source_node_attrs['x']
            if 'y' in source_node_attrs:
                row['source_y'] = source_node_attrs['y']
            if 'z' in source_node_attrs:
                row['source_z'] = source_node_attrs['z']
            if 'x' in target_node_attrs:
                row['target_x'] = target_node_attrs['x']
            if 'y' in target_node_attrs:
                row['target_y'] = target_node_attrs['y']
            if 'z' in target_node_attrs:
                row['target_z'] = target_node_attrs['z']

            for attr_key, attr_value in edge.get('v', {}).items():
                row[attr_key] = attr_value

            rows.append(row)

        return pd.DataFrame(rows)
