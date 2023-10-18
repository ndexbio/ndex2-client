import json

from . import create_nice_cx_from_raw_cx, create_nice_cx_from_file
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
        return True if value.lower() == 'true' else False
    elif dtype.startswith("list_of_"):
        elem_type = dtype.split("_")[2]
        return [convert_value(elem_type, v) for v in value]
    else:
        return value


class CX2Factory(object):
    """
    Base class for Factory classes that create
    :py:class:`~ndex2.cx2.CX2Network` objects
    """
    def __init__(self):
        """
        Constructor
        """
        pass

    def get_cx2_network(self, input_data=None):
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


class NoStyleCXToCX2Factory(CX2Factory):
    """
    Creates :py:class:`~ndex2.cx2.CX2Network` network from
    CX data or :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
    """
    def __init__(self):
        """
        Constructor
        """
        super().__init__()

    def get_cx2_network(self, input_data=None):
        """
        Creates :py:class:`~ndex2.cx2.CX2Network` from
        CX data or :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        but does **NOT** convert the style associated with input network

        .. note::

            Style is NOT converted by this call

        :param input_data: Optional input data for used to generate
                           network
        :type input_data: list or :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
        :return: Generated network
        :rtype: :py:class:`~ndex2.cx2.CX2Network`
        """
        raise NotImplementedError('TODO Need to implement this')

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
        self.attribute_declarations = None
        self.network_attributes = {}
        self.nodes = {}
        self.edges = {}
        self.visual_properties = []
        self.node_bypasses = {}
        self.edge_bypasses = {}
        self.opaque_aspects = []
        self.status = {}
        self._aliases = {"nodes": {}, "edges": {}}
        self._default_values = {"nodes": {}, "edges": {}}

    def get_attribute_declarations(self):
        return self.attribute_declarations

    def set_attribute_declarations(self, value):
        self.attribute_declarations = value

    def get_network_attributes(self):
        return self.network_attributes

    def set_network_attributes(self, value):
        self.network_attributes = value

    def add_node(self, node_id, attributes=None, x=None, y=None, z=None):
        """Adds a node to the network."""
        node = {
            "id": node_id,
            "v": attributes or {},
            "x": x,
            "y": y,
            "z": z
        }
        self.nodes[node_id] = node

    def get_node(self, node_id):
        """Retrieves a node based on its ID."""
        return self.nodes.get(node_id, None)

    def remove_node(self, node_id):
        """Removes a node and checks for dangling edges."""
        # Remove the node
        if node_id in self.nodes:
            del self.nodes[node_id]

        edges_to_remove = [edge_id for edge_id, edge in self.edges.items() if
                           edge["s"] == node_id or edge["t"] == node_id]
        for edge_id in edges_to_remove:
            self.remove_edge(edge_id)

    def update_node(self, node_id, attributes=None, x=None, y=None, z=None):
        """Updates the attributes of a node."""
        if node_id in self.nodes:
            if attributes:
                self.nodes[node_id]["v"].update(attributes)
            if x is not None:
                self.nodes[node_id]["x"] = x
            if y is not None:
                self.nodes[node_id]["y"] = y
            if z is not None:
                self.nodes[node_id]["z"] = z

    def add_edge(self, edge_id, source, target, attributes=None):
        """Adds an edge to the network."""
        edge = {
            "id": edge_id,
            "s": source,
            "t": target,
            "v": attributes or {}
        }
        self.edges[edge_id] = edge

    def get_edge(self, edge_id):
        """Retrieves an edge based on its ID."""
        return self.edges.get(edge_id, None)

    def remove_edge(self, edge_id):
        """Removes an edge from the network."""
        if edge_id in self.edges:
            del self.edges[edge_id]

    def update_edge(self, edge_id, attributes=None):
        """Updates the attributes of an edge."""
        if edge_id in self.edges and attributes:
            self.edges[edge_id]["v"].update(attributes)

    def get_visual_properties(self):
        return self.visual_properties

    def set_visual_properties(self, value):
        self.visual_properties = value

    def get_node_bypasses(self):
        return self.node_bypasses

    def set_node_bypasses(self, value):
        self.node_bypasses = value

    def add_node_bypass(self, node_id, value):
        """
        Adds a node-specific visual property bypass.

        :param node_id: ID of the node.
        :param value: Visual property bypass value.
        """
        self.node_bypasses[node_id] = value

    def get_edge_bypasses(self):
        return self.edge_bypasses

    def set_edge_bypasses(self, value):
        self.edge_bypasses = value

    def add_edge_bypass(self, edge_id, value):
        """
        Adds an edge-specific visual property bypass.

        :param edge_id: ID of the edge.
        :param value: Visual property bypass value.
        """
        self.edge_bypasses[edge_id] = value

    def get_opaque_aspects(self):
        return self.opaque_aspects

    def set_opaque_aspects(self, value):
        self.opaque_aspects = value

    def get_status(self):
        return self.status

    def set_status(self, value):
        self.status = value

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
                for aspect, declarations in self.attribute_declarations.items():
                    for key, details in declarations.items():
                        alias = details.get("a", None)
                        if alias and aspect in ["nodes", "edges"]:
                            self._aliases[aspect][alias] = key
                        default_value = details.get("v", None)
                        if default_value and aspect in ["nodes", "edges"]:
                            self._default_values[aspect][key] = default_value

            elif 'networkAttributes' in section:
                network_attrs = {}
                for attr in section['networkAttributes']:
                    for key, value in attr.items():
                        declared_type = (self.get_attribute_declarations()['networkAttributes'].get(key, {})
                                         .get('d', 'string'))
                        network_attrs[key] = convert_value(declared_type, value)
                self.set_network_attributes(network_attrs)

            elif 'nodes' in section:
                for node in section['nodes']:
                    attributes = self._process_attributes('nodes', node["v"])
                    x = node.get("x", None)
                    y = node.get("y", None)
                    z = node.get("z", None)
                    self.add_node(node["id"], attributes, x, y, z)

            elif 'edges' in section:
                for edge in section['edges']:
                    attributes = self._process_attributes('edges', edge["v"])
                    self.add_edge(edge["id"], edge["s"], edge["t"], attributes)

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
                self.opaque_aspects.append(section)

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
        meta_data = [
            {"elementCount": 1, "name": "attributeDeclarations"},
            {"elementCount": 1, "name": "networkAttributes"},
            {"elementCount": len(self.nodes), "name": "nodes"},
            {"elementCount": len(self.edges), "name": "edges"},
            {"elementCount": 1, "name": "visualProperties"},
            {"elementCount": len(self.node_bypasses), "name": "nodeBypasses"},
            {"elementCount": len(self.edge_bypasses), "name": "edgeBypasses"}
        ]
        for opaque_aspect in self.opaque_aspects:
            aspect_name = list(opaque_aspect.keys())[0]
            aspect_count = len(opaque_aspect[aspect_name])
            meta_data.append({"elementCount": aspect_count, "name": aspect_name})
        output_data.append({"metaData": meta_data})

        output_data.append({"attributeDeclarations": [self.attribute_declarations]})
        output_data.append({"networkAttributes": [self.network_attributes]})

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

        return output_data

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
        for key, default_value in self._default_values[aspect_name].items():
            actual_key = self._aliases[aspect_name].get(key, key)
            processed_attrs[actual_key] = default_value

        for key, value in attributes.items():
            actual_key = self._aliases[aspect_name].get(key, key)
            declared_type = self.attribute_declarations[aspect_name].get(actual_key, {}).get('d', 'string')
            if value is not None:
                processed_attrs[actual_key] = convert_value(declared_type, value)

        return processed_attrs

    def _replace_with_alias(self, data_list, aspect):
        """
        Replaces attribute names in a data list with their corresponding aliases, if available.

        :param data_list: List of data items (e.g., nodes or edges) with attributes.
        :type data_list: list
        :param aspect: Name of the aspect (e.g., 'nodes', 'edges') for which aliases are to be applied.
        :type aspect: str
        """
        new_data = []

        reverse_aliases = {v: k for k, v in self._aliases[aspect].items()}

        for item in data_list:
            new_item = item.copy()
            if 'v' in new_item:
                for attr in list(new_item['v'].keys()):
                    if attr in reverse_aliases:
                        new_item['v'][reverse_aliases[attr]] = new_item['v'].pop(attr)
            new_data.append(new_item)

        return new_data


