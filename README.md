# **NDEx2 Client v1.0**

## **Overview**

The NDEx2 Client v1.0 Python module provides methods to access NDEx via the NDEx Server API. It also provides methods for common operations on networks. It includes the NiceCX network object class for convenient NDEx access and as a data model for applications.

## **Jupyter Notebook Tutorials**
* Basic Use of the NDEx2 Client:[NDEx2 Client v1.0 Tutorial](https://github.com/ndexbio/ndex-jupyter-notebooks/blob/master/notebooks/NDEx2%20Client%20v1.0%20Tutorial.ipynb)
* Working with the NiceCX Network Class: [NiceCX v1.0 Tutorial](https://github.com/ndexbio/ndex-jupyter-notebooks/blob/master/notebooks/NiceCX%20v1.0%20Tutorial.ipynb)

## **Requirements**

The NDEx2 Client 1.0 module requires Python 3.6+ and the latest version of the PIP Python package manager for installation. [Click here](https://pypi.python.org/pypi/pip) to download the PIP Python package.

## **Installing the NDEx2 Client Module**

The NDEx2 Client 1.0 module can be installed from the Python Package Index (PyPI) repository using PIP:

> pip install ndex2

If you already have an older version of the ndex2 module installed, you can use this command instead:

> pip install --upgrade ndex2

## **NDEx2 Client Objects**

The NDEx2 Client provides an interface to an NDEx server that is managed via a client object class. An NDEx2 Client object can be used to access an NDEx server either anonymously or using a specific user account. For each NDEx server and user account that you want to use in your script or application, you create an NDEx2 Client instance. In this example, a client object is created to access the public NDEx server.
```
import ndex2.client
anon_ndex=ndex2.client.Ndex("http://public.ndexbio.org")
```
A client object using a specific user account can perform operations requiring authentication, such as saving networks to that account.
```
my_account="your account"
my_password="your password"
my_ndex=ndex2.client.Ndex("http://public.ndexbio.org", my_account, my_password)
```

### **NDEx Client Object Methods:**

#### **Status**

##### **update_status()**

* Updates the client object *status* attribute with the status of the NDEx Server.

#### **Users**

##### **get_user_by_username(username)**

* Returns a user object corresponding to the provided username

* Error if this account is not found

* If the user account has not been verified by the user yet, the returned object will contain no user UUID and the *isVerified* field will be false.

#### **Network**

##### **save_new_network(cx)**

* Creates a new network from cx, a python dict in CX format.

##### **save_cx_stream_as_new_network(cx_stream)**

* Creates a network from the byte stream cx_stream.

##### **update_cx_network(cx_stream, network_id)**

* Updates network specified by network_id with the new content from the byte stream cx_stream.

* Errors if the network_id does not correspond to an existing network on the NDEx Server which the authenticated user either owns or has WRITE permission.

* Errors if the cx_stream data is larger than the maximum size allowed by the NDEx server.

##### **delete_network(network_id)**

* Deletes the network specified by network_id.

* There is no method to undo a deletion, so care should be exercised.

* The specified network must be owned by the authenticated user.

##### **get_network_summary(network_id)**

* Retrieves a NetworkSummary JSON object from the network specified by network_id and returns it as a Python dict.

* A NetworkSummary object provides useful information about the network, a mixture of network profile information (properties expressed in special aspects of the network CX), network properties (properties expressed in the networkAttributes aspect of the network CX) and network system properties (properties expressing how the network is stored on the server, not part of the network CX).

<table>
  <tr>
    <td>Attribute</td>
    <td>Description</td>
    <td>Type</td>
  </tr>
  <tr>
    <td>creationTme</td>
    <td>Time at which the network was created</td>
    <td>timeStamp</td>
  </tr>
  <tr>
    <td>description</td>
    <td>Text description of the network, same meaning as dc:description</td>
    <td>string</td>
  </tr>
  <tr>
    <td>edgeCount</td>
    <td>The number of edge objects in the network</td>
    <td>integer</td>
  </tr>
  <tr>
    <td>errorMessage</td>
    <td>If this network is not a valid CX network, this field holds the error message produced by the CX network validator.</td>
    <td>string</td>
  </tr>
  <tr>
    <td>externalId</td>
    <td>UUID of the network</td>
    <td>string</td>
  </tr>
  <tr>
    <td>isDeleted</td>
    <td>True if the network is marked as deleted</td>
    <td>boolean</td>
  </tr>
  <tr>
    <td>isReadOnly</td>
    <td>True if the network is marked as readonly</td>
    <td>boolean</td>
  </tr>
  <tr>
    <td>isShowCase</td>
    <td>True if the network is showcased</td>
    <td>boolean</td>
  </tr>
  <tr>
    <td>isValid</td>
    <td>True if the network is a valid CX network</td>
    <td>boolean</td>
  </tr>
  <tr>
    <td>modificationTime</td>
    <td>Time at which the network was last modified</td>
    <td>timeStamp</td>
  </tr>
  <tr>
    <td>name</td>
    <td>Name or title of the network, not unique, same meaning as dc:title</td>
    <td>string</td>
  </tr>
  <tr>
    <td>nodeCount</td>
    <td>The number of node objects in the network</td>
    <td>integer</td>
  </tr>
  <tr>
    <td>owner</td>
    <td>The userName of the network owner</td>
    <td>string</td>
  </tr>
  <tr>
    <td>ownerUUID</td>
    <td>The UUID of the networks owner</td>
    <td>string</td>
  </tr>
  <tr>
    <td>properties</td>
    <td>List of NDExPropertyValuePair objects: describes properties of the networ</td>
    <td>list</td>
  </tr>
  <tr>
    <td>subnetworkIds</td>
    <td>List of integers which are identifiers of subnetworks</td>
    <td>list</td>
  </tr>
  <tr>
    <td>uri</td>
    <td>URI of the current network</td>
    <td>string</td>
  </tr>
  <tr>
    <td>version</td>
    <td>Format is not controlled but best practice is to use a string conforming to Semantic Versioning</td>
    <td>string</td>
  </tr>
  <tr>
    <td>visibility</td>
    <td>PUBLIC or PRIVATE. PUBLIC means it can be found or read by anyone, including anonymous users. PRIVATE is the default, means that it can only be found or read by users according to their permissions</td>
    <td>string</td>
  </tr>
  <tr>
    <td>warnings</td>
    <td>List of warning messages produced by the CX network validator</td>
    <td>list</td>
  </tr>
</table>


* * * *


* The **properties** attribute in the above table represents a list of attributes where each attribute is a dictionary with the following fields:

<table>
  <tr>
    <td>Property Object Field</td>
    <td>Description</td>
    <td>Type</td>
  </tr>
  <tr>
    <td>dataType</td>
    <td>Type of the attribute</td>
    <td>string</td>
  </tr>
  <tr>
    <td>predicateString</td>
    <td>Name of the attribute.</td>
    <td>string</td>
  </tr>
  <tr>
    <td>value</td>
    <td>Value of the attribute</td>
    <td>string</td>
  </tr>
  <tr>
    <td>subNetworkId</td>
    <td>Subnetwork Id of the attribute</td>
    <td>string</td>
  </tr>
</table>


* * * *


* Errors if the network is not found or if the authenticated user does not have READ permission for the network.

* Anonymous users can only access networks with visibility = PUBLIC.

##### **get_network_as_cx_stream(network_id)**

* Returns the network specified by network_id as a CX byte stream.

* This is performed as a monolithic operation, so it is typically advisable for applications to first use the getNetworkSummary method to check the node and edge counts for a network before retrieving the network.

##### **set_network_system_properties(network_id, network_system_properties)**

* Sets the system properties specified in network_system_properties data for the network specified by network_id.

* Network System properties describe the network’s status on the NDEx server but are not part of the corresponding CX network object.

* As of NDEx V2.0 the supported system properties are:

    * readOnly: boolean

    * visibility: PUBLIC or PRIVATE.

    * showcase: boolean. Controls whether the network will display on the homepage of the authenticated user. Returns an error if the user does not have explicit permission to the network.

    * network_system_properties format: {property: value, ...}, such as:

        * {"readOnly": True}

        * {"visibility": “PUBLIC”}

        * {"showcase": True}

        * {"readOnly": True, “visibility”: “PRIVATE”, “showcase”: False}.

##### **make_network_private(network_id)**

* Sets visibility of the network specified by network_id to private.

* This is a shortcut for setting the visibility of the network to PRIVATE with the set_network_system_properties method:

    * set_network_system_properties(network_id, {"visibility": “PRIVATE”}).

##### **make_network_public(network_id)**

* Sets visibility of the network specified by network_id to public

* This is a shortcut for setting the visibility of the network to PUBLIC with the set_network_system_properties method:

    * set_network_system_properties(network_id, {"visibility": “PUBLIC”}).

##### **set_read_only(network_id, value)**

* Sets the read-only flag of the network specified by network_id to value.

* The type of value is boolean (True or False).

* This is a shortcut for setting readOnly for the network by the set_network_system_properties method:

    * set_network_system_properties(network_id, {"readOnly": True})

    * set_network_system_properties(network_id, {"readOnly": False}).

##### **update_network_group_permission(group_id, network_id, permission)**

* Updates the permission of a group specified by group_id for the network specified by network_id.

* The permission is updated to the value specified in the permission parameter, either READ, WRITE, or ADMIN.

* Errors if the authenticated user making the request does not have WRITE or ADMIN permissions to the specified network.

* Errors if network_id does not correspond to an existing network.

* Errors if the operation would leave the network without any user having ADMIN permissions: NDEx does not permit networks to become 'orphans' without any owner.

##### **grant_networks_to_group(group_id, network_ids, permission="READ”)**

* Updates the permission of a group specified by group_id for all the networks specified in network_ids list

* For each network, the permission is updated to the value specified in the permission parameter. permission parameter is READ, WRITE, or ADMIN; default value is READ.

* Errors if the authenticated user making the request does not have WRITE or ADMIN permissions to each network.

* Errors if any of the network_ids does not correspond to an existing network.

* Errors if it would leave any network without any user having ADMIN permissions: NDEx does not permit networks to become 'orphans' without any owner.

##### **update_network_user_permission(user_id, network_id, permission)**

* Updates the permission of the user specified by user_id for the network specified by network_id.

* The permission is updated to the value specified in the permission parameter. permission parameter is READ, WRITE, or ADMIN.

* Errors if the authenticated user making the request does not have WRITE or ADMIN permissions to the specified network.

* Errors if network_id does not correspond to an existing network.

* Errors if it would leave the network without any user having ADMIN permissions: NDEx does not permit networks to become 'orphans' without any owner.

##### **grant_network_to_user_by_username(username, network_id, permission)**

* Updates the permission of a user specified by username for the network specified by network_id.

* This method is equivalent to getting the user_id via get_user_by_name(username), and then calling update_network_user_permission with that user_id.

##### **grant_networks_to_user(user_id, network_ids, permission="READ”)**

* Updates the permission of a user specified by user_id for all the networks specified in network_ids list.

##### **update_network_profile(network_id, network_profile)**

* Updates the profile information of the network specified by network_id based on a network_profile object specifying the attributes to update.

* Any profile attributes specified will be updated but attributes that are not specified will have no effect - omission of an attribute does not mean deletion of that attribute.

* The network profile attributes that can be updated by this method are 'name', 'description' and 'version'.

##### **set_network_properties(network_id, network_properties)**

* Updates the NetworkAttributes aspect the network specified by network_id based on the list of NdexPropertyValuePair objects specified in network_properties.

* **This method requires careful use**:

    * Many networks in NDEx have no subnetworks and in those cases the subNetworkId attribute of every NdexPropertyValuePair should **not** be set.

    * Some networks, including some saved from Cytoscape have one subnetwork. In those cases, every NdexPropertyValuePair should have the **subNetworkId attribute set to the id of that subNetwork**.

    * Other networks originating in Cytoscape Desktop correspond to Cytoscape "collections" and may have multiple subnetworks. Each subnetwork may have NdexPropertyValuePairs associated with it and these will be visible in the Cytoscape network viewer. The collection itself may have NdexPropertyValuePairs associated with it and these are not visible in the Cytoscape network viewer but may be set or read by specific Cytoscape Apps. In these cases, **we strongly recommend that you edit these network attributes in Cytoscape** rather than via this API unless you are very familiar with the Cytoscape data model.

* NdexPropertyValuePair object has these attributes:

<table>
  <tr>
    <td>Attribute</td>
    <td>Description</td>
    <td>Type</td>
  </tr>
  <tr>
    <td>subNetworkId</td>
    <td>Optional identifier of the subnetwork to which the property applies.</td>
    <td>string</td>
  </tr>
  <tr>
    <td>predicateString</td>
    <td>Name of the attribute.</td>
    <td>string</td>
  </tr>
  <tr>
    <td>dataType</td>
    <td>Data type of this property. Its value has to be one of the attribute data types that CX supports.</td>
    <td>string</td>
  </tr>
  <tr>
    <td>value</td>
    <td>A string representation of the property value.</td>
    <td>string</td>
  </tr>
</table>


* * * *


* Errors if the authenticated user does not have ADMIN permissions to the specified network.

* Errors if network_id does not correspond to an existing network.

##### **get_provenance(network_id)**

* Returns the Provenance aspect of the network specified by network_id.

* See the document [NDEx Provenance History](http://www.home.ndexbio.org/network-provenance-history/) for a detailed description of this structure and best practices for its use.

* Errors if network_id does not correspond to an existing network.

* The returned value is a Python dict corresponding to a JSON ProvenanceEntity object:

    * A provenance history is a tree structure containing ProvenanceEntity and ProvenanceEvent objects. It is serialized as a JSON structure by the NDEx API.

    * The root of the tree structure is a ProvenanceEntity object representing the current state of the network.

    * Each ProvenanceEntity may have a single ProvenanceEvent object that represents the immediately prior event that produced the ProvenanceEntity. In turn, linked to network of ProvenanceEvent and ProvenanceEntity objects representing the workflow history that produced the current state of the Network.

    * The provenance history records significant events as Networks are copied, modified, or created, incorporating snapshots of information about "ancestor" networks.

    * Attributes in ProvenanceEntity:

        * *uri* : URI of the resource described by the ProvenanceEntity. This field will not be set in some cases, such as a file upload or an algorithmic event that generates a network without a prior network as input

        * *creationEvent* : ProvenanceEvent. has semantics of PROV:wasGeneratedBy properties: array of SimplePropertyValuePair objects

    * Attributes in ProvenanceEvent:

        * *endedAtTime* : timestamp. Has semantics of PROV:endedAtTime

        * *startedAtTime* : timestamp. Has semantics of PROV:endedAtTime

        * *inputs* : array of ProvenanceEntity objects. Has semantics of PROV:used.

        * *properties *: array of SimplePropertyValuePair.

##### **set_provenance(network_id, provenance)**

* Updates the Provenance aspect of the network specified by network_id to be the ProvenanceEntity object specified by provenance argument.

* The provenance argument is intended to represent the current state and history of the network and to contain a tree-structure of ProvenanceEvent and ProvenanceEntity objects that describe the networks provenance history.

* Errors if the authenticated user does not have ADMIN permissions to the specified network.

* Errors if network_id does not correspond to an existing network.

#### **Search**

##### **search_networks(search_string="", account_name=None, start=0, size=100, include_groups=False)**

* Returns a SearchResult object which contains:

    * Array of NetworkSummary objects (networks)

    * the total hit count of the search (numFound)

    * Position of the returned elements (start)

* Search_string parameter specifies the search string.

* **DEPRECATED**: the account_name is optional, but has been superseded by the search string field **userAdmin:account_name** If it is provided, the the search will be constrained to networks owned by that account.

* The start and size parameter are optional. The default values are start = 0 and size = 100.

* The optional include_groups argument defaults to false. It enables search to return a network where a group has permission to access the network and the user is a member of the group. if include_groups is true, the search will also return networks based on permissions from the authenticated user’s group memberships.

* The method find_networks is a deprecated alternate name for search_networks.

##### **find_networks(search_string="", account_name=None, start=0, size=100)**

* This method is deprecated; search_networks should be used instead.

##### **get_network_summaries_for_user(account_name)**

* Returns a SearchResult object which contains:

    * Array of NetworkSummary objects (networks)

    * The total hit count of the search (numFound)

    * Position of the returned elements (start) for user specified by acount_name argument.

* The number of found NetworkSummary objects is limited to (will not exceed) 1000.

* This function will not return networks where a group has permission to access the network and account_name is a member of the group.

* This function is equivalent to calling search_networks("", account_name, size=1000).

##### **get_network_ids_for_user(account_name)**

* Returns a list of network Ids for the user specified by acount_name argument. The number of found network Ids is limited to (will not exceed) 1000.

* This function is equivalent to calling get_network_summaries_for_user("", account_name, size=1000), and then building a list of network Ids returned by the call to get_network_summaries_for_user.

##### **get_neighborhood_as_cx_stream(network_id, search_string, search_depth=1, edge_limit=2500)**

* Returns a network CX byte stream that is a subset (neighborhood) of the network specified by network_id.

* The subset is determined by a traversal search from nodes identified by search_string to a depth specified by search_depth.

* edge_limit specifies the maximum number of edges that this query can return.

* Server will return an error if the number of edges in the result is larger than the edge_limit parameter.

##### **get_neighborhood(network_id, search_string, search_depth=1, edge_limit=2500)**

* The arguments and behavior are the same as get_neighborhood_as_cx_stream but returns a Python dict corresponding to a network CX JSON object.

#### **Task**

##### **get_task_by_id(task_id)**

* Returns a JSON task object for the task specified by task_id.

* Errors if no task found or if the authenticated user does not own the specified task.

## **NiceCX Objects**

**addCitation(citation_element)**

* Add a citation to the network

**addEdge(id=None, edge_source=None, edge_target=None, edge_interaction=None, json_obj=None, edge_element=None)**

* Add an edge to the network.  

* **id**: Optional identifier.  If one is not provided niceCx will generate one internally

* **edge_source**: Id of the source node for this edge

* **edge_target**: Id of the target node for this edge

* **edge_interaction**: The interaction that describes the relationship between the source and target nodes

* **json_obj**: The cx representation of an edge

* **edge_element**: The niceCx model representation for an edge (nicecxModel.cx.aspects.EdgesElement)

**addEdgeAttribute(property_of=None, name=None, values=None, type=None, subnetwork=None, json_obj=None, edge_attribute_element=None)**

* Add an attribute to the given edge

* **id**: Optional identifier.  If one is not provided niceCx will generate one internally

* **edge_source**: Id of the source node for this edge

* **edge_target**: Id of the target node for this edge

* **edge_interaction**: The interaction that describes the relationship between the source and target nodes

* **json_obj**: The cx representation of an edge attribute

* **edge_attribute_element**: The niceCx model representation for an edge attribute (nicecxModel.cx.aspects.EdgeAttributesElement)

**addEdgeCitations(edge_id, citation_id)**

* Connect a citation to the given edge

**addEdgeCitationsFromCX(edge_citation_cx)**

* Add a citation to the network

**addEdgeSupports(edge_supports_element)**

* Used to add 

**addNameSpace(prefix, uri)**

* Used to add a name space to the network

**addNetworkAttribute(network_attribute_element=None, subnetwork=None, property_of=None, name=None, values=None, type=None, json_obj=None)**

* Used to add an attribute to the network

**addNode(id=None, node_name=None, node_represents=None, json_obj=None, node_element=None)**

* Used to add a node to the network.

* **id**: Optional identifier.  If one is not provided niceCx will generate one internally

* **node_name**: Name for the node

* **node_represents**: The representation for the node.  This can be used to store the normalized id for the node

* **json_obj**: The cx representation of a node

* **node_element**: The niceCx model representation for a node (nicecxModel.cx.aspects.NodesElement)

**addNodeAssociatedAspectElement(nodeId, elmt)**

* Used to associate an element with the specified node 

**addEdgeAssociatedAspect(aspectName)**

* Used to associate an element with the specified edge 

**addNodeAttribute(subnetwork=None, property_of=None, name=None, values=None, type=None, json_obj=None, node_attribute_element=None)**

* Used to add a node attribute to the network.

* **subnetwork**: Optional subnetwork id

* **property_of**: Id of the node this attribute will be associated with

* **name**: The name of the attribute

* **values**: The value(s) of the attribute

* **type**: The type of the value(s)

* **json_obj**: The cx representation of the node attribute

* **node_attribute_element**: The niceCx model representation for a node attribute (nicecxModel.cx.aspects.NodeAttributesElement)

**addNodeCitations(node_id, citation_id)**

* Used to associate a citation with a node

* **node_id**: The id of the node

* **citation_id**: The id of the citation

**addOpaqueAspect(opaque_element)**

* Used to add an opaque aspect (nicecxModel.cx.aspects.AspectElement)

**addSupport(support_element)**

* Add a support element (nicecxModel.cx.aspects.SupportElement)

**apply_template(server, username, password, uuid)**

* Used to add a layout template to the network

* **server**: The ndex server host of the network from which the layout will be copied

* **username**: Optional username to enable access to a private network

* **password**: Optional password to enable access to a private network

* **uuid**: The unique identifier of the network from which the layout will be copied

**getEdgeAssociatedAspect(aspectName)**

* Get the edge associated aspect specified

**getEdgeAssociatedAspects()**

* Get all edge associated aspects

**getEdgeAttributes()**

* Get all edge attributes

**getEdgeAttributesById(id)**

* Get the specified edge attribute

**getEdgeCitations()**

* Get all edge citations

**getEdges()**

* Get all edges

**getMetadata()**

* Get the network metadata

**getName()**

* Get the network name

**getNamespaces()**

* Get the network name spaces

**getNetworkAttributes()**

* Get all network attributes

**getNodeAssociatedAspect(aspectName)**

* Get the specified node associated aspect

**getNodeAssociatedAspects()**

* Get all node associated aspects

**getNodeAttributes()**

* Get all node attributes

**getNodeCitations()**

* Get all node citations

**getNodes()**

* Get all nodes

**getOpaqueAspectTable()**

* Get all opaque aspects

**getProvenance()**

* Get the network provenance

**getSummary()**

* Get a simple network summary 

**setName(network_name)**

* Set the network name

**setNamespaces(ns)**

* Set the network name spaces

**setProvenance(provenance)**

* Set the network provenance

**stream_cx()**

* returns the CX stream representation of the network.

**to_json()**

* Marshal the network into a cx - json structure

**to_networkx()**

* Export the network as a networkx graph

**to_pandas()**

* Export the network as a Pandas DataFrame

**update_to(uuid, server, username, password)**

* Upload this network to the specified server to the account specified by username and password.

* **uuid**: The uuid of the network being updated.

* **server**: The NDEx server to upload the network to.

* **username**: The username of the account to store the network.

* **password**: The password for the account.

* returns: The UUID of the network on NDEx.

* Example: my_niceCx.upload_to(uuid=’34f29fd1-884b-11e7-a10d-0ac135e8bacf’, server='http://test.ndexbio.org', username='myusername', password='mypassword')

**upload_to(server, username, password)**

* Upload this network to the specified server to the account specified by username and password.

* server: The NDEx server to upload the network to.

* username: The username of the account to store the network.

* password: The password for the account.

* return: The UUID of the network on NDEx.

* Example: my_niceCx.upload_to('http://test.ndexbio.org', 'myusername', 'mypassword')

