__author__ = 'aarongary'

import sys
import pandas as pd
import networkx as nx
import io
import decimal
import numpy as np
import json
import ijson
import requests
import base64
import logging

from ndex2.client import Ndex2
from ndex2.exceptions import NDExError
from ndex2.exceptions import NDExNotFoundError
from ndex2.exceptions import NDExUnauthorizedError
from ndex2.exceptions import NDExInvalidParameterError

from ndex2 import constants
from ndex2.util import PandasDataConverter

if sys.version_info.major == 3:
    from urllib.request import urlopen, Request, HTTPError, URLError
else:
    from urllib2 import urlopen, Request, HTTPError, URLError


class NiceCXNetwork:

    VISUAL_PROPERTIES = 'visualProperties'
    CY_VISUAL_PROPERTIES = 'cyVisualProperties'
    PROPERTIES_OF = 'properties_of'
    PROPS_OF_NODES = 'nodes'
    PROPS_OF_EDGES = 'edges'
    META_DATA = 'metaData'

    def __init__(self, **attr):

        self.metadata = {}
        self.nodes = {}
        self.node_int_id_generator = 0
        self.edge_int_id_generator = 0
        self.node_id_lookup = []
        self.edges = {}
        self.citations = {}
        self.nodeCitations = {}
        self.edgeCitations = {}
        self.edgeSupports = {}
        self.nodeSupports = {}
        self.supports = {}
        self.nodeAttributes = {}
        self.edgeAttributes = {}
        self.edgeAttributeHeader = set([])
        self.nodeAttributeHeader = set([])
        self.networkAttributes = []
        self.nodeAssociatedAspects = {}
        self.edgeAssociatedAspects = {}
        self.opaqueAspects = {}
        self.provenance = []
        self.missingNodes = {}
        self.s = None
        self.node_name_to_id_map_cache = {}
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _is_python_three_or_greater():
        """
        Using ``sys.version_info.major`` determines version of
        Python
        :return: True if Python 3 or greater is found, otherwise False
        :rtype: bool
        """
        if sys.version_info.major >= 3:
            return True
        return False

    def __create_edge(self, edge_id=None, edge_source=None,
                      edge_target=None, edge_interaction=None):
        """
        Create a new edge in the network by specifying source-interaction-target

        :param id:
        :type id:
        :param edge_source: The source node this edge, either its id or the node object itself.
        :type edge_source: int
        :param edge_target: The target node this edge, either its id or the node object itself.
        :type edge_target: int
        :param edge_interaction: The interaction that describes the relationship between the source and target nodes
        :type edge_interaction: string
        :param cx_fragment: CX Fragment
        :type cx_fragment: json
        :return: Edge ID
        :rtype: int
        """

        if isinstance(edge_source, dict):
            src_id = edge_source.get(constants.EDGE_ID)
        else:
            src_id = edge_source

        if isinstance(edge_target, dict):
            target_id = edge_target.get(constants.EDGE_ID)
        else:
            target_id = edge_target

        self.edges[edge_id] = {constants.EDGE_ID: edge_id,
                               constants.EDGE_SOURCE: src_id,
                               constants.EDGE_TARGET: target_id}

        if edge_interaction is not None:
            self.edges[edge_id][constants.EDGE_INTERACTION] = edge_interaction

        return edge_id

    def create_edge(self, edge_source=None,
                    edge_target=None, edge_interaction=None):
        """
        Create a new edge in the network by specifying source-interaction-target

        .. warning::

            Version `3.3.1` and prior of this library had a `bug <https://github.com/ndexbio/ndex2-client/issues/60>`__
            that caused this method to behave incorrectly. Please upgrade to
            `3.3.2 <https://pypi.org/project/ndex2/3.3.2/>`__ or greater.

        Example:

            ``my_edge = create_edge(edge_source=my_node, edge_target=my_node2, edge_interaction='up-regulates')``

        :param edge_source: The source node of this edge, either its id or the node object itself.
        :type edge_source: int, dict (with :py:const:`~ndex2.constants.EDGE_ID` property)
        :param edge_target: The target node of this edge, either its id or the node object itself.
        :type edge_target: int, dict (with :py:const:`~ndex2.constants.EDGE_ID` property)
        :param edge_interaction: The interaction that describes the relationship between the source and target nodes
        :type edge_interaction: string
        :return: Edge ID
        :rtype: int
        """
        edge_id = self.edge_int_id_generator

        self.__create_edge(edge_id=edge_id, edge_source=edge_source,
                           edge_target=edge_target,
                           edge_interaction=edge_interaction)
        self.edge_int_id_generator += 1

        return edge_id

    # ==================
    # NODE OPERATIONS
    # ==================
    def __create_node(self, node_id=None, node_name=None, node_represents=None):
        if node_id is None:
            node_id = self.get_next_node_id()

        if node_represents is not None:
            self.nodes[node_id] = {constants.NODE_ID: node_id,
                                   constants.NODE_NAME: node_name,
                                   constants.NODE_REPRESENTS: node_represents}
        else:
            self.nodes[node_id] = {constants.NODE_ID: node_id,
                                   constants.NODE_NAME: node_name,
                                   constants.NODE_REPRESENTS: node_name}

        return id

    def create_node(self, node_name=None, node_represents=None):
        """
        Creates a new node with the corresponding name
        and represents (external id)

        .. warning::

            Version `3.3.1` and prior of this library had a
            `bug <https://github.com/ndexbio/ndex2-client/issues/60>`__
            that caused this method to behave incorrectly.
            Please upgrade to
            `3.3.2 <https://pypi.org/project/ndex2/3.3.2/>`__ or greater.

        Example:

            ``my_node = create_node(node_name='MAPK1, node_represents='1114208')``

        :param node_name: Name of the node
        :type node_name: str
        :param node_represents: Representation of the node (alternate identifier)
        :type node_represents: str
        :return: Node ID
        :rtype: int
        """

        node_id = self.node_int_id_generator
        self.__create_node(node_id=node_id, node_name=node_name,
                           node_represents=node_represents)
        self.node_int_id_generator += 1

        return node_id

    def add_network_attribute(self, name=None, values=None,
                              type=None, subnetwork=None):
        """
        Add an attribute to the network

        :param name: Name of the attribute
        :type name: str
        :param values:  The value(s) of the attribute
        :type values: One of the allowable CX types.  See `Supported data types`_
        :param type: They type of data supplied in values.
                     Default is string.  See `Supported data types`_
        :type type: str
        :return: None
        :rtype: None
        """
        found_attr = False
        for n_a in self.networkAttributes:
            if n_a.get('n') == name:
                n_a['v'] = values

                if 'd' in n_a:
                    del n_a['d']

                if type is not None:
                    n_a['d'] = type

                found_attr = True

                break

        if not found_attr:
            if type is not None:
                network_attribute = {'n': name, 'v': values, 'd': type}
            else:
                network_attribute = {'n': name, 'v': values}

            self.networkAttributes.append(network_attribute)

    def add_citation(self, id, title=None, contributor=None,
                     identifier=None, type=None,
                     description=None, attributes=None):
        add_this_citation = {'@id': id}

        if contributor is not None:
            add_this_citation['dc:contributor'] = contributor

        if identifier is not None:
            add_this_citation['dc:identifier'] = identifier

        if type is not None:
            add_this_citation['dc:type'] = type

        if title is not None:
            add_this_citation['dc:title'] = title

        if description is not None:
            add_this_citation['dc:description'] = description

        if attributes is not None:
            add_this_citation[attributes] = attributes

        self.citations[id] = add_this_citation

        return add_this_citation

    def add_edge_citations(self, edge_id, citation):
        if isinstance(citation, dict):
            edge_citation_element = {'po': [edge_id],
                                     'citations': [citation.get('@id')]}
        else:
            edge_citation_element = {'po': [edge_id],
                                     'citations': [citation]}

        self.build_many_to_many_relation('edgeCitations',
                                         edge_citation_element, 'citations')

    def add_support(self, id=None, text=None, citation_id=None,
                    attributes=None, props=None):
        add_this_supports = {'@id': id}

        if text is not None:
            add_this_supports['text'] = text

        if citation_id is not None:
            add_this_supports['citation'] = citation_id

        if attributes is not None and len(attributes) > 0:
            add_this_supports['attributes'] = attributes

        if props is not None and len(props) > 0:
            add_this_supports['properties'] = props

        self.supports[id] = add_this_supports

        return add_this_supports

    def add_edge_supports(self, edge_id, support):
        if isinstance(support, dict):
            edge_support_element = {'po': [edge_id],
                                    'supports': [support.get('@id')]}
        else:
            edge_support_element = {'po': [edge_id],
                                    'supports': [support]}

        self.build_many_to_many_relation('edgeSupports',
                                         edge_support_element, 'supports')

    def build_many_to_many_relation(self, aspect_name, element,
                                    relation_name):
        if aspect_name == 'nodeCitations':
            aspect = self.nodeCitations
        elif aspect_name == 'edgeCitations':
            aspect = self.edgeCitations
        elif aspect_name == 'edgeSupports':
            aspect = self.edgeSupports
        else:
            raise Exception('Only nodeCitations, edgeCitations and '
                            'edgeSupports are supported. ' +
                            aspect_name + ' was supplied')

        for po in element.get('po'):
            po_id = aspect.get(po)
            if po_id is None:
                aspect[po] = element.get(relation_name)
            else:
                aspect[po] += element.get(relation_name)
    # TODO
    # make opaque aspect into a one shot method to set the whole aspect.
    # i.e. not one element at a time

    def add_opaque_aspect(self, aspect_name, aspect):
        if isinstance(aspect, list):
            self.opaqueAspects[aspect_name] = aspect
        elif isinstance(aspect, dict):
            if 'error' in aspect:
                pass
            else:
                self.opaqueAspects[aspect_name] = [aspect]
        else:
            raise Exception('Provided input was not of type list.')

    def add_opaque_aspect_element(self, opaque_element):
        raise Exception('add_opaque_aspect_element() is deprecated.  '
                        'Please use add_opaque_aspect()')

    def set_name(self, network_name):
        """
        Set the network name

        Example:

            ``set_name('P38 Signaling')``

        :param network_name: Network name
        :type network_name: string
        :return: None
        :rtype: None

        """
        self.add_network_attribute(name='name',
                                   values=network_name, type='string')

    def get_name(self):
        """
        Get the network name

        :return: Network name
        :rtype: string
        """
        for net_a in self.networkAttributes:
            if net_a.get('n') == 'name':
                return net_a.get('v')

        return None

    def add_name_space(self, prefix, uri):
        found_context = False
        for n_a in self.networkAttributes:
            if n_a.get('n') == '@context':
                found_context = True
                add_to_this_context = json.loads(n_a['v'])
                add_to_this_context[prefix] = uri
                n_a['v'] = json.dumps(add_to_this_context)
                break

        if not found_context:
            self.add_network_attribute(name='@context',
                                       values=json.dumps({prefix: uri}),
                                       type='string')

    def set_namespaces(self, ns):
        self.set_context(ns)

    def get_namespaces(self,):
        return self.get_context()

    def get_edges(self):
        """
        Returns an iterator over edge ids as keys and edge
        objects as values.

        Example:

            ``for edge_id, edge_obj in nice_cx.get_edges():``

            ``print(edge_obj.get('i')) # print interaction``

            ``print(edge_obj.get('s')) # print source node id``

        :return: Edge iterator
        :rtype: iterator
        """
        if NiceCXNetwork._is_python_three_or_greater():
            return self.edges.items()
        return self.edges.iteritems()

    def get_edge(self, edge):
        return self.edges.get(edge)

    # ==============================
    #  NETWORK PROPERTY OPERATIONS
    # ==============================
    def get_network_attribute(self, attribute_name):
        """
        Get the value of a network attribute

        :param attribute_name: Attribute name
        :type attribute_name: string
        :return: Network attribute object
        :rtype: dict
        """
        for n_a in self.networkAttributes:
            if n_a.get('n') == attribute_name:
                return n_a

        return None

    def get_network_attribute_names(self):
        """
        Creates a a generator that gets network attribute names.

        :return: attribute name via a generator
        :rtype: string
        """
        for n_a in self.networkAttributes:
            if constants.NET_ATTR_NAME not in n_a:
                continue
            yield n_a.get(constants.NET_ATTR_NAME)

    def get_next_node_id(self):
        return_id = self.node_int_id_generator
        self.node_int_id_generator += 1
        return return_id

    def add_node_attribute(self, property_of=None, name=None, values=None,
                           type=None, subnetwork=None,
                           overwrite=False):
        if property_of is None:
            raise NDExError('Node attribute requires property_of')

        if isinstance(property_of, dict):
            node_id = property_of.get(constants.NODE_ID)
            if node_id is None:
                raise NDExError('No id found in Node')
        else:
            node_id = property_of

        if name is None or values is None:
            raise NDExError('Node attribute requires the name and values property')

        if self.nodeAttributes.get(node_id) is None:
            self.nodeAttributes[node_id] = []

        if overwrite is True:
            for index, val in enumerate(self.nodeAttributes[node_id]):
                if val[constants.NODE_ATTR_NAME] == name:
                    del self.nodeAttributes[node_id][index]

        n_attrib = {constants.NODE_ATTR_PROPERTYOF: node_id,
                    constants.NODE_ATTR_NAME: name,
                    constants.NODE_ATTR_VALUE: values}
        if type is None:
            attr_type = None
            if isinstance(values, float):
                attr_type = 'double'
            elif isinstance(values, int):
                attr_type = 'integer'
            elif isinstance(values, list):
                attr_type = 'list_of_string'

            if attr_type:
                n_attrib[constants.NODE_ATTR_DATATYPE] = attr_type
        else:
            n_attrib[constants.NODE_ATTR_DATATYPE] = type

        self.nodeAttributes[node_id].append(n_attrib)

    def add_edge_attribute(self, property_of, name, values, type=None,
                           subnetwork=None):
        if isinstance(property_of, dict):
            property_of = property_of.get('@id')

        if self.edgeAttributes.get(property_of) is None:
            self.edgeAttributes[property_of] = []

        if type is None:
            self.edgeAttributes[property_of].append({'po': property_of,
                                                     'n': name, 'v': values})
        else:
            self.edgeAttributes[property_of].append({'po': property_of,
                                                     'n': name,
                                                     'v': values, 'd': type})

    def get_nodes(self):
        """
        Returns an iterator over node ids as keys and node objects as values.

        Example:

            ``for id, node in nice_cx.get_nodes():``

            ``node_name = node.get('n')``

            ``node_represents = node.get('r')``



        :return: iterator over nodes
        :rtype: iterator
        """
        if NiceCXNetwork._is_python_three_or_greater():
            return self.nodes.items()
        return self.nodes.iteritems()

    def get_node(self, node_id):
        return self.nodes.get(node_id)

    def _generate_node_name_to_id_map(self):
        self.node_name_to_id_map_cache = {node.get('n'): node_id for node_id, node in self.get_nodes()}

    def get_node_by_name(self, node_name):
        if(len(self.node_name_to_id_map_cache) < 1):
            self._generate_node_name_to_id_map()

        node_id_lookup = self.node_name_to_id_map_cache.get(node_name)
        if node_id_lookup is not None:
            return self.nodes.get(node_id_lookup)
        else:
            return None

    # TODO - Check edges for orphans.  Check node attributes for orphans
    #def remove_node(self, node_id):
    #    raise Warning()
    #    return self.nodes.pop(node_id, None)

    #=============================
    # NODE ATTRIBUTES OPERATIONS
    #=============================
    def set_node_attribute(self, node, attribute_name, values, type=None,
                           overwrite=False):
        """
        Set an attribute of a node, where the node may be specified by its id or passed in as a node dict.

        Example:

            ``set_node_attribute(my_node, 'Pathway', 'Signal Transduction / Growth Regulation')``

            or

            ``set_node_attribute(my_node, 'Mutation Frequency', 0.007, type='double')``

        :param node: Node to add the attribute to
        :type node: int or node dict with @id attribute
        :param attribute_name: attribute name
        :type attribute_name: string
        :param values: A value or list of values of the attribute
        :type values: list, string, int or double
        :param type: The datatype of the attribute values, defaults is string.  See `Supported data types`_
        :type type: str
        :param overwrite: If True node attribute matching 'attribute_name' is removed first otherwise
                          code blindly adds attribute
        :type overwrite: bool True means to overwrite node attribute named attribute_name
        :return: None
        :rtype: None
        """

        self.add_node_attribute(property_of=node, name=attribute_name,
                                values=values, type=type,
                                overwrite=overwrite)

    def get_node_attribute(self, node, attribute_name):
        """
        Get the node attribute of a node, where the node may be specified by its id or passed in as an object.

        Example:

             ``get_node_attribute(my_node, 'Pathway')``
             ``# returns: {'@id': 0, 'n': 'diffusion-heat', 'v': 0.832, 'd': 'double'}``


        :param node: node object or node id
        :type node: int or node dict with @id attribute
        :param attribute_name: attribute name
        :type attribute_name:
        :return: the node attibute object or None if the attribute doesn't exist
        :rtype: dict
        """
        node_attrs = self.get_node_attributes(node)

        if node_attrs:
            for n_a in node_attrs:
                if n_a.get('n') == attribute_name:
                    return n_a

        return None

    def get_node_attribute_value(self, node, attribute_name):
        """
        Get the value(s) of an attribute of a node, where the node may be specified by its id or passed in as an object.

        Example:

             ``get_node_attribute_value(my_node, 'Pathway')``
             ``# returns: 'Signal Transduction / Growth Regulation'``


        :param node: node object or node id
        :type node: int or node dict with @id attribute
        :param attribute_name: attribute name
        :type attribute_name:
        :return: the value of the attibute or None if the attribute doesn't exist
        :rtype: string
        """
        node_attrs = self.get_node_attributes(node)

        if node_attrs:
            for n_a in node_attrs:
                if n_a.get('n') == attribute_name:
                    return n_a.get('v')

        return None

    def get_node_attributes(self, node):
        """
        Get the attribute objects of a node, where the node may be specified by its id or passed in as an object.

        Example:

             ``get_node_attributes(my_node)``
             ``# returns: [{'po': 0, 'n': 'Pathway', 'v': 'Signal Transduction / Growth Regulation'}]``

        :param node: node object or node id
        :type node: int or node dict with @id attribute
        :return: node attributes
        :rtype: list
        """
        if isinstance(node, dict):
            return self.nodeAttributes.get(node.get('@id'))
        else:
            return self.nodeAttributes.get(node)

    def set_network_attribute(self, name, values=None, type=None):
        """
        Set an attribute of the network

        .. code-block:: python

            from ndex2.nice_cx_network import NiceCXNetwork

            net = NiceCXNetwork()
            net.set_network_attribute(name='networkType', values='Genetic interactions')

        :param name: Attribute name
        :type name: str
        :param values: The values of the attribute
        :type values: list, str, float, or int
        :param type: The datatype of the attribute values.  See `Supported data types`_
        :type type: str
        :return: None
        :rtype: none
        """
        return self.add_network_attribute(name, values=values,
                                          type=type)

    def set_edge_attribute(self, edge, attribute_name, values, type=None):
        """
        Set the value(s) of attribute of an edge, where the edge may be
        specified  by its id or passed in an object.

        Example:

            ``set_edge_attribute(0, 'weight', 0.5, type='double')``

            or

            ``set_edge_attribute(my_edge, 'Disease', 'Atherosclerosis')``


        :param edge: Edge to add the attribute to
        :type edge: int or edge dict with @id attribute
        :param attribute_name: Attribute name
        :type attribute_name: str
        :param values: A value or list of values of the attribute
        :type values: list
        :param type: The datatype of the attribute values, defaults to the
                     python datatype of the values.
                     See `Supported data types`_
        :type type: str
        :return: None
        :rtype: None
        """

        self.add_edge_attribute(property_of=edge, name=attribute_name,
                                values=values, type=type)
        #TODO add support for subnetworks

    def get_edge_attributes(self, edge):
        """
        Get the attribute objects of an edge, where the edge may be specified by its id or passed in as an object.

        Example:

             ``get_edge_attributes(my_edge)``

             ``# returns: [{'@id': 0, 'n': 'weight', 'v': 0.849, 'd': 'double'}, {'@id': 0, 'n': 'Type', 'v': 'E1'}]``

        :param edge: Edge object or edge id
        :type edge: int or edge dict with @id attribute
        :return: Edge attribute objects
        :rtype: list of edge dict
        """
        if isinstance(edge, dict):
            return self.edgeAttributes.get(edge.get('@id'))

        return self.edgeAttributes.get(edge)

    def get_edge_attribute(self, edge, attribute_name):
        """
        Get the edge attributes of an edge, where the edge may be specified by its id or passed in as an object.


        Example:

             ``get_edge_attribute(my_edge, 'weight')``

             ``# returns: {'@id': 0, 'n': 'weight', 'v': 0.849, 'd': 'double'}``


        :param edge: Edge object or edge id
        :type edge: int or edge dict with @id attribute
        :param attribute_name: Attribute name
        :type attribute_name:
        :return: Edge attribute object
        :rtype: list, string, int or double
        """

        edge_attrs = self.get_edge_attributes(edge)
        if edge_attrs:
            edge_attr_found = False
            for e_a in edge_attrs:
                if e_a.get('n') == attribute_name:
                    return e_a

        return None, None

    def get_edge_attribute_value(self, edge, attribute_name):
        """
        Get the value(s) of an attribute of an edge, where the edge may be specified by its id or passed in as an object.

        Example:

             ``get_edge_attribute_value(my_edge, 'weight')``

             ``# returns: 0.849``

        :param edge: Edge object or edge id
        :type edge: int or edge dict with @id attribute
        :param attribute_name: Attribute name
        :type attribute_name:
        :return: Edge attribute value(s)
        :rtype: list, string, int or double
        """

        edge_attrs = self.get_edge_attributes(edge)
        if edge_attrs:
            edge_attr_found = False
            for e_a in edge_attrs:
                if e_a.get('n') == attribute_name:
                    return e_a.get('v')

        return None, None

    def get_node_attributesx(self):
        return self.nodeAttributes.items()

    def remove_node(self, node):
        return self.nodes.pop(node, None)

    def remove_node_attribute(self, node, attribute_name):
        node_attrs = self.get_node_attributes(node)

        if node_attrs:
            for n_a in node_attrs:
                if n_a.get('n') == attribute_name:
                    node_attrs.remove(n_a)
                    break

    def remove_edge(self, edge):
        return self.edges.pop(edge, None)

    def remove_edge_attribute(self, edge, attribute_name):
        edge_attrs = self.get_edge_attributes(edge)

        if edge_attrs:
            for e_a in edge_attrs:
                if e_a.get('n') == attribute_name:
                    edge_attrs.remove(e_a)
                    break

    #==================
    # OTHER OPERATIONS
    #==================

    def get_context(self):
        """
        Get the @context information of the network.  This information
        maps namespace prefixes to their defining URIs

        Example:

            ``{'pmid': 'https://www.ncbi.nlm.nih.gov/pubmed/'}``

        :return: context object
        :rtype: dict
        """
        for n_a in self.networkAttributes:
            if n_a.get('n') == '@context':
                return json.loads(n_a['v'])

        return None

    def set_context(self, context):
        """
        Set the @context information of the network.  This information
        maps namespace prefixes to their defining URIs

        Example:

        .. code-block:: python

            from ndex2.nice_cx_network import NiceCXNetwork

            net = NiceCXNetwork()
            net.set_context({'pmid': 'https://www.ncbi.nlm.nih.gov/pubmed/'})


        :param context: dict where key is name and value is URI or list of those
                        dict objects
        :type context: dict or list
        :raises NDExError: If **context** is not of type :py:class:`list` or :py:class:`dict`
        :return: None
        :rtype: none
        """
        if isinstance(context, list):
            add_this_context = {}
            for c in context:
                for k, v in c.items():
                    add_this_context[k] = v
            self.add_network_attribute(name='@context',
                                       values=json.dumps(add_this_context))
        elif isinstance(context, dict):
            self.add_network_attribute(name='@context',
                                       values=json.dumps(context))
        else:
            raise NDExError('Context provided is not of type list or dict')

    def get_metadata(self):
        """
        Get the network metadata

        :return: Network metadata
        :rtype: Iterator of metadata dict
        """
        if NiceCXNetwork._is_python_three_or_greater():
            return self.metadata.items()
        return self.metadata.iteritems()

    def set_metadata(self, metadata_obj):
        """
        Set the network metadata

        .. versionchanged:: 3.5.0
           Now raises more specific :py:class:`~ndex2.exceptions.NDExError`
           if **metadata_obj** is not of type :py:`dict`

        :param metadata_obj: Dict of metadata objects
        :type metadata_obj: dict
        :raises NDExError: If **metadata_obj** is not of type `dict`
        :return: None
        :rtype: none
        """
        if isinstance(metadata_obj, dict):
            self.metadata = metadata_obj
        else:
            raise NDExError('Set metadata input was not of type <dict>')

    def get_opaque_aspect_table(self):
        return self.opaqueAspects

    def get_opaque_aspect(self, aspect_name):
        """
        Get the elements of the aspect specified by aspect_name

        :param aspect_name: the name of the aspect to retrieve.
        :type aspect_name: string
        :return: Opaque aspect
        :rtype: list of aspect elements
        """
        return self.opaqueAspects.get(aspect_name)

    def set_opaque_aspect(self, aspect_name, aspect_elements):
        """
        Set the aspect specified by aspect_name to the list of
        aspect elements. If aspect_elements is `None`, the
        aspect is removed.

        .. versionchanged:: 3.5.0
           Fixed bug where passing `None` in `aspect_elements` did
           **NOT** remove aspect. Code also now raises
           :py:class:`~ndex2.exceptions.NDExError` if input values are
           invalid

        .. code-block:: python

            from ndex2.nice_cx_network import NiceCXNetwork
            net = NiceCXNetwork()

            # to set an opaque aspect
            net.set_opaque_aspect('foo', [{'data': 'val'}])

            # to remove an opaque aspect named 'foo'
            net.set_opaque_aspect('foo', None)

        :param aspect_name: Name of the aspect
        :type aspect_name: str
        :param aspect_elements: Aspect element
        :type aspect_elements: list of dict or dict
        :raises NDExError: If `aspect_name` is `None`, or if
                           `aspect_elements` is not `None`,
                           :py:class:`dict`, or :py:class:`list`
        :return: None
        :rtype: none
        """
        if aspect_name is None:
            raise NDExError('aspect_name is None')
        if aspect_elements is None:
            self.remove_opaque_aspect(aspect_name)
            return
        if isinstance(aspect_elements, list):
            self.opaqueAspects[aspect_name] = aspect_elements
            return
        if isinstance(aspect_elements, dict):
            self.opaqueAspects[aspect_name] = [aspect_elements]
            return

        raise NDExError('Provided aspect for ' +
                        aspect_name +
                        ' is not of type <list or dict>')

    def remove_opaque_aspect(self, aspect_name):
        """
        Removes the given aspect from the opaque aspects
        collection

        :param aspect_name: The opaque aspect name
        :type aspect_name: str
        :return: None
        :rtype: None
        """
        self.opaqueAspects.pop(aspect_name, None)

    def get_opaque_aspect_names(self):
        """
        Get the names of all opaque aspects

        :return: List of opaque aspect names
        :rtype: list of strings
        """
        return self.opaqueAspects.keys()

    # TODO - determine if this is useful
    def get_edge_attribute_element(self, edge, attr_name):
        attrs = self.edgeAttributes.get(edge.get_id())
        for attr in attrs:
            if attr.get_name() == attr_name:
                return attr

        return None

    def get_edge_attributes_by_id(self, id):
        return self.edgeAttributes.get(id)

    def get_node_associated_aspects(self):
        return self.nodeAssociatedAspects

    def get_edge_associated_aspects(self):
        return self.edgeAssociatedAspects

    def get_node_associated_aspect(self, aspectName):
        return self.nodeAssociatedAspects.get(aspectName)

    def get_edge_associated_aspect(self, aspectName):
        return self.edgeAssociatedAspects.get(aspectName)

    def get_provenance(self):
        return self.provenance

    def get_missing_nodes(self):
        return self.missingNodes

    def get_edge_citations(self):
        return self.edgeCitations

    def get_node_citations(self):
        return self.nodeCitations

    def _get_visual_properties_aspect(self):
        """
        Gets the visual Properties aspect (an opaque aspect) by
        first looking for :py:const:`~.NiceCXNetwork.CY_VISUAL_PROPERTIES` aspect
        and if not found then :py:const:`~.NiceCXNetwork.VISUAL_PROPERTIES`
        aspect.

        :return: visual properties aspect as dict or None if not found
        """
        opaque_aspect_names = self.get_opaque_aspect_names()
        if NiceCXNetwork.CY_VISUAL_PROPERTIES in opaque_aspect_names:
            return self.get_opaque_aspect(NiceCXNetwork.CY_VISUAL_PROPERTIES)
        if NiceCXNetwork.VISUAL_PROPERTIES in opaque_aspect_names:
            return self.get_opaque_aspect(NiceCXNetwork.VISUAL_PROPERTIES)

    def _remove_node_and_edge_specific_visual_properties(self, vis_aspect):
        """
        Removes node and edge specific visual properties

        :return: **vis_aspect* with node and edge
        :rtype: list
        """
        if vis_aspect is None:
            return vis_aspect
        new_list = []
        for entry in vis_aspect:
            if NiceCXNetwork.PROPERTIES_OF in entry:
                if entry[NiceCXNetwork.PROPERTIES_OF] == NiceCXNetwork.PROPS_OF_NODES:
                    continue
                if entry[NiceCXNetwork.PROPERTIES_OF] == NiceCXNetwork.PROPS_OF_EDGES:
                    continue
            new_list.append(entry)
        return new_list

    def apply_style_from_network(self, nicecxnetwork):
        """
        Applies Cytoscape visual properties from the network passed into this method.
        The style is pulled from :py:const:`~.NiceCXNetwork.VISUAL_PROPERTIES` or
        :py:const:`~.NiceCXNetwork.CY_VISUAL_PROPERTIES`

        :param nicecxnetwork: Network to extract style from
        :type nicecxnetwork: :py:class:`~.NiceCXNetwork`
        :raises TypeError: If object passed in is NOT a :py:class:`~.NiceCXNetwork` object or if object is None
        :raises NDExError: If :py:class:`~.NiceCXNetwork` does not have any visual styles
        :return: None
        :rtype: None
        """
        if nicecxnetwork is None:
            raise TypeError('Object passed in is None')
        if not isinstance(nicecxnetwork, NiceCXNetwork):
            raise TypeError('Object passed in is not NiceCXNetwork')

        vis_props_aspect = nicecxnetwork._get_visual_properties_aspect()
        if vis_props_aspect is None:
            raise NDExError('No visual style found in network')

        clean_vis_props_aspect = self._remove_node_and_edge_specific_visual_properties(vis_props_aspect)

        self._set_visual_properties_aspect(clean_vis_props_aspect)

    def _delete_deprecated_visual_properties_aspect(self):
        """
        If found removes deprecated :py:const:`~.NiceCXNetwork.CY_VISUAL_PROPERTIES`
        from opaque aspects and from metadata
        :return: None
        :rtype: None
        """
        opaque_aspect_names = self.get_opaque_aspect_names()
        if opaque_aspect_names is not None:
            if NiceCXNetwork.VISUAL_PROPERTIES in opaque_aspect_names:
                self.logger.debug(NiceCXNetwork.VISUAL_PROPERTIES +
                                  ' in opaque aspect. Removing entry')
                self.remove_opaque_aspect(NiceCXNetwork.VISUAL_PROPERTIES)
                if NiceCXNetwork.VISUAL_PROPERTIES in self.metadata:
                    self.logger.warning(NiceCXNetwork.VISUAL_PROPERTIES +
                                        ' found in metadata. this should'
                                        ' be removed')

    def _set_visual_properties_aspect(self, visual_props_aspect):
        """
        Replaces existing visual properties with data passed in.
        This method will update meta data and remove all visual aspects
        setting the new data to :py:const:`~.NiceCXNetwork.CY_VISUAL_PROPERTIES`
        aspect

        :param visual_props_aspect: visual properties aspect
        :type visual_props_aspect: list
        :raises TypeError: If **visual_props_aspect** is `None`
        :return: None
        """
        if visual_props_aspect is None:
            raise TypeError('Visual Properties aspect is None')

        self._delete_deprecated_visual_properties_aspect()

        self.set_opaque_aspect(NiceCXNetwork.CY_VISUAL_PROPERTIES,
                               visual_props_aspect)
        mde = {
            'name': NiceCXNetwork.CY_VISUAL_PROPERTIES,
            'elementCount': len(visual_props_aspect),
            'version': "1.0",
            'consistencyGroup': 1,
            'properties': []
        }
        self.metadata[NiceCXNetwork.CY_VISUAL_PROPERTIES] = mde

    def apply_template(self, server, uuid, username=None, password=None):
        """
        Applies the Cytoscape visual properties of a network from the provided
        uuid to this network.

        This allows the use of networks formatted in Cytoscape as templates to apply
        visual styles to other networks.

        .. versionchanged:: 3.5.0
           Fixed bug where style from template was appended
           instead of replacing the existing style. In most cases, method
           now raises :py:class:`~ndex2.exceptions.NDExError` and
           subclasses instead of more generic :py:class:`Exception`

        .. code-block:: python

            from ndex2.nice_cx_network import NiceCXNetwork

            nice_cx = NiceCXNetwork()
            nice_cx.apply_template('public.ndexbio.org',
                                   '51247435-1e5f-11e8-b939-0ac135e8bacf')

        :param server: server host name (i.e. public.ndexbio.org)
        :type server: str
        :param username: username (optional - used when accessing private networks)
        :type username: str
        :param password: password (optional - used when accessing private networks)
        :type password:  str
        :param uuid: uuid of the styled network
        :type uuid: str
        :raises NDExError: Raised if *server* or *uuid* not set or if metaData is not found
                           in the network specified by *uuid* or some other server error
        :raises NDExUnauthorizedError: If credentials not authorized to access network
                                       specified by *uuid*
        :raises NDExNotFoundError: If network with *uuid* not found
        :return: None
        :rtype: None
        """
        error_message = []
        if not server:
            error_message.append('server')
        if not uuid:
            error_message.append('uuid')

        if len(error_message) > 0:
            raise NDExError(', '.join(error_message) +
                            ' not specified in apply_template')

        # ===================
        # METADATA
        # ===================
        available_aspects = []
        metadata_return = self.get_aspect(uuid, NiceCXNetwork.META_DATA,
                                          server, username, password)

        if metadata_return is None:
            raise NDExError('Template not found %s.' % uuid)

        for ae in (o for o in metadata_return):
            available_aspects.append(ae.get('name'))

        # =======================
        # ADD VISUAL PROPERTIES
        # =======================
        for oa in available_aspects:
            if NiceCXNetwork.VISUAL_PROPERTIES in oa or NiceCXNetwork.\
                    CY_VISUAL_PROPERTIES in oa:
                objects = self.get_aspect(uuid, oa, server,
                                          username, password)
                self._set_visual_properties_aspect(objects)

    def get_frag_from_list_by_key(self, cx, key):
        for aspect in cx:
            if key in aspect:
                return aspect[key]

        return []

    def to_pandas_dataframe(self, dataconverter=PandasDataConverter(),
                            include_attributes=False):
        """
        Network edges exported as a :py:class:`pandas.DataFrame`

        .. versionchanged:: 3.5.0
            Added **include_attributes** and  **dataconverter** parameters

        The following columns will be added to the :py:class:`pandas.DataFrame`:

        * **source** - Name of edge source node

        * **interaction** - Interaction between source and target node

        * **target** - Name of edge target node


        If **include_attributes** parameter is set to ``True`` then:

            All edge attributes will be also added as separate columns with
            same name.

            Attributes on **source** node will be added as a columns with ``source_``
            prefixed to name.

            Attributes on **target** node will be added as columns with ``target_``
            prefixed to name.

        .. note::

            Values will converted based on CX data types. See
            :py:class:`~ndex2.util.PandasDataConverter` for information
            on how conversion is performed

        .. code-block:: python

            from ndex2.nice_cx_network import NiceCXNetwork

            net = NiceCXNetwork()
            node_one = net.create_node('node1')
            node_two = net.create_node('node2')

            net.set_node_attribute(node_one, 'weight', 0.5, type='double')
            net.set_node_attribute(node_two, 'weight', 0.2, type='double')

            edge_one = net.create_edge(edge_source=node_one, edge_target=node_two,
                                       edge_interaction='binds')

            net.set_edge_attribute(edge_one, 'edgelabel', 'an edge')
            df = net.to_pandas_dataframe(include_attributes=True) # df is now a pandas dataframe

            print(df.head())

        Output from above code block:

        .. code-block:: python

               source interaction target edgelabel  target_weight  source_weight
            0  node1       binds  node2   an edge            0.2            0.5

        .. note::

            This method only processes nodes, edges, node attributes and
            edge attributes, but not network attributes or other aspects

        :param dataconverter: Object that converts CX data values to native
                              data types. Default is
                              :py:class:`~ndex2.util.PandasDataConverter`
        :type dataconverter: :py:class:`~ndex2.util.DataConverter`
        :param include_attributes: If `True` then edge attributes are added to
                                   :py:class:`pandas.DataFrame`, otherwise only
                                   **source**, **target**, and **interaction** are
                                   added
        :type include_attributes: bool
        :raises NDExInvalidParameterError: If **include_attributes** is not ``None`` or a :py:class:`bool`
        :return: Edge table with attributes
        :rtype: :py:class:`pandas.DataFrame`
        """
        if include_attributes is not None and isinstance(include_attributes, bool) is False:
            raise NDExInvalidParameterError('include_attributes must be None or a bool')

        rows = []
        if sys.version_info.major == 3:
            edge_items = self.edges.items()
        else:
            edge_items = self.edges.iteritems()

        edge_attr_name_set = set()
        node_attr_name_set = set()

        omit_attrs = True
        if include_attributes is not None and include_attributes is True:
            omit_attrs = False

        for k, v in edge_items:
            if omit_attrs is False:
                e_a = self.edgeAttributes.get(k)
                # ==========================
                # PROCESS EDGE ATTRIBUTES
                # ==========================
                add_this_dict = {}
                if e_a is not None:
                    for e_a_item in e_a:
                        add_this_dict[e_a_item.get('n')] = dataconverter.convert_value(e_a_item.get('v'),
                                                                                       e_a_item.get('d'))
                        edge_attr_name_set.add(e_a_item.get('n'))
                # ================================
                # PROCESS SOURCE NODE ATTRIBUTES
                # ================================
                s_a = self.nodeAttributes.get(v.get('s'))
                if s_a is not None:
                    for s_a_item in s_a:
                        add_this_dict['source_' + s_a_item.get('n')] = dataconverter.convert_value(s_a_item.get('v'),
                                                                                                       s_a_item.get('d'))
                        node_attr_name_set.add('source_' + s_a_item.get('n'))

                # ================================
                # PROCESS TARGET NODE ATTRIBUTES
                # ================================
                t_a = self.nodeAttributes.get(v.get('t'))
                if t_a is not None:
                    for t_a_item in t_a:
                        add_this_dict['target_' + t_a_item.get('n')] = dataconverter.convert_value(t_a_item.get('v'),
                                                                                                       t_a_item.get('d'))
                        node_attr_name_set.add('target_' + s_a_item.get('n'))

            if omit_attrs is False and add_this_dict:
                rows.append(dict(add_this_dict,
                                 source=self.nodes.get(v.get('s')).get('n'),
                                 target=self.nodes.get(v.get('t')).get('n'),
                                 interaction=v.get('i')))
            else:
                rows.append(dict(source=self.nodes.get(v.get('s')).get('n'),
                                 target=self.nodes.get(v.get('t')).get('n'),
                                 interaction=v.get('i')))
        if omit_attrs is False:
            df_columns = ['source', 'interaction', 'target'] + list(edge_attr_name_set) + list(node_attr_name_set)
        else:
            df_columns = ['source', 'interaction', 'target']

        return pd.DataFrame(rows, columns=df_columns)

    def add_metadata_stub(self, aspect_name):
        md = self.metadata.get(aspect_name)
        #if md is None:
        #    mde = MetaDataElement(elementCount=0, properties=[], version='1.0', consistencyGroup=1, name=aspect_name)
        #    self.add_metadata(mde)

    def to_cx_stream(self):
        """
        Returns a stream of the CX corresponding to the network. Can be used to post to endpoints that can accept
        streaming inputs

        :return: The CX stream representation of this network.
        :rtype: io.BytesIO
        """
        cx = self.to_cx()

        if sys.version_info.major == 3:
            return io.BytesIO(json.dumps(cx).encode('utf-8'))
        else:
            return_bytes = None
            try:
                return_bytes = io.BytesIO(json.dumps(cx))
            except UnicodeDecodeError as err1:
                print("Detected invalid encoding. Trying latin-1 encoding.")
                return_bytes = io.BytesIO(json.dumps(cx, encoding="latin-1"))
                print("Success")
            except Exception as err2:
                print(err2.message)

            return return_bytes

    def upload_to(self, server=None, username=None, password=None,
                  user_agent='', client=None):
        """
        Upload this network as a new network on NDEx server.

        .. versionchanged:: 3.4.0

            This method was switched to named arguments and the server and account
            credentials can be passed in one of two ways.

        Option 1) Set **username** and **password** parameters.

        Option 2) Set **client** parameter with valid :py:class:`~ndex2.client.Ndex2` object

        .. note::

            If **client** parameter is set, **username**, **password**, and **server**
            parameters are ignored

        Example:

        .. code-block:: python

            import ndex2
            nice_cx = ndex2.nice_cx_network.NiceCXNetwork()
            nice_cx.create_node('foo')

            # using production NDEx server
            nice_cx.update_to(username=user_var,
                              password=password_var)

            # if one needs to use alternate NDEx server
            nice_cx.update_to(server='public.ndexbio.org',
                              username=username_var,
                              password=password_var)

            # Option 2, create Ndex2 client object
            ndex_client = ndex2.client.Ndex2(username=username_var,
                                             password=password_var)

            # using NDEx client object for connection
            nice_cx.update_to(client=ndex_client)

        :param server: The NDEx server to upload the network to. Leaving unset or `None` will use production
        :type server: str
        :param username: The username of the account to store the network.
        :type username: str
        :param password: The password for the account.
        :type password: str
        :param user_agent: String to append to User-Agent field sent to NDEx REST service
        :type user_agent: str
        :param client: NDEx2 object with valid credentials. If set **server**, **username**, and **password**
                       parameters will be ignored.
        :type client: :py:class:`~ndex2.client.Ndex2`
        :return: The UUID of the network on NDEx.
        :rtype: str
        """
        if client is not None:
            ndex = client
        else:
            ndex = Ndex2(server, username, password, user_agent=user_agent)
        return ndex.save_new_network(self.to_cx())

    def update_to(self, uuid, server=None, username=None, password=None,
                  user_agent='', client=None):
        """
        Replace the network on NDEx server with matching NDEx `uuid` with
        this network.

        .. versionchanged:: 3.4.0

            This method was switched to named arguments and the server and account
            credentials can be passed in one of two ways.


        Option 1) Set **username** and **password** parameters.

        Option 2) Set **client** parameter with valid :py:class:`~ndex2.client.Ndex2` object

        .. note::

            If **client** parameter is set, **username**, **password**, and **server**
            parameters are ignored.

        Example:

        .. code-block:: python

            import ndex2
            nice_cx = ndex2.nice_cx_network.NiceCXNetwork()
            nice_cx.create_node('foo')

            # using production NDEx server
            nice_cx.update_to('2ec87c51-c349-11e8-90ac-525400c25d22',
                              username=user_var,
                              password=password_var)

            # if one needs to use alternate NDEx server
            nice_cx.update_to('2ec87c51-c349-11e8-90ac-525400c25d22',
                              server='public.ndexbio.org',
                              username=username_var,
                              password=password_var)

            # Option 2, create Ndex2 client object
            ndex_client = ndex2.client.Ndex2(username=username_var,
                                             password=password_var)

            # using NDEx client object for connection
            nice_cx.update_to('2ec87c51-c349-11e8-90ac-525400c25d22',
                              client=ndex_client)

        :param uuid: UUID of the network on NDEx.
        :type uuid: str
        :param server: The NDEx server to upload the network to. Leaving unset or `None` will use production.
        :type server: str
        :param username: The username of the account to store the network.
        :type username: str
        :param password: The password for the account.
        :type password: str
        :param user_agent: String to append to User-Agent field sent to NDEx REST service
        :type user_agent: str
        :param client: NDEx2 object with valid credentials. If set **server**, **username**, and **password**
                       parameters will be ignored.
        :type client: :py:class:`~ndex2.client.Ndex2`
        :return: Empty string
        :rtype: str

        """
        cx = self.to_cx()
        if client is not None:
            ndex = client
        else:
            ndex = Ndex2(server, username, password, user_agent=user_agent)

        if len(cx) > 0:
            if cx[len(cx) - 1] is not None:
                if cx[len(cx) - 1].get('status') is None:
                    # No STATUS element in the array.  Append a new status
                    cx.append({"status": [{"error": "", "success": True}]})
                else:
                    if len(cx[len(cx) - 1].get('status')) < 1:
                        # STATUS element found, but the status was empty
                        cx[len(cx) - 1].get('status').append({"error": "",
                                                              "success": True})

            if sys.version_info.major == 3:
                stream = io.BytesIO(json.dumps(cx).encode('utf-8'))
            else:
                stream = io.BytesIO(json.dumps(cx))

            return ndex.update_cx_network(stream, uuid)
        else:
            raise IndexError("Cannot save empty CX.  Please provide a "
                             "non-empty CX document.")

    def _get_node_and_edge_items(self):
        """
        Deals with differences in API of items() call
        between Python 2 and 3
        If Python >= 3 gets node.items() and edge.items() otherwise
        returns node.iteritems() and edge.iteritems()

        :return: tuple (node iterator, edge iterator)
        :rtype: tuple
        """
        if NiceCXNetwork._is_python_three_or_greater():
            return self.nodes.items(), self.edges.items()

        return self.nodes.iteritems(), self.edges.iteritems()

    def to_networkx(self, mode='legacy'):
        """
        Returns a NetworkX ``Graph()`` object or one of its subclasses
        based on the network.
        The `mode` parameter dictates how the translation occurs.

        This method currently supports the following mode values:

        .. warning::

            **legacy** mode has known bugs when
            networkx 2.0+ or greater is installed.

            See the description on **legacy** mode below for more information.

        **Modes:**

        **legacy:**

            If mode set to **legacy** then this method will behave
            as it has for all versions of NDEx2 Python Client 3.1.0 and
            earlier which varies depending on version of networkx installed
            as described here:

            For networkx 2.0 and greater:
            (see :class:`LegacyNetworkXVersionTwoPlusFactory`)

            For older versions of networkx the following class is
            used with the `legacymode` parameter set to `True`:
            (see :class:`DefaultNetworkXFactory`)

        **default:**

            If mode is **default** or None then this method uses
            :class:`DefaultNetworkXFactory` regardless of
            networkx installed with `legacymode` set to `False`

            .. note::

                ``default`` mode is the preferred mode to use

        Examples:

        .. code-block:: python

            # returns networkx graph using improved converter
            graph = nice_cx.to_networkx(mode='default')

            # returns networkx graph using legacy implementation
            graph = nice_cx.to_networkx(mode='legacy)


        :param mode: Since translation to networkx can be done in many ways this mode lets
                     the caller dictate the method.
        :type mode: string
        :raises NDExError: If `mode` is not None, 'legacy', or 'default'
        :return: Networkx graph
        :rtype: :class:`networkx.Graph` or :class:`networkx.MultiGraph`
        """
        if mode is None or mode == 'default':
            fac = DefaultNetworkXFactory()
        elif mode == 'legacy':
            nx_major_version = NetworkXFactory.get_networkx_major_version()
            if nx_major_version >= 2.0:
                fac = LegacyNetworkXVersionTwoPlusFactory()
            else:
                fac = DefaultNetworkXFactory(legacymode=True)
        else:
            raise NDExError(str(mode) + ' is not a valid mode')

        return fac.get_graph(self)

    def get_summary(self):
        """
        .. deprecated:: 3.3.2

            This method has been deprecated.  Please use :func:`print_summary`


        """

        raise Warning('get_summary() is deprecated.  Please use print_summary() instead')

        n_a_count = 0
        for k, v in self.nodeAttributes.items():
            n_a_count += len(v)

        e_a_count = 0
        for k, v in self.edgeAttributes.items():
            e_a_count += len(v)

        network_name = self.get_name()
        if not network_name:
            network_name = 'Untitled'

        summary_json = {
            'Name': network_name,
            'Nodes': len(self.nodes),
            'Edges': + len(self.edges),
            'Node Attributes': n_a_count,
            'Edge Attributes': e_a_count
        }

        return summary_json

    def print_summary(self):
        """
        Print a network summary

        :return: Network summary
        :rtype: string
        """
        n_a_count = 0
        for k, v in self.nodeAttributes.items():
            n_a_count += len(v)

        e_a_count = 0
        for k, v in self.edgeAttributes.items():
            e_a_count += len(v)

        network_name = self.get_name()
        if not network_name:
            network_name = 'Untitled'

        summary_string = \
            'Name: ' + network_name + '\n'\
            'Nodes: ' + str(len(self.nodes)) + '\n'\
            + 'Edges: ' + str(len(self.edges)) + '\n'\
            + 'Node Attributes: ' + str(n_a_count) + '\n'\
            + 'Edge Attributes: ' + str(e_a_count) + '\n'

        print(summary_string)

    def __str__(self):
        return 'nodes: %d \n edges: %d' % (len(self.nodes), len(self.edges))

    def to_cx(self, log_to_stdout=True):
        """
        Return the CX corresponding to the network.

        .. versionchanged:: 3.5.0
           Added **log_to_stdout** param which lets caller silence
           print statement *Generating CX*

        :param log_to_stdout: If ``True`` then code will output to
                              standard out *Generating CX*
        :type log_to_stdout: bool
        :return: CX representation of the network
        :rtype: CX (list of dict aspects)
        """
        output_cx = [{"numberVerification": [{"longNumber": 281474976710655}]}]

        if log_to_stdout is not None and log_to_stdout is True:
            print('Generating CX')

        #=====================================================
        # IF THE @ID IS NOT NUMERIC WE NEED TO CONVERT IT TO
        # INT BY USING THE INDEX OF THE NON-NUMERIC VALUE
        #=====================================================
        if self.nodes:
            output_cx.append(self.generate_aspect('nodes'))
        if self.edges:
            output_cx.append(self.generate_aspect('edges'))
        if self.networkAttributes:
            output_cx.append(self.generate_aspect('networkAttributes'))
        if self.nodeAttributes:
            output_cx.append(self.generate_aspect('nodeAttributes'))
        if self.edgeAttributes:
            output_cx.append(self.generate_aspect('edgeAttributes'))
        if self.citations:
            output_cx.append(self.generate_aspect('citations'))
        if self.nodeCitations:
            output_cx.append(self.generate_aspect('nodeCitations'))
        if self.edgeCitations:
            output_cx.append(self.generate_aspect('edgeCitations'))
        if self.supports:
            output_cx.append(self.generate_aspect('supports'))
        if self.edgeSupports:
            output_cx.append(self.generate_aspect('edgeSupports'))
        if self.opaqueAspects:
            for oa in self.opaqueAspects:
                if isinstance(self.opaqueAspects[oa], bytes):
                    bytes_string = self.opaqueAspects[oa].decode('ascii')
                    output_cx.append({oa: [bytes_string]})
                else:
                    output_cx.append({oa: self.opaqueAspects[oa]})
                oa_md = self.metadata.get(oa)
                if oa_md:
                    oa_md['elementCount'] = len(self.opaqueAspects[oa])
                else:
                    self.metadata[oa] = {
                        'name': oa,
                        'elementCount': len(self.opaqueAspects[oa]),
                        'idCounter': len(self.opaqueAspects[oa]) + 1,
                        'properties': []
                    }

        if self.metadata:
            #===========================
            # UPDATE CONSISTENCY GROUP
            #===========================
            metadata_list = []
            for k, mdata in self.metadata.items():
                metadata_list.append(mdata)

            output_cx.insert(1, {'metaData': metadata_list})

            if output_cx[-1].get('status') is None:
                output_cx.append({'status': [{'error': '', 'success': True}]})

        return output_cx

    def generate_aspect(self, aspect_name):
        core_aspect = ['nodes', 'edges', 'networkAttributes', 'nodeAttributes',
                       'edgeAttributes', 'metaData', 'citations', 'supports']
        aspect_element_array = []
        element_count = 0
        element_id_max = 0

        use_this_aspect = None
        #=============================
        # PROCESS CORE ASPECTS FIRST
        #=============================
        if aspect_name in core_aspect:
            use_this_aspect = self.string_to_aspect_object(aspect_name)

        if use_this_aspect is not None:
            if isinstance(use_this_aspect, dict):
                if aspect_name in ['nodes', 'edges']:
                    for k, asp in use_this_aspect.items():
                        element_count += 1
                        if asp.get('@id') > element_id_max:
                            element_id_max = asp.get('@id')
                        aspect_element_array.append(asp)
                else:
                    for k, asp in use_this_aspect.items():
                        if isinstance(asp, list):
                            for asp_item in asp:
                                element_count += 1
                                aspect_element_array.append(asp_item)
                        else:
                            element_count += 1
                            aspect_element_array.append(asp)
            elif isinstance(use_this_aspect, list):
                aspect_element_array = use_this_aspect
                element_count = len(use_this_aspect)

        else:
            #===========================
            # PROCESS NON-CORE ASPECTS
            #===========================
            use_this_aspect = self.string_to_aspect_object(aspect_name)

            if use_this_aspect is not None:
                if isinstance(use_this_aspect, dict):
                    items = None
                    if sys.version_info.major == 3:
                        items = use_this_aspect.items()
                    else:
                        items = use_this_aspect.iteritems()

                    for k, v in items:
                        if aspect_name == 'edgeSupports':
                            if isinstance(v, list):
                                aspect_element_array.append({'po': [k], 'supports': v})
                            else:
                                aspect_element_array.append({'po': [k], 'supports': [v]})
                        else:
                            if isinstance(v, list):
                                aspect_element_array.append({'po': [k], 'citations': v})
                            else:
                                aspect_element_array.append({'po': [k], 'citations': [v]})
                        element_count +=1
                else:
                    raise Exception('Citation was not in json format')
            else:
                return None

        md = {
            'name': aspect_name,
            'elementCount': element_count,
            'idCounter': element_count,
            'version': "1.0",
            'consistencyGroup': 1,
            'properties': []
        }

        self.metadata[aspect_name] = md

        aspect = {aspect_name: aspect_element_array}

        return aspect

    def generate_metadata_aspect(self):
        aspect_element_array = []
        element_count = 0
        element_id_max = 0

        use_this_aspect = self.string_to_aspect_object('metaData')

        if use_this_aspect is not None:
            if sys.version_info.major == 3:
                items = use_this_aspect.items()
            else:
                items = use_this_aspect.iteritems()

            for k, v in items:
                add_this_element = v.to_cx()
                id = add_this_element.get('@id')

                if id is not None and id > element_id_max:
                    element_id_max = id
                aspect_element_array.append(add_this_element)
                element_count +=1

        aspect = {'metaData': aspect_element_array}

        return aspect

    def handle_metadata_update(self, aspect_name):
        aspect = self.string_to_aspect_object(aspect_name)

    def update_consistency_group(self):
        consistency_group = 1
        if self.metadata:
            for mi_k, mi_v in self.metadata.items():
                cg = mi_v.get_consistency_group()
                if cg > consistency_group:
                    consistency_group = cg

            consistency_group += 1  # bump the consistency group up by one

            for mi_k, mi_v in self.metadata.items():
                mi_v.set_consistency_group(consistency_group)

    def generate_metadata(self, G, unclassified_cx):

        return_metadata = []
        consistency_group = 1
        if self.metadata_original is not None:
            for mi in self.metadata_original:
                if mi.get("consistencyGroup") is not None:
                    if mi.get("consistencyGroup") > consistency_group:
                        consistency_group = mi.get("consistencyGroup")
                else:
                    mi['consistencyGroup'] = 0
            consistency_group += 1  # bump the consistency group up by one


        #========================
        # Nodes metadata
        #========================
        node_ids = [n[0] for n in G.nodes_iter(data=True)]
        if len(node_ids) < 1:
            node_ids = [0]
        return_metadata.append(
            {
                "consistencyGroup": consistency_group,
                "elementCount": len(node_ids),
                "idCounter": max(node_ids),
                "name": "nodes",
                "properties": [],
                "version": "1.0"
            }
        )

        #========================
        # Edges metadata
        #========================
        edge_ids = [e[2]for e in G.edges_iter(data=True, keys=True)]
        if len(edge_ids) < 1:
            edge_ids = [0]
        return_metadata.append(
            {
                "consistencyGroup": consistency_group,
                "elementCount": len(edge_ids),
                "idCounter": max(edge_ids),
                "name": "edges",
                "properties": [],
                "version": "1.0"
            }
        )

        #=============================
        # Network Attributes metadata
        #=============================
        if len(G.graph) > 0:
            return_metadata.append(
                {
                    "consistencyGroup": consistency_group,
                    "elementCount": len(G.graph),
                    "name": "networkAttributes",
                    "properties": [],
                    "version": "1.0"
                }
            )

        #===========================
        # Node Attributes metadata
        #===========================
        #id_max = 0
        attr_count = 0
        for node_id, attributes in G.nodes_iter(data=True):
            for attribute_name in attributes:
                if attribute_name != "name" and attribute_name != "represents":
                    attr_count += 1

        if attr_count > 0:
            return_metadata.append(
                {
                    "consistencyGroup": consistency_group,
                    "elementCount": attr_count,
                    #"idCounter": id_max,
                    "name": "nodeAttributes",
                    "properties": [],
                    "version": "1.0"
                }
            )

        #===========================
        # Edge Attributes metadata
        #===========================
        #id_max = 0
        attr_count = 0
        for s, t, id, a in G.edges(data=True, keys=True):
            if(bool(a)):
                for attribute_name in a:
                    if attribute_name != "interaction":
                        attr_count += 1

        if(attr_count > 0):
            return_metadata.append(
                {
                    "consistencyGroup" : consistency_group,
                    "elementCount" : attr_count,
                    #"idCounter": id_max,
                    "name" : "edgeAttributes",
                    "properties" : [ ],
                    "version" : "1.0"
                }
            )

        #===========================
        # cyViews metadata
        #===========================
        if self.view_id != None:
            return_metadata.append(
                {
                    "elementCount": 1,
                    "name": "cyViews",
                    "properties": [],
                    "consistencyGroup" : consistency_group
                }
            )

        #===========================
        # subNetworks metadata
        #===========================
        if self.subnetwork_id != None:
            return_metadata.append(
                {
                    "elementCount": 1,
                    "name": "subNetworks",
                    "properties": [],
                    "consistencyGroup" : consistency_group
                }
            )

        #===========================
        # networkRelations metadata
        #===========================
        if self.subnetwork_id != None and self.view_id != None:
            return_metadata.append(
                {
                    "elementCount": 2,
                    "name": "networkRelations",
                    "properties": [],
                    "consistencyGroup" : consistency_group
                }
            )

        #===========================
        # citations and supports metadata
        #===========================
        if len(self.support_map) > 0:
            return_metadata.append(
                {
                    "elementCount": len(self.support_map),
                    "name": "supports",
                    "properties": [],
                    "idCounter": max(self.support_map.keys()),
                    "consistencyGroup" : consistency_group
                }
            )

        if len(self.node_support_map) > 0:
            return_metadata.append(
                {
                    "elementCount": len(self.node_support_map),
                    "name": "nodeSupports",
                    "properties": [],
                    "consistencyGroup" : consistency_group
                }
            )
        if len(self.edge_support_map) > 0:
            return_metadata.append(
                {
                    "elementCount": len(self.edge_support_map),
                    "name": "edgeSupports",
                    "properties": [],
                    "consistencyGroup" : consistency_group
                }
            )

        if len(self.citation_map) > 0:
            return_metadata.append(
                {
                    "elementCount": len(self.citation_map),
                    "name": "citations",
                    "properties": [],
                    "idCounter": max(self.citation_map.keys()),
                    "consistencyGroup" : consistency_group
                }
            )

        if len(self.node_citation_map) > 0:
            return_metadata.append(
                {
                    "elementCount": len(self.node_citation_map),
                    "name": "nodeCitations",
                    "properties": [],
                    "consistencyGroup" : consistency_group
                }
            )

        if len(self.edge_citation_map) > 0:
            return_metadata.append(
                {
                    "elementCount": len(self.edge_citation_map),
                    "name": "edgeCitations",
                    "properties": [],
                    "consistencyGroup" : consistency_group
                }
            )

        if len(self.function_term_map) > 0:
            return_metadata.append(
                {
                    "elementCount": len(self.function_term_map),
                    "name": "functionTerms",
                    "properties": [],
                    "consistencyGroup" : consistency_group
                }
            )

        if len(self.reified_edges) > 0:
            return_metadata.append(
                {
                    "elementCount": len(self.reified_edges),
                    "name": "reifiedEdges",
                    "properties": [],
                    "consistencyGroup" : consistency_group
                }
            )

        #===========================
        # ndexStatus metadata
        #===========================
        return_metadata.append(
            {
                "consistencyGroup": consistency_group,
                "elementCount": 1,
                "name": "ndexStatus",
                "properties": [],
                "version": "1.0"
            }
        )

        #===========================
        # cartesianLayout metadata
        #===========================
        if self.pos and len(self.pos) > 0:
            return_metadata.append(
                {
                    "consistencyGroup": consistency_group,
                    "elementCount": len(self.pos),
                    "name": "cartesianLayout",
                    "properties": [],
                    "version": "1.0"
                }
            )

        #===========================
        # OTHER metadata
        #===========================
        for asp in self.unclassified_cx:
            try:
                aspect_type = asp.iterkeys().next()
                if(aspect_type == "visualProperties"
                   or aspect_type == "cyVisualProperties"
                   or aspect_type == "@context"):
                    return_metadata.append(
                        {
                            "consistencyGroup": consistency_group,
                            "elementCount": len(asp[aspect_type]),
                            "name": aspect_type,
                            "properties": []
                         }
                    )
            except Exception as e:
                print(e.message)

        return [{'metaData': return_metadata}]

    def string_to_aspect_object(self, aspect_name):
        """
        Given an aspect name via **aspect_name**
        this method returns the corresponding aspect
        object

        .. versionchanged:: 3.5.0
           ``@context`` aspect removed

        :param aspect_name: name of aspect
        :type aspect_name: str
        :return: Aspect object or None
        """
        if aspect_name == 'metaData':
            return self.metadata
        elif aspect_name == 'nodes':
            return self.nodes
        elif aspect_name == 'edges':
            return self.edges
        elif aspect_name == 'networkAttributes':
            return self.networkAttributes
        elif aspect_name == 'nodeAttributes':
            return self.nodeAttributes
        elif aspect_name == 'edgeAttributes':
            return self.edgeAttributes
        elif aspect_name == 'citations':
            return self.citations
        elif aspect_name == 'nodeCitations':
            return self.nodeCitations
        elif aspect_name == 'edgeCitations':
            return self.edgeCitations
        elif aspect_name == 'edgeSupports':
            return self.edgeSupports
        elif aspect_name == 'supports':
            return self.supports

    def get_aspect(self, uuid, aspect_name, server, username, password, stream=False):
        """

        :param uuid:
        :param aspect_name:
        :param server:
        :param username:
        :param password:
        :param stream: refers to the response not the request
        :type stream: bool
        :return:
        """
        if stream:
            return self.stream_aspect(uuid, aspect_name, server, username, password)
        else:
            return self.get_stream(uuid, aspect_name, server, username, password)

    def get_stream(self, uuid, aspect_name, server, username, password):
        """

        :param uuid: Unique id of network in NDEx
        :type uuid: str
        :param aspect_name: aspect to stream. If `metaData` then
                            the meta data of the network will be
                            returned
        :type aspect_name: str
        :param server: Server to connect to. If value does not
                       start with http, then http:// is prepended
        :type server: str
        :param username: NDEx username or None to not authenticate
        :type username: str
        :param password: NDEx password or None to not authenticate
        :type password: str
        :return:
        :rtype:
        """
        if not server.lower().startswith('http'):
            server = 'http://' + server

        s = requests.session()
        if username and password:
            #  add credentials to the session, if available
            s.auth = (username, password)

        url_suffix = '/' + aspect_name

        # if the metaData aspect is the aspect name
        # it means caller just wants the meta data aspect
        # which is obtained by omitting the aspect name
        # from the end of the URL
        if aspect_name == 'metaData':
            url_suffix = ''

        aspect_response = s.get(server + '/v2/network/' + uuid +
                                '/aspect' + url_suffix)
        if aspect_response.status_code == 401:
            raise NDExUnauthorizedError(str(aspect_response.text))
        if aspect_response.status_code == 404:
            raise NDExNotFoundError(str(aspect_response.text))
        if aspect_response.status_code > 200:
            raise NDExError(str(aspect_response.text))
        try:
            json_response = aspect_response.json()
            if aspect_name == 'metaData':
                return json_response[aspect_name]
            return json_response
        except json.decoder.JSONDecodeError as de:
            raise NDExError('Error parsing JSON from server: ' +
                            str(de))
        except requests.exceptions.RequestException as e:
            raise NDExError('Error parsing JSON from server: ' +
                            str(e))
        finally:
            s.close()

    def stream_aspect(self, uuid, aspect_name, server, username, password):
        if 'http' not in server:
            server = 'http://' + server
        if aspect_name == 'metaData':

            s = requests.session()
            if username and password:
                # add credentials to the session, if available
                s.auth = (username, password)
            md_response = s.get(server + '/v2/network/' + uuid + '/aspect')
            json_response = md_response.json()
            s.close()
            return json_response.get('metaData')
        else:
            if username and password:
                #base64string = base64.b64encode('%s:%s' % (username, password))
                request = Request(server + '/v2/network/' + uuid + '/aspect/' + aspect_name, headers={"Authorization": "Basic " + base64.encodestring(username + ':' + password).replace('\n', '')})
            else:
                request = Request(server + '/v2/network/' + uuid + '/aspect/' + aspect_name)
            try:
                urlopen_result = urlopen(request) #'http://dev2.ndexbio.org/v2/network/' + uuid + '/aspect/' + aspect_name)
            except HTTPError as e:
                print(e.code)
                return []
            except URLError as e:
                print('Other error')
                print('URL Error %s' % e.message())
                return []

            return_items = ijson.items(urlopen_result, 'item')
            return return_items

    def _stringify_node_attributes(self):
        for node_id, node in self.get_nodes():
            if self.get_node_attributes(node) is not None:
                for attr in self.get_node_attributes(node):
                    if isinstance(attr['v'], dict) or isinstance(attr['v'], list):
                        attr['v'] = json.dumps(attr['v'])
                    elif not isinstance(attr['v'], str):
                        attr['v'] = str(attr['v'])


class DecimalEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        if sys.version_info.major == 3:
            if isinstance(o, np.int64):
                return int(o)
        return super(DecimalEncoder, self).default(o)


class NetworkXFactory(object):
    """
    Base class for subclasses that implement a
    factory that creates :class:`networkx.Graph` objects
    and contains a couple utility methods used by
    implementing factory classes

    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._nx_major_version = NetworkXFactory.get_networkx_major_version()

    @staticmethod
    def get_networkx_major_version(networkx_version=nx.__version__):
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

    def get_graph(self, nice_cx_network, networkx_graph=None):
        """
        Creates NetworkX Graph object which can
        be one of the multiple types of Graph objects

        :raises NotImplementedError: Subclasses should implement this method
        :param nice_cx_network: Network to create networkx graph from
        :type nice_cx_network: :py:class:`NiceCXNetwork`
        :param networkx_graph: Empty networkx graph to populate
        :type networkx_graph: :class:`networkx.Graph` or subtype
        :return: networkx Graph object of some type
        :rtype: :class:`networkx.Graph`
        """
        raise NotImplementedError('Must be implemented by sub class')

    def copy_cartesian_coords_into_graph(self, nice_cx_network,
                                         networkx_graph):
        """
        Examines the `nice_cx_network` extracting the content of
        the opaque aspect :py:const:`~ndex2.constants.CARTESIAN_LAYOUT_ASPECT`

        .. versionchanged:: 3.5.0
           code now inverts value of y coordinate
           so position is correct in networkx

        If data is found in above aspect, then this method iterates through the
        list of values which is assumed to be a dictionary of node ids
        with coordinates as seen here::

            [
             { 'node': <id>, 'x': <x coord>, 'y': <y coord},
             { 'node': <id>, 'x': <x coord>, 'y': <y coord},
             .
             .
            ]

        These values (as seen in example above) are stored in the
        `networkx_graph` object as tuples with id of node set as key like so:

        .. code-block:: python

            networkx_graph.pos[<id from above>] = (<x coord>, <y coord>)


        :param nice_cx_network: Input network
        :type nice_cx_network: :py:class:`NiceCXNetwork`
        :param networkx_graph: Network to append coordinates to
        :raises NDExError: If either input parameter is None
        :type networkx_graph: :class:`networkx.Graph`
        :return: None
        """
        if nice_cx_network is None:
            raise NDExError('Input network is None')

        if networkx_graph is None:
            raise NDExError('Output Graph is None')

        cl = nice_cx_network.get_opaque_aspect(constants.CARTESIAN_LAYOUT_ASPECT)
        if not cl:
            return

        networkx_graph.pos = {}
        for coord in cl:
            ctuple = (coord.get(constants.LAYOUT_X),
                      -coord.get(constants.LAYOUT_Y))
            networkx_graph.pos[coord.get(constants.LAYOUT_NODE)] = ctuple

    def add_network_attributes_from_nice_cx_network(self, nice_cx_network,
                                                    networkx_graph):
        """
        Iterates through network attributes of input `nice_cx_network`
        appending the attributes to the graph object passed in
        setting the values like so:

        .. code-block:: python

            networkx_graph.graph[attribute_name] = attribute_value

        If the value of a network attribute is of type list then the
        values are converted to strings and concatenated into a single
        string separated by commas.

        :param nice_cx_network: Network to extract network attributes from
        :type nice_cx_network: :py:class:`NiceCXNetwork`
        :param networkx_graph: networkx Graph object, should work with
                               any of the types of Graphs ie MultiGraph etc..
        :type networkx_graph: :class:`networkx.Graph`
        :raises NDExError: If either input parameter is None
        :return: None
        """
        if nice_cx_network is None:
            raise NDExError('Input network is None')

        if networkx_graph is None:
            raise NDExError('Output Graph is None')

        for name in nice_cx_network.get_network_attribute_names():
            netattr = nice_cx_network.get_network_attribute(name)
            if netattr is None:
                continue
            val = netattr[constants.NET_ATTR_VALUE]
            if isinstance(val, list):
                val = ','.join([str(entry) for entry in val])
            networkx_graph.graph[name] = val

    def add_node(self, networkx_graph, nodeid, node_attributes, name=None, represents=None):
        """
        Adds node to `graph` dealing with differences between
        networkx 1.x and 2.x+

        :param networkx_graph: networkx graph to add node to
        :type networkx_graph: :class:`networkx.Graph` or one of its subtypes
        :param nodeid: node identifier can be string, int etc.
        :param node_attributes: dictionary of key => value data to set
                               set node attributes with
        :type node_attributes: dict
        :param name: name of node that is set as attribute with key 'name' on
                     node
        :type name: string
        :param represents: represents value for node that is set as attribute
                           with key 'represents' on node
        :return: None
        """
        if self._nx_major_version >= 2:
            self._add_node_networkx_two_plus(networkx_graph, nodeid, node_attributes,
                                             name=name,
                                             represents=represents)
            return

        self._add_node_networkx_legacy(networkx_graph, nodeid, node_attributes,
                                       name=name, represents=represents)

    def _add_node_networkx_legacy(self, networkx_graph, nodeid, node_attributes,
                                  name=None, represents=None):
        """

        :param networkx_graph:
        :param nodeid:
        :param node_attributes:
        :param name:
        :param represents:
        :return:
        """
        node_attrs = None
        if node_attributes:
            node_attrs = {}
            for na_item in node_attributes:
                node_attrs[na_item.get(constants.NODE_ATTR_NAME)] = na_item.get(constants.NODE_ATTR_VALUE)
        if represents:
            networkx_graph.add_node(nodeid, node_attrs, name=name, represents=represents)
        else:
            networkx_graph.add_node(nodeid, node_attrs, name=name)

    def _add_node_networkx_two_plus(self, networkx_graph, nodeid, node_attributes,
                                    name=None,
                                    represents=None):
        """
        Adds node to `graph` assuming installed version of networkx is 2 or greater

        :param networkx_graph: Graph to add node to
        :type networkx_graph: :class:`networkx.Graph`
        :param nodeid: id of node, could be str, int
        :param node_attributes: dictionary of node attributes usually obtained by
                                invoking :py:func:`NiceCXNetwork.get_node_attributes(nodeid)`
        :type node_attributes: dict
        :param name:
        :param represents:
        :return:
        """
        networkx_graph.add_node(nodeid)
        if node_attributes:
            for n_a in node_attributes:
                networkx_graph.nodes[nodeid][n_a.get(constants.NODE_ATTR_NAME)] = n_a.get(constants.NODE_ATTR_VALUE)
        if represents:
            networkx_graph.nodes[nodeid]['represents'] = represents
        if name:
            networkx_graph.nodes[nodeid]['name'] = name

    def add_edge(self, networkx_graph, source_node, target_node, attribute_dict):
        """
        Adds edge to `graph` dealing with differences between
        networkx 1.x and 2.x+

        :param networkx_graph: networkx graph to add node to
        :type networkx_graph: :class:`networkx.Graph` or one of its subtypes
        :param source_node: id of source node
        :param target_node: id of target node
        :param attribute_dict: dictionary of edge attributes
        :type attribute_dict: dict
        :return: None
        """
        if self._nx_major_version >= 2:
            self._add_edge_networkx_two_plus(networkx_graph, source_node,
                                             target_node, attribute_dict)
            return

        self._add_edge_networkx_legacy(networkx_graph, source_node, target_node,
                                       attribute_dict)

    def _add_edge_networkx_two_plus(self, networkx_graph, source_node,
                                    target_node, attribute_dict):
        """

        :param networkx_graph:
        :param source_node:
        :param target_node:
        :param attribute_dict:
        :return:
        """
        edge_key = networkx_graph.add_edge(source_node, target_node)
        if attribute_dict is None:
            return

        if edge_key is None:
            for k in attribute_dict:
                networkx_graph[source_node][target_node][k] = attribute_dict[k]
            return

        for k in attribute_dict:
            networkx_graph[source_node][target_node][edge_key][k] = attribute_dict[k]

    def _add_edge_networkx_legacy(self, networkx_graph, source_node,
                                  target_node, attribute_dict):
        """

        :param networkx_graph:
        :param source_node:
        :param target_node:
        :param attribute_dict:
        :return:
        """
        networkx_graph.add_edge(source_node, target_node, attr_dict=attribute_dict)


class DefaultNetworkXFactory(NetworkXFactory):
    """

    Converts :class:`NiceCXNetwork` to :class:`networkx.Graph`
    object or one of its subtypes

    For details on implementation see :func:`~get_graph`
    """

    def __init__(self, legacymode=False):
        """
        Constructor


        Note: the parameters in the constructor change behavior of
        :py:func:`~DefaultNetworkXFactory.get_graph`

        :param legacymode: If set to True then
                           :py:func:`~DefaultNetworkXFactory.get_graph`
                           behaves like NDEx2 Python client version 3.1 and earlier in that
                           this method returns a :class:`networkx.Graph` object.
                           see :py:func:`~DefaultNetworkXFactory.get_graph` for more
                           information
        :type legacymode: bool
        :raises NDExError: If invalid value is set in `legacymode` parameter
        """
        super(DefaultNetworkXFactory, self).__init__()
        if legacymode is None:
            legacymode = False

        if not isinstance(legacymode, bool):
            raise NDExError(str(legacymode) +
                            ' not a valid value for legacymode parameter')

        self._legacymode = legacymode

    def get_graph(self, nice_cx_network, networkx_graph=None):
        """
        Creates a :class:`networkx.Graph`, or a subtype,
        object from `nice_cx_network` passed in.

        .. warning::

            Converting large networks (10,000+ edges or nodes) may take a
            long time and consume lots of memory.

        The conversion is done as follows:

        Any network attributes are copied to the :class:`networkx.Graph`
        in manner described here:
        :py:func:`~NetworkXFactory.add_network_attributes_from_nice_cx_network`

        For nodes:

        All nodes are added with the node id set to the id or
        :py:const:`~ndex2.constants.NODE_ID` of input network nodes.

        A node attribute named 'name' is set for each node with its
        value set to the value of the 'name' attribute from the input
        network.

        If 'r' exists on node, the value is added as a node attribute
        named 'represents' (unless `legacymode` is set to `True` in
        constructor)

        All other node attributes are added using the same attribute
        name as found in the input network. The value is directly set
        as it was found in input network (could be single object or list)

        For edges:

        Each edge is added setting the source to the value of
        :py:const:`~ndex2.constants.EDGE_SOURCE` attribute
        and target set as :py:const:`~ndex2.constants.EDGE_TARGET`
        attribute of input network.

        Any edge attributes named :py:const:`~ndex2.constants.EDGE_INTERACTION`
        are renamed 'interaction' and stored as an attribute for the edge

        .. versionchanged:: 3.5.0
            If the value of an edge attribute is a list then the value
            is set directly in the graph as is as opposed to being converted
            into a comma delimited string

        Coordinates are copied in manner described here:
        :py:func:`~NetworkXFactory.copy_cartesian_coords_into_graph`

        .. warning::

            If **legacymode** is set to True in constructor then:

            * :class:`networkx.Graph` created by this method does **NOT** support multiple edges between the same nodes. Extra edges encountered are **ignored** and not converted.

            * In addition, the 'r' attribute in the node dict is **NOT** copied to the resulting :class:`networkx.Graph` object.

            * `networkx_graph` parameter is ignored

        :param nice_cx_network: Network to extract graph from
        :type nice_cx_network: :class:`NiceCXNetwork`
        :param networkx_graph: Empty networkx graph to populate which is **IGNORED** if
                               `legacymode` is set to True in constructor. If unset
                               and `legacymode` is False in constructor then
                               a :class:`networkx.MultiDiGraph` is created
        :type networkx_graph: :class:`networkx.Graph` or subtype
        :raises NDExError: if input network is None
        :return: Input network converted to networkx Graph
        :rtype: :class:`networkx.Graph` if legacymode is set to True in constructor
                otherwise :class:`networkx.MultiDiGraph` unless `networkx_graph` is set in
                which case `networkx_graph` is returned
        """
        if nice_cx_network is None:
            raise NDExError('input network is None')

        if self._legacymode is True:
            g = nx.Graph()
        else:
            if networkx_graph is None:
                g = nx.MultiDiGraph()
            else:
                g = networkx_graph

        self.add_network_attributes_from_nice_cx_network(nice_cx_network,
                                                         g)
        self._process_nodes(nice_cx_network, g)
        self._process_edges(nice_cx_network, g)
        self.copy_cartesian_coords_into_graph(nice_cx_network,
                                              g)
        return g

    def _process_nodes(self, nice_cx_network, graph):
        """
        Iterates through the nodes adding them to the graph object
        using :func:`networkx.Graph.add_node()` setting name of node
        to node id and 'name' attribute to the value of the node
        attribute 'name'. This has a couple problems, one if the
        attribute value is a list that list is directly set in the
        Graph() object.
        :return:
        """
        represents = None
        for k, v in nice_cx_network.get_nodes():
            if self._legacymode is False:
                represents = v.get(constants.NODE_REPRESENTS)

            self.add_node(graph, k,
                          nice_cx_network.get_node_attributes(k),
                          name=v.get(constants.NODE_ATTR_NAME),
                          represents=represents)

    def _process_edges(self, nice_cx_network, graph):
        """
        Adds edges by calling :func:`networkx.Graph().add_edge()` setting
        source to the 's' attribute on the
        :param graph: Graph to add edges to
        :type graph: :class:`networkx.Graph`
        :return:
        """
        for k, v in nice_cx_network.get_edges():
            e_a = nice_cx_network.get_edge_attributes(k)
            add_this_dict = {}
            add_this_dict['interaction'] = v.get(constants.EDGE_INTERACTION)
            if e_a is not None:
                for e_a_item in e_a:
                    add_this_dict[e_a_item.get('n')] = e_a_item.get('v')

            self.add_edge(graph, v[constants.EDGE_SOURCE],
                          v[constants.EDGE_TARGET],
                          add_this_dict)


class LegacyNetworkXVersionTwoPlusFactory(NetworkXFactory):
    """
    .. deprecated:: 3.2.0

            This implementation contains errors, but is left for backwards
            compatibility of :func:`NiceCXNetwork.to_networkx`

    Converts :class:`NiceCXNetwork` to :class:`networkx.Graph`
    object following logic in legacy NDEx2 Python client when networkx 2.0+
    is installed.

    .. warning:: This implementation assumes networkx 2.0+ is installed and will fail with older versions.

    For conversion details see :func:`~LegacyNetworkXVersionTwoPlusFactory.get_graph`
    """
    def __init__(self):
        """
        Constructor

        """
        super(LegacyNetworkXVersionTwoPlusFactory, self).__init__()

    def get_graph(self, nice_cx_network, networkx_graph=None):
        """
        Creates a :class:`networkx.Graph` object from `nice_cx_network`
        passed in.

        .. deprecated:: 3.2.0

            This implementation contains errors, but is left for backwards
            compatibility of :func:`NiceCXNetwork.to_networkx`

        .. warning::

            Converting large networks (10,000+ edges or nodes) may take a
            long time and consume lots of memory.

            This implementation uses node name as ID for nodes, which is
            problematic if multiple nodes share the same name and
            results in invalid mapping of node positions

            :class:`networkx.Graph` created by this method does NOT support
            multiple edges between the same nodes. Extra edges encountered
            are **ignored** and not converted.

        The conversion is done as follows:

        Any network attributes are copied to the :class:`networkx.Graph`
        in manner described here:
        :py:func:`~NetworkXFactory.add_network_attributes_from_nice_cx_network`

        For nodes:

        All nodes are added with the node id set to value of 'n' on
        node. For multiple nodes with same 'n' value behavior is unknown

        A node attribute named 'name' is set for each node with its
        value set to the value of the 'name' attribute from the input
        network.

        If 'r' exists on node, the value is added as a node attribute
        named 'represents'

        All other node attributes are added using the same attribute
        name as found in the input network. The value is directly set
        name as found in the input network. The value is directly set
        as it was found in input network (could be single object or list)


        For edges:

        Each edge is added setting the source to the value of 's' attribute
        and target set as 't' attribute of input network.

        Any edge attributes named 'i' are renamed 'interaction' and
        stored as an attribute for the edge

        If the value of an edge attribute is a list then the list values
        are turned into a string separated by a comma and then enclosed
        by double quotes.

        Coordinates are copied in manner described here:
        :py:func:`~NetworkXFactory.copy_cartesian_coords_into_graph`

        :param nice_cx_network: Network to extract graph from
        :type nice_cx_network: :class:`NiceCXNetwork`
        :param networkx_graph: ignored by this implementation
        :type networkx_graph: :class:`networkx.Graph` or subtype
        :return: Input network converted to networkx Graph
        :rtype: :class:`networkx.Graph`
        """
        g = nx.Graph()
        self.add_network_attributes_from_nice_cx_network(nice_cx_network,
                                                         g)
        self._process_nodes(nice_cx_network, g)
        self._process_edges(nice_cx_network, g)
        self.copy_cartesian_coords_into_graph(nice_cx_network,
                                              g)
        return g

    def _process_nodes(self, nice_cx_network, graph):
        """
        Processes the nodes
        :return:
        """
        for k, v in nice_cx_network.get_nodes():
            node_name = v.get('n')
            graph.add_node(v.get('n'))
            n_a = nice_cx_network.get_node_attributes(k)
            if n_a:
                for na_item in n_a:
                    graph.nodes[node_name][na_item.get('n')] = na_item.get('v')

            if v.get('r'):
                graph.nodes[node_name]['represents'] = v.get('r')

    def _process_edges(self, nice_cx_network, graph):
        """
        Process edges
        :param graph:
        :return:
        """
        for k, v in nice_cx_network.get_edges():

            source_node = nice_cx_network.get_node(v.get('s')).get('n')
            target_node = nice_cx_network.get_node(v.get('t')).get('n')

            graph.add_edge(source_node, target_node)
            e_a = nice_cx_network.get_edge_attributes(k)
            graph[source_node][target_node]['interaction'] = v.get('i')
            if e_a is not None:
                for e_a_item in e_a:
                    if isinstance(e_a_item.get('v'), list):
                        graph[source_node][target_node][e_a_item.get('n')] = '"%s"' % ','.join(
                            str(e) for e in e_a_item.get('v'))
                    else:
                        graph[source_node][target_node][e_a_item.get('n')] = e_a_item.get('v')