class CX2NetworkFactory(object):
    """
    Abstract factory class for CX2Network creation.
    """

    def __init__(self):
        pass

    def get_cx2network(self, input_data) -> CX2Network:
        """
        Abstract method that should be implemented by derived classes to provide a mechanism
        for creating a CX2Network instance.

        :param input_data: Input data to create CX2Network.
        :type input_data:
        :return: An instance of CX2Network.
        """
        pass


class NoStyleCXToCX2NetworkFactory(CX2NetworkFactory):

    def __init__(self):
        super(NoStyleCXToCX2NetworkFactory, self).__init__()

    def _translate_network_attributes_to_cx2(self, network_attributes):
        cx2_data = {}
        for item in network_attributes:
            key = item['n']
            value = item['v']
            cx2_data[key] = value
        return [cx2_data]

    def _translate_nodes_to_cx2(self, nodes, cartesian_layout, node_attributes):
        cx2_nodes = {}
        for node, layout in zip(nodes.values(), cartesian_layout):
            cx2_node = {
                "id": node['@id'],
                "x": layout['x'],
                "y": layout['y'],
                "v": {
                    "n": node['n'],
                    "r": node['r']
                }
            }
            for attr in node_attributes[node['@id']]:
                value = attr['v']
                if 'd' in attr:
                    data_type = attr.get('d')
                    value = convert_value(data_type, value)
                cx2_node['v'][attr['n']] = value
            cx2_nodes[cx2_node['id']] = cx2_node
        return cx2_nodes

    def _translate_edges_to_cx2(self, edges, edge_attributes):
        cx2_edges = {}
        for edge in edges.values():
            cx2_edge = {
                "id": edge['@id'],
                "s": edge['s'],
                "t": edge['t'],
                "v": {
                    "i": edge['i']
                }
            }
            for attr in edge_attributes[edge['@id']]:
                value = attr['v']
                if 'd' in attr:
                    data_type = attr.get('d')
                    value = convert_value(data_type, value)
                cx2_edge['v'][attr['n']] = value
            cx2_edges[cx2_edge['id']] = cx2_edge
        return cx2_edges

    def get_cx2network(self, input_data) -> CX2Network:
        if isinstance(input_data, NiceCXNetwork):
            network = input_data
        elif isinstance(input_data, str):
            network = create_nice_cx_from_file(input_data)
        else:
            network = create_nice_cx_from_raw_cx(input_data)

        cx2network_obj = CX2Network()
        cx2network_obj.network_attributes = self._translate_network_attributes_to_cx2(network.networkAttributes)
        cx2network_obj.nodes = self._translate_nodes_to_cx2(network.nodes, network.opaqueAspects['cartesianLayout'],
                                                            network.nodeAttributes)
        cx2network_obj.edges = self._translate_edges_to_cx2(network.edges, network.edgeAttributes)

        cx2network_obj.write_as_raw_cx2("/Users/jlenkiewicz/Documents/repos/ndex2-client/tests/data/out.cx2")
        return cx2network_obj


class RawCX2NetworkFactory(CX2NetworkFactory):
    def get_cx2network(self, input_data) -> CX2Network:
        pass

#
# cl = NoStyleCXToCX2NetworkFactory()
# cl.get_cx2network("/Users/jlenkiewicz/Documents/repos/ndex2-client/tests/data/glypican2.cx")
