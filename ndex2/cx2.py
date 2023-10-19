import json

from ndex2 import create_nice_cx_from_raw_cx, create_nice_cx_from_file
from ndex2.nice_cx_network import NiceCXNetwork


def convert_value(dtype, value):
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
        if isinstance(value, bool):
            return value
        else:
            return True if value.lower() == 'true' else False
    elif dtype.startswith("list_of_"):
        elem_type = dtype.split("_")[2]
        return [convert_value(elem_type, v) for v in value]
    else:
        return value


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
        self._attribute_declarations = None
        self._network_attributes = {}
        self._nodes = {}
        self._edges = {}
        self._visual_properties = []
        self._node_bypasses = {}
        self._edge_bypasses = {}
        self._opaque_aspects = []
        self._status = {}

    def get_attribute_declarations(self):
        return self._attribute_declarations

    def set_attribute_declarations(self, value):
        self._attribute_declarations = value

    def get_network_attributes(self):
        return self._network_attributes

    def set_network_attributes(self, network_attrs):
        processed_network_attrs = {}
        for key, value in network_attrs.items():
            declared_type = self.get_declared_type('networkAttributes', key)
            processed_network_attrs[key] = convert_value(declared_type, value)
        self._network_attributes = processed_network_attrs

    def get_nodes(self):
        return self._nodes

    def add_node(self, node_id, attributes=None, x=None, y=None, z=None):
        """Adds a node to the network."""
        processed_attributes = self._process_attributes('nodes', attributes)
        node = {
            "id": node_id,
            "v": processed_attributes or {},
            "x": x,
            "y": y,
            "z": z
        }
        self._nodes[node_id] = node

    def get_node(self, node_id):
        """Retrieves a node based on its ID."""
        return self._nodes.get(node_id, None)

    def remove_node(self, node_id):
        """Removes a node and checks for dangling edges."""
        # Remove the node
        if node_id in self._nodes:
            del self._nodes[node_id]

        edges_to_remove = [edge_id for edge_id, edge in self._edges.items() if
                           edge["s"] == node_id or edge["t"] == node_id]
        for edge_id in edges_to_remove:
            self.remove_edge(edge_id)

    def update_node(self, node_id, attributes=None, x=None, y=None, z=None):
        """Updates the attributes of a node."""
        if node_id in self._nodes:
            if attributes:
                self._nodes[node_id]["v"].update(attributes)
            if x is not None:
                self._nodes[node_id]["x"] = x
            if y is not None:
                self._nodes[node_id]["y"] = y
            if z is not None:
                self._nodes[node_id]["z"] = z

    def get_edges(self):
        return self._edges

    def add_edge(self, edge_id, source, target, attributes=None):
        """Adds an edge to the network."""
        processed_attributes = self._process_attributes('edges', attributes)
        edge = {
            "id": edge_id,
            "s": source,
            "t": target,
            "v": processed_attributes or {}
        }
        self._edges[edge_id] = edge

    def get_edge(self, edge_id):
        """Retrieves an edge based on its ID."""
        return self._edges.get(edge_id, None)

    def remove_edge(self, edge_id):
        """Removes an edge from the network."""
        if edge_id in self._edges:
            del self._edges[edge_id]

    def update_edge(self, edge_id, attributes=None):
        """Updates the attributes of an edge."""
        if edge_id in self._edges and attributes:
            self._edges[edge_id]["v"].update(attributes)

    def get_visual_properties(self):
        return self._visual_properties

    def set_visual_properties(self, value):
        self._visual_properties = value

    def get_node_bypasses(self):
        return self._node_bypasses

    def add_node_bypass(self, node_id, value):
        """
        Adds a node-specific visual property bypass.

        :param node_id: ID of the node.
        :param value: Visual property bypass value.
        """
        self._node_bypasses[node_id] = value

    def get_edge_bypasses(self):
        return self._edge_bypasses

    def add_edge_bypass(self, edge_id, value):
        """
        Adds an edge-specific visual property bypass.

        :param edge_id: ID of the edge.
        :param value: Visual property bypass value.
        """
        self._edge_bypasses[edge_id] = value

    def get_opaque_aspects(self):
        return self._opaque_aspects

    def set_opaque_aspects(self, value):
        self._opaque_aspects = value

    def add_opaque_aspect(self, aspect):
        """
        Adds an opaque aspect to the list of opaque aspects.

        :param aspect: The opaque aspect to add.
        """
        self._opaque_aspects.append(aspect)

    def get_status(self):
        return self._status

    def set_status(self, value):
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
        aliases = {}
        declarations = self.get_attribute_declarations()[aspect]
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
        default_values = {}
        declarations = self.get_attribute_declarations()[aspect]
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
        if isinstance(cx2_data, str):
            with open(cx2_data, 'r') as cx2_file:
                raw_data = json.load(cx2_file)
        elif isinstance(cx2_data, list):
            raw_data = cx2_data
        else:
            raise ValueError("Invalid input. The input parameter 'cx2_data' should be a file path (str) or a list.")

        for section in raw_data:
            if 'attributeDeclarations' in section:
                self.set_attribute_declarations(section['attributeDeclarations'][0])

            elif 'networkAttributes' in section:
                self.set_network_attributes(section['networkAttributes'][0])

            elif 'nodes' in section:
                for node in section['nodes']:
                    x = node.get("x", None)
                    y = node.get("y", None)
                    z = node.get("z", None)
                    self.add_node(node["id"], node["v"], x, y, z)

            elif 'edges' in section:
                for edge in section['edges']:
                    self.add_edge(edge["id"], edge["s"], edge["t"], edge["v"])

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
                self.set_status(section["status"])
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

    def to_cx2(self):
        """
        Generates the CX2 representation of the current state of the instance.

        This method constructs a list structure representing the current state of the network
        in the CX2 format.

        :return: A list representing the CX2 formatted data of the current network state.
        :rtype: list
        """
        output_data = [{
            "CXVersion": "2.0",
            "hasFragments": False
        }]
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
        output_data.append({"metaData": meta_data})

        output_data.append({"attributeDeclarations": [self.get_attribute_declarations()]})
        output_data.append({"networkAttributes": [self.get_network_attributes()]})

        nodes_list = self._replace_with_alias(list(self.get_nodes().values()), 'nodes')
        edges_list = self._replace_with_alias(list(self.get_edges().values()), 'edges')

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
            output_data.append({"status": self._status})

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

        for key, value in attributes.items():
            actual_key = aliases.get(key, key)
            declared_type = self.get_declared_type(aspect_name, actual_key)
            if value is not None:
                processed_attrs[actual_key] = convert_value(declared_type, value)

        return processed_attrs

    def _replace_with_alias(self, aspect_list, aspect_name):
        """
        Replaces attribute names in a data list with their corresponding aliases, if available.

        :param aspect_list: List of data items (e.g., nodes or edges) with attributes.
        :type aspect_list: list
        :param aspect: Name of the aspect (e.g., 'nodes', 'edges') for which aliases are to be applied.
        :type aspect: str
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
        """
        Constructor
        """
        pass

    def get_cx2_network(self, input_data=None) -> CX2Network:
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
        """
        Constructor
        """
        super(NoStyleCXToCX2NetworkFactory, self).__init__()

    def _translate_network_attributes_to_cx2(self, network_attributes):
        cx2_data = {}
        for item in network_attributes:
            key = item['n']
            value = item['v']
            cx2_data[key] = value
        return cx2_data

    def _generate_attribute_declarations(self, network_attributes, nodes, node_attributes, edges, edge_attributes):
        attribute_declarations = {
            "networkAttributes": {},
            "nodes": {},
            "edges": {}
        }
        for item in network_attributes:
            attribute_declarations['networkAttributes'][item['n']] = {'d': item.get('d', 'string')}

        node_internal_attributes = set()
        for val in nodes.values():
            node_internal_attributes.update(val.keys())
        node_internal_attributes.remove('@id')
        for item in node_internal_attributes:
            if item == 'n':
                attribute_declarations['nodes']['name'] = {'a': 'n', 'd': 'string'}
            elif item == 'r':
                attribute_declarations['nodes']['represents'] = {'a': 'r', 'd': 'string'}

        for attr_list in node_attributes.values():
            for attr in attr_list:
                if (attr['n'] not in attribute_declarations['nodes'].keys() or
                        attribute_declarations['nodes'][attr['n']]['d'] == 'string'):
                    attribute_declarations['nodes'][attr['n']] = {'d': attr.get('d', 'string')}

        edge_internal_attributes = set()
        for val in edges.values():
            edge_internal_attributes.update(val.keys())
        edge_internal_attributes.remove('@id')
        if 'i' in edge_internal_attributes:
            attribute_declarations['edges']['interaction'] = {'a': 'i', 'd': 'string'}

        for attr_list in edge_attributes.values():
            for attr in attr_list:
                if (attr['n'] not in attribute_declarations['edges'].keys() or
                        attribute_declarations['edges'][attr['n']]['d'] == 'string'):
                    attribute_declarations['edges'][attr['n']] = {'d': attr.get('d', 'string')}

        return attribute_declarations

    def _process_node_attributes(self, node, node_attributes):
        attr_vals = {}
        if 'n' in node.keys():
            attr_vals['n'] = node['n']
        if 'r' in node.keys():
            attr_vals['r'] = node['r']
        for attr in node_attributes[node['@id']]:
            value = attr['v']
            attr_vals[attr['n']] = value
        return attr_vals

    def _process_edge_attributes(self, edge, edge_attributes):
        attr_vals = {}
        if 'i' in edge.keys():
            attr_vals['i'] = edge['i']
        for attr in edge_attributes[edge['@id']]:
            value = attr['v']
            attr_vals[attr['n']] = value
        return attr_vals

    def get_cx2network(self, input_data) -> CX2Network:
        """
        Creates :py:class:`~ndex2.cx2.CX2Network` from
        CX data or :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        but does **NOT** convert the style associated with input network

        .. note::

            Style is NOT converted by this call

        :param input_data: Optional input data used to generate network
        :type input_data: list or :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
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
        cx2network_obj.set_attribute_declarations(self._generate_attribute_declarations(
            network.networkAttributes, network.nodes, network.nodeAttributes, network.edges, network.edgeAttributes))
        print(cx2network_obj.get_attribute_declarations())

        cx2network_obj.set_network_attributes(self._translate_network_attributes_to_cx2(network.networkAttributes))

        for node, layout in zip(network.nodes.values(), network.opaqueAspects['cartesianLayout']):
            attr_val = self._process_node_attributes(node, network.nodeAttributes)
            cx2network_obj.add_node(node['@id'], attr_val, layout.get('x', None), layout.get('y', None),
                                    layout.get('z', None))

        for edge in network.edges.values():
            attr_val = self._process_edge_attributes(edge, network.edgeAttributes)
            cx2network_obj.add_edge(edge['@id'], edge['s'], edge['t'], attr_val)

        cx2network_obj.set_status([{'error': '', 'success': True}])

        return cx2network_obj


class RawCX2NetworkFactory(CX2NetworkFactory):

    def __init__(self):
        """
        Constructor
        """
        super(RawCX2NetworkFactory, self).__init__()

    def get_cx2network(self, input_data) -> CX2Network:
        """
        Creates :py:class:`~ndex2.cx2.CX2Network` from raw CX2 data.
        """
        cx2network_obj = CX2Network()
        cx2network_obj.create_from_raw_cx2(input_data)
        return cx2network_obj
