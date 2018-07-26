__author__ = 'aarongary'

import json
import sys
import os
import errno
import pandas as pd
import networkx as nx
import io
import decimal
import numpy as np
import math
import json
import ijson
import requests
import base64
from ndex2cx import known_aspects_min
from ndex2.niceCxInterface import NiceCx

if sys.version_info.major == 3:
    from urllib.request import urlopen, Request, HTTPBasicAuthHandler, HTTPPasswordMgrWithDefaultRealm, \
        build_opener, install_opener, HTTPError, URLError
else:
    from urllib2 import urlopen, Request, HTTPBasicAuthHandler, HTTPPasswordMgrWithDefaultRealm, \
        build_opener, install_opener, HTTPError, URLError

userAgent = 'NiceCX-Python/1.0'

class NiceCXNetwork(NiceCx):
    def __init__(self, cx=None, server=None, username=None, password=None, uuid=None, networkx_G=None, pandas_df=None, filename=None, data=None, **attr):

        self.metadata = {}
        self.context = []
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

        if cx:
            self.create_from_cx(cx)
        elif networkx_G:
            self.create_from_networkx(networkx_G)
        elif pandas_df is not None:
            self.create_from_pandas(pandas_df)
        elif filename is not None:
            if os.path.isfile(filename):
                with open(filename, 'rU') as file_cx:
                    #====================================
                    # BUILD NICECX FROM FILE
                    #====================================
                    self.create_from_cx(json.load(file_cx))
            else:
                raise Exception('Input provided is not a valid file')
        else:
            if server and uuid:
                self.create_from_server(server, username, password, uuid)

    def __create_edge(self, id=None, edge_source=None, edge_target=None, edge_interaction=None, cx_fragment=None):
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

        self.add_edge(id=id, source=edge_source, target=edge_target, interaction=edge_interaction)
        #edge_element = EdgeElement(id=id, edge_source=edge_source, edge_target=edge_target, edge_interaction=edge_interaction, cx_fragment=cx_fragment)

        #self.add_edge(edge_element)

        return id

    def create_edge(self, edge_source=None, edge_target=None, edge_interaction=None, cx_fragment=None):
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
        edge_id = self.edge_int_id_generator

        self.add_edge(id=edge_id, source=edge_source, target=edge_target, interaction=edge_interaction)
        self.edge_int_id_generator += 1

        return edge_id

    def add_network_attribute(self, name=None, values=None, type=None, subnetwork=None):
        found_attr = False
        for n_a in self.networkAttributes:
            if n_a.get('n') == name:
                n_a['v'] = values

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

    # TODO
    # make opaque aspect into a one shot method to set the whole aspect.
    # i.e. not one element at a time
    def add_opaque_aspect(self, aspect_name, aspect):
        if isinstance(aspect, list):
            aspect_element = {aspect_name: aspect}
            self.add_opaque_aspect_element(aspect_element)
            #self.add_metadata_stub(aspect_name)
        else:
            raise Exception('Provided input was not of type list.')

    def add_opaque_aspect_element(self, opaque_element):
        raise Exception('add_opaque_aspect_element() is deprecated.  Please use add_opaque_aspect()')

    def set_name(self, network_name):
        """
        Set the network name
        :param network_name: Network name
        :type network_name: string
        :return: None
        :rtype:none
        """
        #add_this_network_attribute = NetworkAttributesElement(name='name', values=network_name, type=ATTRIBUTE_DATA_TYPE.STRING)

        self.add_network_attribute(name='name', values=network_name, type='string')

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
        self.context.append({prefix: uri})

    def set_namespaces(self,ns ):
        self.context = ns

    def get_namespaces(self,):
        return self.context

    def get_edges (self):
        """
        Returns an iterator over edge ids as keys and edge objects as values.
        :return: Edge iterator
        :rtype: iterator
        """
        return self.edges.items()

    def get_edge(self, edge):
        return self.edges.get(edge)

    def get_edge_attribute_object(self, edge, attribute_name):
        edge_attrs = self.edgeAttributes.get(edge)

        if edge_attrs:
            for e_a in edge_attrs:
                if e_a.get('n') == attribute_name:
                    return e_a

        return None

    #==============================
    # NETWORK PROPERTY OPERATIONS
    #==============================
    def get_network_attribute(self, attribute_name):
        """
        Get the value of a network attribute
        :param attribute_name: Attribute name
        :type attribute_name: string
        :return: Network attribute object
        :rtype: nicecxModel.cx.aspects.NetworkAttributesElement
        """
        for n_a in self.networkAttributes:
            if n_a.get('n') == attribute_name:
                return n_a

        return None

    #==================
    # NODE OPERATIONS
    #==================
    def create_node(self, id=None, node_name=None, node_represents=None, cx_fragment=None):
        if id is None:
            id=self.get_next_node_id()

        self.add_node(id=id, name=node_name, represents=node_represents)

        return id

    def add_node(self, id=None, name=None, represents=None, data_type=None):
        """
        Add a node object to the network. (For an easier method for adding nodes use create_node() )

        :param id:
        :type id:
        :param name:
        :type name:
        :param represents:
        :type represents:
        :param data_type:
        :type data_type:
        :return:
        :rtype:
        """

        """
        :param node_element: A node object
        :type node_element: nicecxModel.cx.aspects.NodesElement
        :return: Node ID
        :rtype: int
        """
        if represents is not None:
            self.nodes[id] = {'@id': id, 'n': name, 'r': represents}
        else:
            self.nodes[id] = {'@id': id, 'n': name, 'r': name}

        if data_type is not None:
            self.nodes[id]['d'] = data_type

        return id

    def get_next_node_id(self):
        return_id = self.node_int_id_generator
        self.node_int_id_generator += 1
        return return_id

    def add_node_attribute(self, property_of=None, name=None, values=None, type=None, subnetwork=None):
        if property_of is None:
            raise Exception('Node attribute requires the property_of property')

        if name is None or values is None:
            raise Exception('Node attribute requires the name and values property')

        if self.nodeAttributes.get(property_of) is None :
            self.nodeAttributes[property_of] = []

        if type is None:
            self.nodeAttributes[property_of].append({'po': property_of, 'n': name, 'v': values})
        else:
            self.nodeAttributes[property_of].append({'po': property_of, 'n': name, 'v': values, 'd': type})

    def add_edge(self, id=None, source=None, target=None, interaction=None):
        """
        Add an edge object to the network.

        :param id: internal identifier
        :type id: int
        :param source: id of source node
        :type source: int
        :param target: id of target node
        :type target: int
        :param interaction: type of edge interaction
        :type interaction: string
        :return: edge id
        :rtype: int
        """
        if id is None:
            raise Exception('No ID provided')

        if source is None or target is None or interaction is None:
            print('source: %s, target: %s or target: %s was None.  Skipping edge' % (source, target, interaction))
            return None
            #raise Exception('Source, Target and Interaction are required to create an edge')

        self.edges[id] = {'@id': id, 's': source, 't': target, 'i': interaction}

        return id

    def add_edge_attribute(self, property_of=None, name=None, values=None, type=None, subnetwork=None):
        if isinstance(property_of, dict):
            property_of = property_of.get('@id')
        if property_of is None:
            raise Exception('Edge attribute requires the property_of property')

        if name is None or values is None:
            raise Exception('Edge attribute requires the name and values property')

        if self.edgeAttributes.get(property_of) is None :
            self.edgeAttributes[property_of] = []

        if type is None:
            self.edgeAttributes[property_of].append({'po': property_of, 'n': name, 'v': values})
        else:
            self.edgeAttributes[property_of].append({'po': property_of, 'n': name, 'v': values, 'd': type})

    def get_nodes(self):
        """
        Returns an iterator over node ids as keys and node objects as values.
        :return: iterator over nodes
        :rtype: iterator
        """
        return self.nodes.items()

    def get_node(self, node_id):
        return self.nodes.get(node_id)

    # TODO - Check edges for orphans.  Check node attributes for orphans
    #def remove_node(self, node_id):
    #    raise Warning()
    #    return self.nodes.pop(node_id, None)

    #=============================
    # NODE ATTRIBUTES OPERATIONS
    #=============================
    def set_node_attribute(self, node, attribute_name, values, type=None, subnetwork=None, cx_fragment=None):
        """
        Set the value(s) of an attribute of a node, where the node may be specified by its id or passed in as an object.
        :param node: node object or node id
        :type node: nicecxModel.cx.aspects.NodesElement or int
        :param attribute_name: attribute name
        :type attribute_name: string
        :param values: A value or list of values of the attribute
        :type values: list, string, int or float
        :param type: the datatype of the attribute values, defaults to the python datatype of the values.
        :type type: nicecxModel.cx.aspects.ATTRIBUTE_DATA_TYPE
        :param subnetwork: the id of the subnetwork to which this attribute applies.
        :type subnetwork: int or string
        :param cx_fragment: CX fragment
        :type cx_fragment: json
        :return: none
        :rtype:
        """

        self.add_node_attribute(property_of=node, name=attribute_name, values=values, type=type)

    def get_node_attribute_objects(self, node, attribute_name):
        """
        Get the attribute objects for a node attribute name, where the node may be specified by its id or passed in
        as an object. The node attribute objects include datatype and subnetwork information. An example of networks
        that include subnetworks are Cytoscape collections stored in NDEx.
        :param node: node object or node id
        :type node: nicecxModel.cx.aspects.NodesElement or int
        :param attribute_name: attribute name
        :type attribute_name: string
        :return:
        :rtype:
        """
        node_attrs = self.get_node_attributes(node)

        if node_attrs:
            for n_a in node_attrs:
                if n_a.get('n') == attribute_name:
                    return n_a

        return None

    def get_node_attribute(self, node, attribute_name):
        """
        Get the value(s) of an attribute of a node, where the node may be specified by its id or passed in as an object.
        :param node: node object or node id
        :type node: nicecxModel.cx.aspects.NodesElement or int
        :param attribute_name: attribute name
        :type attribute_name:
        :return: string
        :rtype:
        """
        n_a = self.get_node_attribute_objects(node, attribute_name)
        if n_a:
            return n_a.get('v')
        else:
            return None

    def get_node_attributes(self, node):
        """
        Get the attribute objects of a node, where the node may be specified by its id or passed in as an object.
        :param node: node object or node id
        :type node: nicecxModel.cx.aspects.NodesElement or int
        :return:
        :rtype:
        """
        return self.nodeAttributes.get(node.get('@id'))



    def set_network_attribute(self, name=None, values=None, type=None, subnetwork=None, cx_fragment=None):
        """
        Set an attribute of the network

        :param name: Attribute name
        :type name: string
        :param values: The values of the attribute
        :type values: list, string, float or int
        :param type: The datatype of the attribute values
        :type type: cx.aspects.ATTRIBUTE_DATA_TYPE
        :param subnetwork: The id of the subnetwork (if any) to which this attribute applies.
        :type subnetwork: int
        :param cx_fragment: CX fragment
        :type cx_fragment: json
        :return: None
        :rtype: none
        """

        found_attr = False
        for n_a in self.networkAttributes:
            if n_a.get('n') == name:
                n_a['v'] = values
                if type is not None:
                    n_a['d'] = type

                if subnetwork:
                    n_a['s'] = subnetwork

                found_attr = True

                break

        if not found_attr:
            if type is not None:
                net_attr = {
                    'n': name,
                    'v': values,
                    'd': type
                }
            else:
                net_attr = {
                    'n': name,
                    'v': values
                }

            self.networkAttributes.append(net_attr)


    #==================================
    # EDGE ATTRIBUTE OPERATIONS
    #==================================
    def set_edge_attribute(self, edge, attribute_name, values, type=None, subnetwork=None, cx_fragment=None):
        """
        Set the value(s) of attribute of an edge, where the edge may be specified by its id or passed in an object.
        :param edge:
        :type edge:
        :param attribute_name: Attribute name
        :type attribute_name:
        :param values: The values of the attribute
        :type values:
        :param type: The datatype of the attribute values, defaults to the python datatype of the values.
        :type type: nicecxModel.cx.aspects.ATTRIBUTE_DATA_TYPE
        :param subnetwork: The id of the subnetwork to which this attribute applies.
        :type subnetwork: string or int
        :param cx_fragment: CX Fragment (optional)
        :type cx_fragment: json
        :return: none
        :rtype:
        """

        self.add_edge_attribute(property_of=edge, name=attribute_name, values=values, type=type)

    def get_edge_attributes(self, edge):
        """
        Get the attribute objects of an edge, where the edge may be specified by its id or passed in as an object.
        :param edge: Edge object or edge id
        :type edge: nicecxModel.cx.aspects.EdgeElement or int
        :return: Edge attribute objects
        :rtype: list of nicecxModel.cx.aspects.EdgeAttributesElement
        """
        return self.edgeAttributes.get(edge)

    def get_edge_attribute_objects(self, edge, attribute_name):
        """
        Get the attribute objects for an edge attribute name, where the edge may be specified by its id or passed in
        as an object. The edge attribute objects include datatype and subnetwork information. An example of networks
        that include subnetworks are Cytoscape collections stored in NDEx.
        :param edge: Edge object or edge id
        :type edge: nicecxModel.cx.aspects.EdgesElement or int
        :param attribute_name: Attribute name
        :type attribute_name:
        :return: Edge attribute object
        :rtype: nicecxModel.cx.aspects.EdgesAttributesElement
        """
        edge_attrs = self.get_edge_attributes(edge)

        if edge_attrs:
            for e_a in edge_attrs:
                if e_a.get('n') == attribute_name:
                    return e_a

        return None

    # TODO - return the element as the appropriate type (cast)
    def get_edge_attribute(self, edge, attribute_name, subnetwork=None):
        """
        Get the value(s) of an attribute of an edge, where the edge may be specified by its id or passed in as an object.
        :param edge: Edge object or edge id
        :type edge: nicecxModel.cx.aspects.EdgesElement or int
        :param attribute_name: Attribute name
        :type attribute_name:
        :param subnetwork: The id of the subnetwork (if any) to which this attribute was applied.
        :type subnetwork: int
        :return: Edge attribute value(s)
        :rtype: list, string, int or float
        """
        edge_attr = self.get_edge_attribute_object(edge, attribute_name)
        if edge_attr:
            return edge_attr.get('v'), edge_attr.get('d')
        else:
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
        Get the @context aspect of the network, the aspect that maps namespace prefixes to their defining URIs
        :return: List of context objects
        :rtype: list of json objects
        """
        return self.context

    def set_context(self, context):
        """
        Set the @context aspect of the network, the aspect that maps namespace prefixes to their defining URIs
        :param context: List of context objects
        :type context: List of dict (namespace string: URI)
        :return: None
        :rtype: none
        """
        print('context is of type %s' % type(context))
        if isinstance(context, list):
            print('Setting context from list')
            self.context = context
        elif isinstance(context, dict):
            print('Setting context from dict')
            self.context = [context]
        else:
            raise Exception('Context provided is not of type list')

    def get_metadata(self):
        """
        Get the network metadata
        :return: Network metadata
        :rtype: Iterator of nicecxModel.metadata.MetaDataElement
        """
        return self.metadata.items()

    def set_metadata(self, metadata_obj):
        """
        Set the network metadata
        :param metadata_obj: Dict of metadata objects
        :type metadata_obj: dict of nicecxModel.metadata.MetaDataElement
        :return: None
        :rtype: none
        """
        if isinstance(metadata_obj, dict):
            self.metadata = metadata_obj
        else:
            raise Exception('Set metadata input was not of type <dict>')

    def add_metadata(self, md):
        raise Exception('add_metadata() is deprecated')

    def getProvenance(self):
        """
        Get the network provenance as a Python dictionary having the CX provenance schema.
        :return: List of provenance
        :rtype: list of json objects
        """

        return self.provenance

    def set_provenance(self, provenance):
        if isinstance(provenance, list):
            self.provenance = provenance
        else:
            raise Exception('Provided provenance was not of type <list>')

    def get_opaque_aspect_table(self):
        return self.opaqueAspects

    def get_opaque_aspect(self, aspect_name):
        """
        Get the elements of the aspect specified by aspect_name
        :param aspect_name: the name of the aspect to retrieve.
        :type aspect_name: string
        :return: Opaque aspect
        :rtype: nicecxModel.cx.aspects.AspectElement
        """
        return self.opaqueAspects.get(aspect_name)

    def set_opaque_aspect(self, aspect_name, aspect_elements):
        """
        Set the aspect specified by aspect_name to the list of aspect elements. If aspect_elements is None, the
        aspect is removed.
        :param aspect_name: Name of the aspect
        :type aspect_name: string
        :param aspect_elements: Aspect element
        :type aspect_elements: nicecxModel.cx.aspects.AspectElement
        :return: None
        :rtype: none
        """
        if aspect_elements is None:
            self.opaqueAspects.pop(aspect_name, None)
        else:
            if isinstance(aspect_elements, list):
                self.opaqueAspects[aspect_name] = aspect_elements
            else:
                if aspect_name is None:
                    aspect_name = 'unknown'
                raise Exception('Provided aspect for ' + aspect_name + ' is not of type <list>')

    def get_opaque_aspect_names(self):
        """
        Get the names of all opaque aspects
        :return: List of opaque aspect names
        :rtype: list of strings
        """
        return self.opaqueAspects.keys()

    # TODO - determine if this is useful
    def get_edge_attribute_element(self, edge, attr_name):
        attrs =  self.edgeAttributes.get(edge.get_id())
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

    def set_provenance(self, provenance):
        """
        Set the network provenance
        :param provenance: List of provenance objects
        :type provenance: list
        :return: None
        :rtype: none
        """
        self.provenance = provenance

    def get_edge_citations(self):
        return self.edgeCitations

    def get_node_citations(self):
        return self.nodeCitations

    def apply_template(self, server, uuid, username=None, password=None):
        """
        Get a network from NDEx, copy its cytoscapeVisualProperties aspect to this network.
        :param server: server host name (i.e. public.ndexbio.org)
        :type server: string
        :param username: username (optional - used when accessing private networks)
        :type username: string
        :param password: password (optional - used when accessing private networks)
        :type password:  string
        :param uuid: uuid of the styled network
        :type uuid: string
        :return: None
        :rtype: none
        """
        error_message = []
        if not server:
            error_message.append('server')
        if not uuid:
            error_message.append('uuid')

        if server and uuid:
            #===================
            # METADATA
            #===================
            available_aspects = []
            for ae in (o for o in self.get_aspect(uuid, 'metaData', server, username, password)):
                available_aspects.append(ae.get('name'))

            #=======================
            # ADD VISUAL PROPERTIES
            #=======================
            for oa in available_aspects:
                if 'visualProperties' in oa:
                    objects = self.get_aspect(uuid, 'visualProperties', server, username, password)
                    obj_items = (o for o in objects)
                    for oa_item in obj_items:
                        aspectElmts = self.opaqueAspects.get(oa)
                        if aspectElmts is None:
                            aspectElmts = []
                            self.opaqueAspects[oa] = aspectElmts

                        aspectElmts.append(oa_item)

                        #aspect_element = AspectElement(oa_item, oa)
                        #self.add_opaque_aspect_element(aspect_element)
                    #vis_prop_size = len(self.opaqueAspects.get('visualProperties'))
                    #mde = MetaDataElement(elementCount=vis_prop_size, version=1, consistencyGroup=1, name='visualProperties')

                    mde = {
                        'name': 'visualProperties',
                        'elementCount': len(aspectElmts),
                        'version': "1.0",
                        'consistencyGroup': 1,
                        'properties': []
                    }
                    self.metadata['visualProperties'] = mde

                    #self.add_metadata(mde)


                if 'cyVisualProperties' in oa:
                    objects = self.get_aspect(uuid, 'cyVisualProperties', server, username, password)
                    obj_items = (o for o in objects)
                    for oa_item in obj_items:
                        aspectElmts = self.opaqueAspects.get(oa)
                        if aspectElmts is None:
                            aspectElmts = []
                            self.opaqueAspects[oa] = aspectElmts

                        aspectElmts.append(oa_item)

                    mde = {
                              'name': 'cyVisualProperties',
                              'elementCount': len(aspectElmts),
                              'version': "1.0",
                              'consistencyGroup': 1,
                              'properties': []
                          }
                    self.metadata['cyVisualProperties'] = mde

                        #aspect_element = AspectElement(oa_item, oa)
                        #self.add_opaque_aspect_element(aspect_element)
                    #vis_prop_size = len(self.opaqueAspects.get('cyVisualProperties'))
                    #mde = MetaDataElement(elementCount=vis_prop_size, version=1, consistencyGroup=1, name='cyVisualProperties')
                    #self.add_metadata(mde)
        else:
            raise Exception(', '.join(error_message) + 'not specified in apply_template')

    def merge_node_attributes(self, source_attribute1, source_attribute2, target_attribute):
        """
        Checks 2 attribute fields for values and merges them into one attribute.  The best use is when one attribute
        is empty which occurs when loading from an edge file.  Use with caution
        :param source_attribute1: The name of the first attribute
        :type source_attribute1: basestring
        :param source_attribute2: The name of the second attribute
        :type source_attribute2: basestring
        :param target_attribute: The desired name for the merged data
        :type target_attribute: basestring
        :return:
        :rtype:
        """
        for node_id, node in self.nodes.items():
            value1 = self.get_node_attribute(node, source_attribute1)
            value2 = self.get_node_attribute(node, source_attribute2)
            merged_value = value1 or value2
            if merged_value:
                self.set_node_attribute(node, target_attribute, merged_value)
                self.remove_node_attribute(node, source_attribute1)
                self.remove_node_attribute(node, source_attribute2)

    def create_from_pandas(self, df, source_field=None, target_field=None, source_node_attr=[], target_node_attr=[], edge_attr=[], edge_interaction=None):
        raise Exception('create_from_pandas() is no longer supported in NiceCXNetwork.  Please use ndex2.create_nice_cx_from_pandas()')

    def create_from_networkx(self, G):
        raise Exception('create_from_networkx() is no longer supported in NiceCXNetwork.  Please use ndex2.create_nice_cx_from_networkx()')

    def create_from_server(self, server, username, password, uuid):
        raise Exception('create_from_server() is no longer supported in NiceCXNetwork.  Please use ndex2.create_nice_cx_from_server()')

    def create_from_cx(self, cx):
        raise Exception('create_from_cx() is no longer supported in NiceCXNetwork.  Please use ndex2.create_nice_cx_from_cx()')

    def get_frag_from_list_by_key(self, cx, key):
        for aspect in cx:
            if key in aspect:
                return aspect[key]

        return []

    def to_pandas_dataframe(self):
        """
        Export the network as a Pandas DataFrame.

        Note: This method only processed nodes, edges, node attributes and edge attributes, but not network attributes
        or other aspects

        :return: Pandas dataframe
        :rtype: Pandas dataframe
        """
        rows = []
        edge_items = None
        if sys.version_info.major == 3:
            edge_items = self.edges.items()
        else:
            edge_items = self.edges.iteritems()

        for k, v in edge_items:
            e_a = self.edgeAttributes.get(k)
            #==========================
            # PROCESS EDGE ATTRIBUTES
            #==========================
            add_this_dict = {}
            if e_a is not None:
                for e_a_item in e_a:
                    if isinstance(e_a_item.get('v'), list):
                        add_this_dict[e_a_item.get('n')] = ','.join(str(e) for e in e_a_item.get('v'))
                        add_this_dict[e_a_item.get('n')] = '"' + add_this_dict[e_a_item.get('n')] + '"'
                    else:
                        add_this_dict[e_a_item.get('n')] = e_a_item.get('v')
            #================================
            # PROCESS SOURCE NODE ATTRIBUTES
            #================================
            s_a = self.nodeAttributes.get(v.get('s'))
            if s_a is not None:
                for s_a_item in s_a:
                    if isinstance(s_a_item.get('v'), list):
                        add_this_dict['source_' + s_a_item.get('n')] = ','.join(str(e) for e in s_a_item.get('v'))
                        add_this_dict['source_' + s_a_item.get('n')] = '"' + add_this_dict['source_' + s_a_item.get('n')] + '"'
                    else:
                        add_this_dict['source_' + s_a_item.get('n')] = s_a_item.get('v')

            #================================
            # PROCESS TARGET NODE ATTRIBUTES
            #================================
            t_a = self.nodeAttributes.get(v.get('t'))
            if t_a is not None:
                for t_a_item in t_a:
                    if isinstance(t_a_item.get('v'), list):
                        add_this_dict['target_' + t_a_item.get('n')] = ','.join(str(e) for e in t_a_item.get('v'))
                        add_this_dict['target_' + t_a_item.get('n')] = '"' + add_this_dict['target_' + t_a_item.get('n')] + '"'
                    else:
                        add_this_dict['target_' + t_a_item.get('n')] = t_a_item.get('v')

            if add_this_dict:
                rows.append(dict(add_this_dict, source=self.nodes.get(v.get('s')).get('n'), target=self.nodes.get(v.get('t')).get('n'), interaction=v.get('i')))
            else:
                rows.append(dict(source=self.nodes.get(v.get('s')).get('n'), target=self.nodes.get(v.get('t')).get('n'), interaction=v.get('i')))

        nodeAttributeSourceTarget = []
        for n_a in self.nodeAttributeHeader:
            nodeAttributeSourceTarget.append('source_' + n_a)
            nodeAttributeSourceTarget.append('target_' + n_a)

        df_columns = ['source', 'interaction', 'target'] + list(self.edgeAttributeHeader) + nodeAttributeSourceTarget

        return_df = pd.DataFrame(rows, columns=df_columns)

        return return_df

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

    def upload_to(self, server, username, password):
        """
        Upload this network to the specified server to the account specified by username and password.
        Example:
            ndexGraph.upload_to('http://test.ndexbio.org', 'myusername', 'mypassword')
        :param server: The NDEx server to upload the network to.
        :type server: string
        :param username: The username of the account to store the network.
        :type username: string
        :param password: The password for the account.
        :type password: string
        :return: The UUID of the network on NDEx.
        :rtype: string
        """
        if server and 'http' not in server:
            server = 'http://' + server

        ndex = nc.Ndex2(server,username,password)

        return ndex.save_new_network(self.to_cx())

    def upload_new_network_stream(self, server, username, password):
        raise Exception('upload_new_network_stream() is no longer supported.  Please use upload_to()')

    def update_to(self, uuid, server, username, password):
        """ Upload this network to the specified server to the account specified by username and password.

        :param server: The NDEx server to upload the network to.
        :type server: str
        :param username: The username of the account to store the network.
        :type username: str
        :param password: The password for the account.
        :type password: str
        :return: The UUID of the network on NDEx.
        :rtype: str

        Example:
            ndexGraph.upload_to('http://test.ndexbio.org', 'myusername', 'mypassword')
        """
        cx = self.to_cx()
        ndex = nc.Ndex2(server,username,password)

        if(len(cx) > 0):
            if(cx[len(cx) - 1] is not None):
                if(cx[len(cx) - 1].get('status') is None):
                    # No STATUS element in the array.  Append a new status
                    cx.append({"status" : [ {"error" : "","success" : True} ]})
                else:
                    if(len(cx[len(cx) - 1].get('status')) < 1):
                        # STATUS element found, but the status was empty
                        cx[len(cx) - 1].get('status').append({"error" : "","success" : True})

            if sys.version_info.major == 3:
                stream = io.BytesIO(json.dumps(cx).encode('utf-8'))
            else:
                stream = io.BytesIO(json.dumps(cx))

            return ndex.update_cx_network(stream, uuid)
        else:
            raise IndexError("Cannot save empty CX.  Please provide a non-empty CX document.")

    def to_networkx(self):
        """
        Return a NetworkX graph based on the network. Elements in the CartesianCoordinates aspect of the network are transformed to the NetworkX pos attribute.
        :return: Networkx graph
        :rtype: networkx Graph()
        """
        G = nx.Graph()

        if sys.version_info.major == 3:
            node_items = self.nodes.items()
            edge_items = self.edges.items()
        else:
            node_items = self.nodes.iteritems()
            edge_items = self.edges.iteritems()

        #============================
        # PROCESS NETWORK ATTRIBUTES
        #============================
        for net_a in self.networkAttributes:
            G.graph[net_a.get('n')] = net_a.get('v')

        #================================
        # PROCESS NODE & NODE ATTRIBUTES
        #================================
        for k, v in node_items:
            node_attrs = {}
            n_a = self.nodeAttributes.get(k)
            if n_a:
                for na_item in n_a:
                    node_attrs[na_item.get('n')] = na_item.get('v')

            G.add_node(k, node_attrs, name=v.get('n'))

        #================================
        # PROCESS EDGE & EDGE ATTRIBUTES
        #================================
        for k, v in edge_items:
            e_a = self.edgeAttributes.get(k)
            add_this_dict = {}
            add_this_dict['interaction'] = v.get('i')
            if e_a is not None:
                for e_a_item in e_a:
                    if isinstance(e_a_item.get('v'), list):
                        add_this_dict[e_a_item.get('n')] = ','.join(str(e) for e in e_a_item.get('v'))
                        add_this_dict[e_a_item.get('n')] = '"' + add_this_dict[e_a_item.get('n')] + '"'
                    else:
                        add_this_dict[e_a_item.get('n')] = e_a_item.get('v')

            G.add_edge(v.get('s'), v.get('t'), add_this_dict)

        #================
        # PROCESS LAYOUT
        #================
        cartesian_layout = self.opaqueAspects.get('cartesianLayout')
        if cartesian_layout:
            G.pos = {}
            for x_y_pos in cartesian_layout:
                G.pos[x_y_pos.get('node')] = (x_y_pos.get('x'), x_y_pos.get('y'))

        return G

    def get_summary(self):
        """
        Get a network summary
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

        return summary_string

    def __str__(self):
        return json.dumps(self.to_cx(), cls=DecimalEncoder)

    def to_cx(self):
        """
        Return the CX corresponding to the network.
        :return: CX representation of the network
        :rtype: CX (list of dict aspects)
        """
        output_cx = [{"numberVerification": [{"longNumber": 281474976710655}]}]

        #=====================================================
        # IF THE @ID IS NOT NUMERIC WE NEED TO CONVERT IT TO
        # INT BY USING THE INDEX OF THE NON-NUMERIC VALUE
        #=====================================================
        #if self.node_int_id_generator:
        #    self.node_id_lookup = list(self.node_int_id_generator)

        #if self.metadata:
            #output_cx.append(self.generate_aspect('metaData'))
        #    output_cx.append(self.generate_metadata_aspect())
        if self.context:
            output_cx.append(self.generate_aspect('@context'))
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

        #print json.dumps(output_cx)

        return output_cx

    def generate_aspect(self, aspect_name):
        core_aspect = ['nodes', 'edges','networkAttributes', 'nodeAttributes', 'edgeAttributes', 'metaData', '@context']
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

            consistency_group += 1 # bump the consistency group up by one

            for mi_k, mi_v in self.metadata.items():
                #print mi_k
                #print mi_v
                mi_v.set_consistency_group(consistency_group)

    def generate_metadata(self, G, unclassified_cx):
        #if self.metadata:
        #    for k, v in self.metadata.iteritems():


        return_metadata = []
        consistency_group = 1
        if(self.metadata_original is not None):
            for mi in self.metadata_original:
                if(mi.get("consistencyGroup") is not None):
                    if(mi.get("consistencyGroup") > consistency_group):
                        consistency_group = mi.get("consistencyGroup")
                else:
                    mi['consistencyGroup'] = 0

            consistency_group += 1 # bump the consistency group up by one

            #print("consistency group max: " + str(consistency_group))

        # ========================
        # @context metadata
        # ========================
        if self.context:
            return_metadata.append(
                {
                    "consistencyGroup": consistency_group,
                    "elementCount": 1,
                    "name": "@context",
                    "properties": [],
                    "version": "1.0"
                }
            )

        #========================
        # Nodes metadata
        #========================
        node_ids = [n[0] for n in G.nodes_iter(data=True)]
        if(len(node_ids) < 1):
            node_ids = [0]
        return_metadata.append(
            {
                "consistencyGroup" : consistency_group,
                "elementCount" : len(node_ids),
                "idCounter": max(node_ids),
                "name" : "nodes",
                "properties" : [ ],
                "version" : "1.0"
            }
        )

        #========================
        # Edges metadata
        #========================
        edge_ids = [e[2]for e in G.edges_iter(data=True, keys=True)]
        if(len(edge_ids) < 1):
            edge_ids = [0]
        return_metadata.append(
            {
                "consistencyGroup" : consistency_group,
                "elementCount" : len(edge_ids),
                "idCounter": max(edge_ids),
                "name" : "edges",
                "properties" : [ ],
                "version" : "1.0"
            }
        )

        #=============================
        # Network Attributes metadata
        #=============================
        if(len(G.graph) > 0):
            return_metadata.append(
                {
                    "consistencyGroup" : consistency_group,
                    "elementCount" : len(G.graph),
                    "name" : "networkAttributes",
                    "properties" : [ ],
                    "version" : "1.0"
                }
            )

        #===========================
        # Node Attributes metadata
        #===========================
        #id_max = 0
        attr_count = 0
        for node_id , attributes in G.nodes_iter(data=True):
            for attribute_name in attributes:
                if attribute_name != "name" and attribute_name != "represents":
                    attr_count += 1

        if(attr_count > 0):
            return_metadata.append(
                {
                    "consistencyGroup" : consistency_group,
                    "elementCount" : attr_count,
                    #"idCounter": id_max,
                    "name" : "nodeAttributes",
                    "properties" : [ ],
                    "version" : "1.0"
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
                            "consistencyGroup" : consistency_group,
                            "elementCount":len(asp[aspect_type]),
                            "name":aspect_type,
                            "properties":[]
                         }
                    )
            except Exception as e:
                print(e.message)

        return [{'metaData': return_metadata}]

    def string_to_aspect_object(self, aspect_name):
        if aspect_name == 'metaData':
            return self.metadata
        elif aspect_name == '@context':
            return self.context
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
        if stream:
            return self.stream_aspect(uuid, aspect_name, server, username, password)
        else:
            return self.get_stream(uuid, aspect_name, server, username, password)

    # The stream refers to the Response, not the Request
    def get_stream(self, uuid, aspect_name, server, username, password):
        if 'http' not in server:
            server = 'http://' + server

        s = requests.session()
        if username and password:
            # add credentials to the session, if available
            s.auth = (username, password)

        if aspect_name == 'metaData':
            md_response = s.get(server + '/v2/network/' + uuid + '/aspect')
            json_response = md_response.json()
            return json_response.get('metaData')
        else:
            aspect_response = s.get(server + '/v2/network/' + uuid + '/aspect/' + aspect_name)
            json_response = aspect_response.json()
            return json_response

    def stream_aspect(self, uuid, aspect_name, server, username, password):
        if 'http' not in server:
            server = 'http://' + server
        if aspect_name == 'metaData':
            print(server + '/v2/network/' + uuid + '/aspect')

            s = requests.session()
            if username and password:
                # add credentials to the session, if available
                s.auth = (username, password)
            md_response = s.get(server + '/v2/network/' + uuid + '/aspect')
            json_response = md_response.json()
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

            return ijson.items(urlopen_result, 'item')

class DecimalEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        if sys.version_info.major == 3:
            if isinstance(o, np.int64):
                return int(o)
        return super(DecimalEncoder, self).default(o)

import ndex2.client as nc
