class NiceCx(object):
    def create_edge(self, id=None, edge_source=None, edge_target=None, edge_interaction=None, cx_fragment=None):
        '''
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
        '''
        pass

    def add_edge(self, edge_element):
        '''
        Add an edge object to the network. (For an easier method for adding edges use create_edge() )
        :param edge_element: An edge object
        :type edge_element: nicecxModel.cx.aspects.EdgesElement
        :return: Edge ID
        :rtype:
        '''
        pass

    def add_network_attribute(self, network_attribute_element=None, subnetwork=None, property_of=None, name=None, values=None, type=None, json_obj=None):
        pass

    def add_node_attribute(self, node_attribute_element=None, i=None, subnetwork=None, property_of=None, name=None, values=None, type=None, cx_fragment=None):
        pass

    def set_node_attribute_from_cx_fragment(self,cx_fragment):
        pass

    def set_edge_attribute_from_cx_fragment(self,cx_fragment):
        pass

    def set_node_attribute_delete_me(self, node_attribute_element=None, i=None, subnetwork=None, property_of=None, name=None, values=None, type=None, json_obj=None):
        pass

    def add_edge_attribute(self, edge_attribute_element=None, i=None, subnetwork=None, property_of=None, name=None, values=None, type=None, cx_fragment=None):
        pass

    def add_support(self, support_element):
        pass

    def add_citation(self, citation_element):
        pass

    def add_node_citations_from_cx(self, node_citation_cx):
        pass

    def add_node_citations(self, node_id, citation_id):
        pass

    def add_edge_citations_from_cx(self, edge_citation_cx):
        pass

    def add_edge_citations(self, edge_id, citation_id):
        pass

    def add_edge_supports(self, edge_supports_element):
        pass

    def build_many_to_many_relation(self, aspect_name, element, relation_name):
        pass

    # TODO
    # make opaque aspect into a one shot method to set the whole aspect.
    # i.e. not one element at a time
    def add_opaque_aspect(self, opaque_element):
        pass

    def set_name(self, network_name):
        '''
        Set the network name
        :param network_name: Network name
        :type network_name: string
        :return: None
        :rtype:none
        '''
        pass

    def get_name(self):
        '''
        Get the network name
        :return: Network name
        :rtype: string
        '''
        pass

    def add_name_space(self, prefix, uri):
        pass

    def set_namespaces(self,ns ):
        pass

    def get_namespaces(self,):
        pass

    def get_edges (self):
        '''
        Returns an iterator over edge ids as keys and edge objects as values.
        :return: Edge iterator
        :rtype: iterator
        '''
        pass

    def get_edge(self, edge):
        pass

    def get_edge_attribute_object(self, edge, attribute_name):
        pass

    #==============================
    # NETWORK PROPERTY OPERATIONS
    #==============================
    def set_network_attribute(self, name=None, values=None, type=None, subnetwork=None, cx_fragment=None):
        '''
        Set an attribute of the network
        :param name: Attribute name
        :type name: string
        :param values: The values of the attribute
        :type values: list, string, float or int
        :param type: The datatype of the attribute values
        :type type: nicecxModel.cx.aspects.ATTRIBUTE_DATA_TYPE
        :param subnetwork: The id of the subnetwork (if any) to which this attribute applies.
        :type subnetwork: int
        :param cx_fragment: CX fragment
        :type cx_fragment: json
        :return: None
        :rtype: none
        '''
        pass

    def get_network_attribute_objects(self, attribute_name):
        '''
        Get the value of a network attribute
        :param attribute_name: Attribute name
        :type attribute_name: string
        :return: Network attribute object
        :rtype: nicecxModel.cx.aspects.NetworkAttributesElement
        '''
        pass

    def get_network_attribute(self, attribute_name, subnetwork_id=None):
        pass

    def get_network_attributes(self):
        '''
        Get the attribute objects of the network.
        :return: List of NetworkAttributesElement objects
        :rtype: nicecxModel.cx.aspects.NetworkAttributesElement
        '''
        pass

    #==================
    # NODE OPERATIONS
    #==================
    def create_node(self, id=None, node_name=None, node_represents=None, cx_fragment=None):
        pass

    def add_node(self, node_element):
        '''
        Add a node object to the network. (For an easier method for adding nodes use create_node() )
        :param node_element: A node object
        :type node_element: nicecxModel.cx.aspects.NodesElement
        :return: Node ID
        :rtype: int
        '''
        pass

    def get_nodes(self):
        '''
        Returns an iterator over node ids as keys and node objects as values.
        :return: iterator over nodes
        :rtype: iterator
        '''
        pass

    def get_node(self, node):
        pass

    def remove_node(self, node):
        pass

    #=============================
    # NODE ATTRIBUTES OPERATIONS
    #=============================
    def set_node_attribute(self, node, attribute_name, values, type=None, subnetwork=None, cx_fragment=None):
        '''
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
        '''
        pass

    def get_node_attribute_objects(self, node, attribute_name):
        '''
        Get the attribute objects for a node attribute name, where the node may be specified by its id or passed in
        as an object. The node attribute objects include datatype and subnetwork information. An example of networks
        that include subnetworks are Cytoscape collections stored in NDEx.
        :param node: node object or node id
        :type node: nicecxModel.cx.aspects.NodesElement or int
        :param attribute_name: attribute name
        :type attribute_name: string
        :return:
        :rtype:
        '''
        pass

    def get_node_attribute(self, node, attribute_name):
        '''
        Get the value(s) of an attribute of a node, where the node may be specified by its id or passed in as an object.
        :param node: node object or node id
        :type node: nicecxModel.cx.aspects.NodesElement or int
        :param attribute_name: attribute name
        :type attribute_name:
        :return: string
        :rtype:
        '''
        pass

    def get_node_attributes(self, node):
        '''
        Get the attribute objects of a node, where the node may be specified by its id or passed in as an object.
        :param node: node object or node id
        :type node: nicecxModel.cx.aspects.NodesElement or int
        :return:
        :rtype:
        '''
        pass

    #==================================
    # EDGE ATTRIBUTE OPERATIONS
    #==================================
    def set_edge_attribute(self, edge, attribute_name, values, type=None, subnetwork=None, cx_fragment=None):
        '''
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
        '''
        pass
        
    def get_edge_attributes(self, edge):
        '''
        Get the attribute objects of an edge, where the edge may be specified by its id or passed in as an object.
        :param edge: Edge object or edge id
        :type edge: nicecxModel.cx.aspects.EdgeElement or int
        :return: Edge attribute objects
        :rtype: list of nicecxModel.cx.aspects.EdgeAttributesElement
        '''
        pass

    def get_edge_attribute_objects(self, edge, attribute_name):
        '''
        Get the attribute objects for an edge attribute name, where the edge may be specified by its id or passed in
        as an object. The edge attribute objects include datatype and subnetwork information. An example of networks
        that include subnetworks are Cytoscape collections stored in NDEx.
        :param edge: Edge object or edge id
        :type edge: nicecxModel.cx.aspects.EdgesElement or int
        :param attribute_name: Attribute name
        :type attribute_name:
        :return: Edge attribute object
        :rtype: nicecxModel.cx.aspects.EdgesAttributesElement
        '''
        pass

    # TODO - return the element as the appropriate type (cast)
    def get_edge_attribute(self, edge, attribute_name, subnetwork=None):
        '''
        Get the value(s) of an attribute of an edge, where the edge may be specified by its id or passed in as an object.
        :param edge: Edge object or edge id
        :type edge: nicecxModel.cx.aspects.EdgesElement or int
        :param attribute_name: Attribute name
        :type attribute_name:
        :param subnetwork: The id of the subnetwork (if any) to which this attribute was applied.
        :type subnetwork: int
        :return: Edge attribute value(s)
        :rtype: list, string, int or float
        '''
        pass

    def get_node_attributesx(self):
        pass

    def remove_node(self, node):
        pass

    def remove_node_attribute(self, node, attribute_name):
        pass

    def remove_edge(self, edge):
        pass

    def remove_edge_attribute(self, edge, attribute_name):
        pass

    #==================
    # OTHER OPERATIONS
    #==================

    def get_context(self):
        '''
        Get the @context aspect of the network, the aspect that maps namespace prefixes to their defining URIs
        :return: List of context objects
        :rtype: list of json objects
        '''
        pass

    def set_context(self, context):
        '''
        Set the @context aspect of the network, the aspect that maps namespace prefixes to their defining URIs
        :param context: List of context objects
        :type context: List of dict (namespace string: URI)
        :return: None
        :rtype: none
        '''
        pass

    def get_metadata(self):
        '''
        Get the network metadata
        :return: Network metadata
        :rtype: Iterator of nicecxModel.metadata.MetaDataElement
        '''
        pass

    def set_metadata(self, metadata_obj):
        '''
        Set the network metadata
        :param metadata_obj: Dict of metadata objects
        :type metadata_obj: dict of nicecxModel.metadata.MetaDataElement
        :return: None
        :rtype: none
        '''
        pass

    def add_metadata(self, md):
        pass

    def getProvenance(self):
        '''
        Get the network provenance as a Python dictionary having the CX provenance schema.
        :return: List of provenance
        :rtype: list of json objects
        '''
        pass

    def set_provenance(self, provenance):
        pass

    def get_opaque_aspect_table(self):
        pass

    def get_opaque_aspect(self, aspect_name):
        '''
        Get the elements of the aspect specified by aspect_name
        :param aspect_name: the name of the aspect to retrieve.
        :type aspect_name: string
        :return: Opaque aspect
        :rtype: nicecxModel.cx.aspects.AspectElement
        '''
        pass

    def set_opaque_aspect(self, aspect_name, aspect_elements):
        '''
        Set the aspect specified by aspect_name to the list of aspect elements. If aspect_elements is None, the
        aspect is removed.
        :param aspect_name: Name of the aspect
        :type aspect_name: string
        :param aspect_elements: Aspect element
        :type aspect_elements: nicecxModel.cx.aspects.AspectElement
        :return: None
        :rtype: none
        '''
        pass

    def get_opaque_aspect_names(self):
        '''
        Get the names of all opaque aspects
        :return: List of opaque aspect names
        :rtype: list of strings
        '''
        pass

    # TODO - determine if this is useful
    def get_edge_attribute_element(self, edge, attr_name):
        pass

    def get_edge_attributes_by_id(self, id):
        pass

    def get_node_associated_aspects(self):
        pass

    def get_edge_associated_aspects(self):
        pass

    def get_node_associated_aspect(self, aspectName):
        pass

    def get_edge_associated_aspect(self, aspectName):
        pass

    def get_provenance(self):
        pass

    def get_missing_nodes(self):
        pass

    def set_provenance(self, provenance):
        '''
        Set the network provenance
        :param provenance: List of provenance objects
        :type provenance: list
        :return: None
        :rtype: none
        '''
        pass

    def get_edge_citations(self):
        pass

    def get_node_citations(self):
        pass

    def apply_template(self, server, uuid, username=None, password=None):
        '''
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
        '''
        pass

    def merge_node_attributes(self, source_attribute1, source_attribute2, target_attribute):
        '''
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
        '''
        pass

    def create_from_pandas(self, df, source_field=None, target_field=None, source_node_attr=[], target_node_attr=[], edge_attr=[], edge_interaction=None):
        """
        Constructor that uses a pandas dataframe to build niceCX
        :param df: dataframe
        :type df: Pandas Dataframe
        :param headers:
        :type headers:
        :return: none
        :rtype: n/a
        """
        pass

    def create_from_networkx(self, G):
        """
        Constructor that uses a networkx graph to build niceCX
        :param G: networkx graph
        :type G: networkx graph
        :return: none
        :rtype: none
        """
        pass

    def create_from_server(self, server, username, password, uuid):
        pass

    def create_from_cx(self, cx):
        pass

    def get_frag_from_list_by_key(self, cx, key):
        pass

    def to_pandas_dataframe(self):
        '''
        Export the network as a Pandas DataFrame.
        Example: my_niceCx.upload_to(uuid="34f29fd1-884b-11e7-a10d-0ac135e8bacf", server="http://test.ndexbio.org",
        username="myusername", password="mypassword")
        :return: Pandas dataframe
        :rtype: Pandas dataframe
        '''
        pass

    def add_metadata_stub(self, aspect_name):
        pass

    def to_cx_stream(self):
        '''
        Returns a stream of the CX corresponding to the network. Can be used to post to endpoints that can accept
        streaming inputs
        :return: The CX stream representation of this network.
        :rtype: io.BytesIO
        '''
        pass

    def upload_to(self, server, username, password):
        '''
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
        '''
        pass

    def upload_new_network_stream(self, server, username, password):
        pass

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
        pass

    def to_networkx(self):
        '''
        Return a NetworkX graph based on the network. Elements in the CartesianCoordinates aspect of the network are transformed to the NetworkX pos attribute.
        :return: Networkx graph
        :rtype: networkx Graph()
        '''
        pass

    def get_summary(self):
        '''
        Get a network summary
        :return: Network summary
        :rtype: string
        '''
        pass

    def __str__(self):
        pass

    def to_cx(self):
        '''
        Return the CX corresponding to the network.
        :return: CX representation of the network
        :rtype: CX (list of dict aspects)
        '''
        pass

    def generate_aspect(self, aspect_name):
        pass

    def generate_metadata_aspect(self):
        pass

    def handle_metadata_update(self, aspect_name):
        pass

    def update_consistency_group(self):
        pass

    def generate_metadata(self, G, unclassified_cx):
        pass

    def string_to_aspect_object(self, aspect_name):
        pass

    def get_aspect(self, uuid, aspect_name, server, username, password, stream=False):
        pass

    # The stream refers to the Response, not the Request
    def get_stream(self, uuid, aspect_name, server, username, password):
        pass

    def stream_aspect(self, uuid, aspect_name, server, username, password):
        pass

