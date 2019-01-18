**NDEx2 Client v2.0**
=====================

.. image:: https://img.shields.io/travis/ndexbio/ndex2-client.svg
        :target: https://travis-ci.org/ndexbio/ndex2-client.svg?branch=master

.. image:: https://img.shields.io/pypi/v/ndex2.svg
        :target: https://pypi.python.org/pypi/ndex2

.. image:: https://coveralls.io/repos/github/ndexbio/ndex2-client/badge.svg?branch=master
  :target: https://coveralls.io/github/ndexbio/ndex2-client?branch=master


**Overview**
------------

The NDEx2 Client v2.0 Python module provides methods to access NDEx via
the NDEx Server API. It also provides methods for common operations on
networks. It includes the NiceCX network object class for convenient
NDEx access and as a data model for applications.

**Jupyter Notebook Tutorials**
------------------------------

-  Basic Use of the NDEx2 Client:  `NDEx2 Client v2.0
   Tutorial <https://github.com/ndexbio/ndex-jupyter-notebooks/blob/master/notebooks/NDEx2%20Client%20v2.0%20Tutorial.ipynb>`__
-  Working with the NiceCX Network Class: `NiceCX v2.0
   Tutorial <https://github.com/ndexbio/ndex-jupyter-notebooks/blob/master/notebooks/NiceCX%20v2.0%20Tutorial.ipynb>`__

To use these tutorials, clone the `ndex-jupyter-notebooks
repository <https://github.com/ndexbio/ndex-jupyter-notebooks>`__ to
your local machine and start Jupyter Notebooks in the project directory.

For information on installing and using Jupyter Notebooks, go to
`jupyter.org <http://jupyter.org/>`__

**Requirements**
----------------

The NDEx2 Client 2.0 module requires Python 3.6+ and the latest version
of the PIP Python package manager for installation. `Click
here <https://pypi.python.org/pypi/pip>`__ to download the PIP Python
package.

**Installing the NDEx2 Client Module**
--------------------------------------

The NDEx2 Client 2.0 module can be installed from the Python Package
Index (PyPI) repository using PIP:

    pip install ndex2

If you already have an older version of the ndex2 module installed, you
can use this command instead:

    pip install --upgrade ndex2

**NDEx2 Client Objects**
------------------------

The NDEx2 Client provides an interface to an NDEx server that is managed
via a client object class. An NDEx2 Client object can be used to access
an NDEx server either anonymously or using a specific user account. For
each NDEx server and user account that you want to use in your script or
application, you create an NDEx2 Client instance. In this example, a
client object is created to access the public NDEx server.

::

    import ndex2.client
    anon_ndex=ndex2.client.Ndex2("http://public.ndexbio.org")

A client object using a specific user account can perform operations
requiring authentication, such as saving networks to that account.

::

    my_account="your account"
    my_password="your password"
    my_ndex=ndex2.client.Ndex2("http://public.ndexbio.org", my_account, my_password)

**NDEx Client Object Methods:**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Status**
^^^^^^^^^^

**update\_status()**
''''''''''''''''''''

-  Updates the client object *status* attribute with the status of the
   NDEx Server.

**Users**
^^^^^^^^^

**get\_user\_by\_username(username)**
'''''''''''''''''''''''''''''''''''''

-  Returns a user object corresponding to the provided username

-  Error if this account is not found

-  If the user account has not been verified by the user yet, the
   returned object will contain no user UUID and the *isVerified* field
   will be false.

**Network**
^^^^^^^^^^^

**save\_new\_network(cx)**
''''''''''''''''''''''''''

-  Creates a new network from cx, a python dict in CX format.

**save\_cx\_stream\_as\_new\_network(cx\_stream)**
''''''''''''''''''''''''''''''''''''''''''''''''''

-  Creates a network from the byte stream cx\_stream.

**update\_cx\_network(cx\_stream, network\_id)**
''''''''''''''''''''''''''''''''''''''''''''''''

-  Updates network specified by network\_id with the new content from
   the byte stream cx\_stream.

-  Errors if the network\_id does not correspond to an existing network
   on the NDEx Server which the authenticated user either owns or has
   WRITE permission.

-  Errors if the cx\_stream data is larger than the maximum size allowed
   by the NDEx server.

**delete\_network(network\_id)**
''''''''''''''''''''''''''''''''

-  Deletes the network specified by network\_id.

-  There is no method to undo a deletion, so care should be exercised.

-  The specified network must be owned by the authenticated user.

**get\_network\_summary(network\_id)**
''''''''''''''''''''''''''''''''''''''

-  Retrieves a NetworkSummary JSON object from the network specified by
   network\_id and returns it as a Python dict.

-  A NetworkSummary object provides useful information about the
   network, a mixture of network profile information (properties
   expressed in special aspects of the network CX), network properties
   (properties expressed in the networkAttributes aspect of the network
   CX) and network system properties (properties expressing how the
   network is stored on the server, not part of the network CX).

.. raw:: html

   <table>
     <tr>
       <td>

Attribute

.. raw:: html

   </td>
       <td>

Description

.. raw:: html

   </td>
       <td>

Type

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

creationTme

.. raw:: html

   </td>
       <td>

Time at which the network was created

.. raw:: html

   </td>
       <td>

timeStamp

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

description

.. raw:: html

   </td>
       <td>

Text description of the network, same meaning as dc:description

.. raw:: html

   </td>
       <td>

string

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

edgeCount

.. raw:: html

   </td>
       <td>

The number of edge objects in the network

.. raw:: html

   </td>
       <td>

integer

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

errorMessage

.. raw:: html

   </td>
       <td>

If this network is not a valid CX network, this field holds the error
message produced by the CX network validator.

.. raw:: html

   </td>
       <td>

string

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

externalId

.. raw:: html

   </td>
       <td>

UUID of the network

.. raw:: html

   </td>
       <td>

string

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

isDeleted

.. raw:: html

   </td>
       <td>

True if the network is marked as deleted

.. raw:: html

   </td>
       <td>

boolean

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

isReadOnly

.. raw:: html

   </td>
       <td>

True if the network is marked as readonly

.. raw:: html

   </td>
       <td>

boolean

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

isShowCase

.. raw:: html

   </td>
       <td>

True if the network is showcased

.. raw:: html

   </td>
       <td>

boolean

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

isValid

.. raw:: html

   </td>
       <td>

True if the network is a valid CX network

.. raw:: html

   </td>
       <td>

boolean

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

modificationTime

.. raw:: html

   </td>
       <td>

Time at which the network was last modified

.. raw:: html

   </td>
       <td>

timeStamp

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

name

.. raw:: html

   </td>
       <td>

Name or title of the network, not unique, same meaning as dc:title

.. raw:: html

   </td>
       <td>

string

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

nodeCount

.. raw:: html

   </td>
       <td>

The number of node objects in the network

.. raw:: html

   </td>
       <td>

integer

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

owner

.. raw:: html

   </td>
       <td>

The userName of the network owner

.. raw:: html

   </td>
       <td>

string

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

ownerUUID

.. raw:: html

   </td>
       <td>

The UUID of the networks owner

.. raw:: html

   </td>
       <td>

string

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

properties

.. raw:: html

   </td>
       <td>

List of NDExPropertyValuePair objects: describes properties of the
networ

.. raw:: html

   </td>
       <td>

list

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

subnetworkIds

.. raw:: html

   </td>
       <td>

List of integers which are identifiers of subnetworks

.. raw:: html

   </td>
       <td>

list

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

uri

.. raw:: html

   </td>
       <td>

URI of the current network

.. raw:: html

   </td>
       <td>

string

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

version

.. raw:: html

   </td>
       <td>

Format is not controlled but best practice is to use a string conforming
to Semantic Versioning

.. raw:: html

   </td>
       <td>

string

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

visibility

.. raw:: html

   </td>
       <td>

PUBLIC or PRIVATE. PUBLIC means it can be found or read by anyone,
including anonymous users. PRIVATE is the default, means that it can
only be found or read by users according to their permissions

.. raw:: html

   </td>
       <td>

string

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

warnings

.. raw:: html

   </td>
       <td>

List of warning messages produced by the CX network validator

.. raw:: html

   </td>
       <td>

list

.. raw:: html

   </td>
     </tr>
   </table>

--------------

-  The **properties** attribute in the above table represents a list of
   attributes where each attribute is a dictionary with the following
   fields:

.. raw:: html

   <table>
     <tr>
       <td>

Property Object Field

.. raw:: html

   </td>
       <td>

Description

.. raw:: html

   </td>
       <td>

Type

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

dataType

.. raw:: html

   </td>
       <td>

Type of the attribute

.. raw:: html

   </td>
       <td>

string

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

predicateString

.. raw:: html

   </td>
       <td>

Name of the attribute.

.. raw:: html

   </td>
       <td>

string

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

value

.. raw:: html

   </td>
       <td>

Value of the attribute

.. raw:: html

   </td>
       <td>

string

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

subNetworkId

.. raw:: html

   </td>
       <td>

Subnetwork Id of the attribute

.. raw:: html

   </td>
       <td>

string

.. raw:: html

   </td>
     </tr>
   </table>

--------------

-  Errors if the network is not found or if the authenticated user does
   not have READ permission for the network.

-  Anonymous users can only access networks with visibility = PUBLIC.

**get\_network\_as\_cx\_stream(network\_id)**
'''''''''''''''''''''''''''''''''''''''''''''

-  Returns the network specified by network\_id as a CX byte stream.

-  This is performed as a monolithic operation, so it is typically
   advisable for applications to first use the getNetworkSummary method
   to check the node and edge counts for a network before retrieving the
   network.

**set\_network\_system\_properties(network\_id, network\_system\_properties)**
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

-  Sets the system properties specified in network\_system\_properties
   data for the network specified by network\_id.

-  Network System properties describe the network’s status on the NDEx
   server but are not part of the corresponding CX network object.

-  As of NDEx V2.0 the supported system properties are:

   -  readOnly: boolean

   -  visibility: PUBLIC or PRIVATE.

   -  showcase: boolean. Controls whether the network will display on
      the homepage of the authenticated user. Returns an error if the
      user does not have explicit permission to the network.

   -  network\_system\_properties format: {property: value, ...}, such
      as:

      -  {"readOnly": True}

      -  {"visibility": “PUBLIC”}

      -  {"showcase": True}

      -  {"readOnly": True, “visibility”: “PRIVATE”, “showcase”: False}.

**make\_network\_private(network\_id)**
'''''''''''''''''''''''''''''''''''''''

-  Sets visibility of the network specified by network\_id to private.

-  This is a shortcut for setting the visibility of the network to
   PRIVATE with the set\_network\_system\_properties method:

   -  set\_network\_system\_properties(network\_id, {"visibility":
      “PRIVATE”}).

**make\_network\_public(network\_id)**
''''''''''''''''''''''''''''''''''''''

-  Sets visibility of the network specified by network\_id to public

-  This is a shortcut for setting the visibility of the network to
   PUBLIC with the set\_network\_system\_properties method:

   -  set\_network\_system\_properties(network\_id, {"visibility":
      “PUBLIC”}).

**set\_read\_only(network\_id, value)**
'''''''''''''''''''''''''''''''''''''''

-  Sets the read-only flag of the network specified by network\_id to
   value.

-  The type of value is boolean (True or False).

-  This is a shortcut for setting readOnly for the network by the
   set\_network\_system\_properties method:

   -  set\_network\_system\_properties(network\_id, {"readOnly": True})

   -  set\_network\_system\_properties(network\_id, {"readOnly":
      False}).

**update\_network\_group\_permission(group\_id, network\_id, permission)**
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

-  Updates the permission of a group specified by group\_id for the
   network specified by network\_id.

-  The permission is updated to the value specified in the permission
   parameter, either READ, WRITE, or ADMIN.

-  Errors if the authenticated user making the request does not have
   WRITE or ADMIN permissions to the specified network.

-  Errors if network\_id does not correspond to an existing network.

-  Errors if the operation would leave the network without any user
   having ADMIN permissions: NDEx does not permit networks to become
   'orphans' without any owner.

**grant\_networks\_to\_group(group\_id, network\_ids, permission="READ”)**
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

-  Updates the permission of a group specified by group\_id for all the
   networks specified in network\_ids list

-  For each network, the permission is updated to the value specified in
   the permission parameter. permission parameter is READ, WRITE, or
   ADMIN; default value is READ.

-  Errors if the authenticated user making the request does not have
   WRITE or ADMIN permissions to each network.

-  Errors if any of the network\_ids does not correspond to an existing
   network.

-  Errors if it would leave any network without any user having ADMIN
   permissions: NDEx does not permit networks to become 'orphans'
   without any owner.

**update\_network\_user\_permission(user\_id, network\_id, permission)**
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

-  Updates the permission of the user specified by user\_id for the
   network specified by network\_id.

-  The permission is updated to the value specified in the permission
   parameter. permission parameter is READ, WRITE, or ADMIN.

-  Errors if the authenticated user making the request does not have
   WRITE or ADMIN permissions to the specified network.

-  Errors if network\_id does not correspond to an existing network.

-  Errors if it would leave the network without any user having ADMIN
   permissions: NDEx does not permit networks to become 'orphans'
   without any owner.

**grant\_network\_to\_user\_by\_username(username, network\_id, permission)**
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

-  Updates the permission of a user specified by username for the
   network specified by network\_id.

-  This method is equivalent to getting the user\_id via
   get\_user\_by\_name(username), and then calling
   update\_network\_user\_permission with that user\_id.

**grant\_networks\_to\_user(user\_id, network\_ids, permission="READ”)**
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

-  Updates the permission of a user specified by user\_id for all the
   networks specified in network\_ids list.

**update\_network\_profile(network\_id, network\_profile)**
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

-  Updates the profile information of the network specified by
   network\_id based on a network\_profile object specifying the
   attributes to update.

-  Any profile attributes specified will be updated but attributes that
   are not specified will have no effect - omission of an attribute does
   not mean deletion of that attribute.

-  The network profile attributes that can be updated by this method are
   'name', 'description' and 'version'.

**set\_network\_properties(network\_id, network\_properties)**
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

-  Updates the NetworkAttributes aspect the network specified by
   network\_id based on the list of NdexPropertyValuePair objects
   specified in network\_properties.

-  **This method requires careful use**:

   -  Many networks in NDEx have no subnetworks and in those cases the
      subNetworkId attribute of every NdexPropertyValuePair should
      **not** be set.

   -  Some networks, including some saved from Cytoscape have one
      subnetwork. In those cases, every NdexPropertyValuePair should
      have the **subNetworkId attribute set to the id of that
      subNetwork**.

   -  Other networks originating in Cytoscape Desktop correspond to
      Cytoscape "collections" and may have multiple subnetworks. Each
      subnetwork may have NdexPropertyValuePairs associated with it and
      these will be visible in the Cytoscape network viewer. The
      collection itself may have NdexPropertyValuePairs associated with
      it and these are not visible in the Cytoscape network viewer but
      may be set or read by specific Cytoscape Apps. In these cases,
      **we strongly recommend that you edit these network attributes in
      Cytoscape** rather than via this API unless you are very familiar
      with the Cytoscape data model.

-  NdexPropertyValuePair object has these attributes:

.. raw:: html

   <table>
     <tr>
       <td>

Attribute

.. raw:: html

   </td>
       <td>

Description

.. raw:: html

   </td>
       <td>

Type

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

subNetworkId

.. raw:: html

   </td>
       <td>

Optional identifier of the subnetwork to which the property applies.

.. raw:: html

   </td>
       <td>

string

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

predicateString

.. raw:: html

   </td>
       <td>

Name of the attribute.

.. raw:: html

   </td>
       <td>

string

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

dataType

.. raw:: html

   </td>
       <td>

Data type of this property. Its value has to be one of the attribute
data types that CX supports.

.. raw:: html

   </td>
       <td>

string

.. raw:: html

   </td>
     </tr>
     <tr>
       <td>

value

.. raw:: html

   </td>
       <td>

A string representation of the property value.

.. raw:: html

   </td>
       <td>

string

.. raw:: html

   </td>
     </tr>
   </table>

--------------

-  Errors if the authenticated user does not have ADMIN permissions to
   the specified network.

-  Errors if network\_id does not correspond to an existing network.

**get\_provenance(network\_id)**
''''''''''''''''''''''''''''''''

-  Returns the Provenance aspect of the network specified by
   network\_id.

-  See the document `NDEx Provenance
   History <http://www.home.ndexbio.org/network-provenance-history/>`__
   for a detailed description of this structure and best practices for
   its use.

-  Errors if network\_id does not correspond to an existing network.

-  The returned value is a Python dict corresponding to a JSON
   ProvenanceEntity object:

   -  A provenance history is a tree structure containing
      ProvenanceEntity and ProvenanceEvent objects. It is serialized as
      a JSON structure by the NDEx API.

   -  The root of the tree structure is a ProvenanceEntity object
      representing the current state of the network.

   -  Each ProvenanceEntity may have a single ProvenanceEvent object
      that represents the immediately prior event that produced the
      ProvenanceEntity. In turn, linked to network of ProvenanceEvent
      and ProvenanceEntity objects representing the workflow history
      that produced the current state of the Network.

   -  The provenance history records significant events as Networks are
      copied, modified, or created, incorporating snapshots of
      information about "ancestor" networks.

   -  Attributes in ProvenanceEntity:

      -  *uri* : URI of the resource described by the ProvenanceEntity.
         This field will not be set in some cases, such as a file upload
         or an algorithmic event that generates a network without a
         prior network as input

      -  *creationEvent* : ProvenanceEvent. has semantics of
         PROV:wasGeneratedBy properties: array of
         SimplePropertyValuePair objects

   -  Attributes in ProvenanceEvent:

      -  *endedAtTime* : timestamp. Has semantics of PROV:endedAtTime

      -  *startedAtTime* : timestamp. Has semantics of PROV:endedAtTime

      -  *inputs* : array of ProvenanceEntity objects. Has semantics of
         PROV:used.

      -  *properties*: array of SimplePropertyValuePair.

**set\_provenance(network\_id, provenance)**
''''''''''''''''''''''''''''''''''''''''''''

-  Updates the Provenance aspect of the network specified by network\_id
   to be the ProvenanceEntity object specified by provenance argument.

-  The provenance argument is intended to represent the current state
   and history of the network and to contain a tree-structure of
   ProvenanceEvent and ProvenanceEntity objects that describe the
   networks provenance history.

-  Errors if the authenticated user does not have ADMIN permissions to
   the specified network.

-  Errors if network\_id does not correspond to an existing network.

**Search**
^^^^^^^^^^

**search\_networks(search\_string="", account\_name=None, start=0, size=100, include\_groups=False)**
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

-  Returns a SearchResult object which contains:

   -  Array of NetworkSummary objects (networks)

   -  the total hit count of the search (numFound)

   -  Position of the returned elements (start)

-  Search\_string parameter specifies the search string.

-  **DEPRECATED**: the account\_name is optional, but has been
   superseded by the search string field **userAdmin:account\_name** If
   it is provided, the the search will be constrained to networks owned
   by that account.

-  The start and size parameter are optional. The default values are
   start = 0 and size = 100.

-  The optional include\_groups argument defaults to false. It enables
   search to return a network where a group has permission to access the
   network and the user is a member of the group. if include\_groups is
   true, the search will also return networks based on permissions from
   the authenticated user’s group memberships.

-  The method find\_networks is a deprecated alternate name for
   search\_networks.

**find\_networks(search\_string="", account\_name=None, start=0, size=100)**
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

-  This method is deprecated; search\_networks should be used instead.

**get\_network\_summaries\_for\_user(account\_name)**
'''''''''''''''''''''''''''''''''''''''''''''''''''''

-  Returns a SearchResult object which contains:

   -  Array of NetworkSummary objects (networks)

   -  The total hit count of the search (numFound)

   -  Position of the returned elements (start) for user specified by
      acount\_name argument.

-  The number of found NetworkSummary objects is limited to (will not
   exceed) 1000.

-  This function will not return networks where a group has permission
   to access the network and account\_name is a member of the group.

-  This function is equivalent to calling search\_networks("",
   account\_name, size=1000).

**get\_network\_ids\_for\_user(account\_name)**
'''''''''''''''''''''''''''''''''''''''''''''''

-  Returns a list of network Ids for the user specified by acount\_name
   argument. The number of found network Ids is limited to (will not
   exceed) 1000.

-  This function is equivalent to calling
   get\_network\_summaries\_for\_user("", account\_name, size=1000), and
   then building a list of network Ids returned by the call to
   get\_network\_summaries\_for\_user.

**get\_neighborhood\_as\_cx\_stream(network\_id, search\_string, search\_depth=1, edge\_limit=2500)**
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

-  Returns a network CX byte stream that is a subset (neighborhood) of
   the network specified by network\_id.

-  The subset is determined by a traversal search from nodes identified
   by search\_string to a depth specified by search\_depth.

-  edge\_limit specifies the maximum number of edges that this query can
   return.

-  Server will return an error if the number of edges in the result is
   larger than the edge\_limit parameter.

**get\_neighborhood(network\_id, search\_string, search\_depth=1, edge\_limit=2500)**
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

-  The arguments and behavior are the same as
   get\_neighborhood\_as\_cx\_stream but returns a Python dict
   corresponding to a network CX JSON object.

**Task**
^^^^^^^^

**get\_task\_by\_id(task\_id)**
'''''''''''''''''''''''''''''''

-  Returns a JSON task object for the task specified by task\_id.

-  Errors if no task found or if the authenticated user does not own the
   specified task.

**NiceCX Objects**
------------------

**Nodes**
~~~~~~~~~

**create\_node(name, represents=None)**

Create a new node in the network, specifying the node's name and
optionally the id of the entity that it represents.

-  **name**: Name for the node
-  **represents**: The ID of the entity represented by the node. Best
   practice is to use IDs from standard namespaces and to define
   namespace prefixes in the network context.

**add\_node(node)**

Add a node object to the network.

-  **node**: A node object (nicecxModel.cx.aspects.NodesElement)

**set\_node\_attribute(node, attribute\_name, values, type=None,
subnetwork=None)**

Set the value(s) of an attribute of a node, where the node may be
specified by its id or passed in as an object.

-  **node**: node object or node id
-  **attribute\_name**: attribute name
-  **values**: A value or list of values of the attribute
-  **type**: the datatype of the attribute values, defaults to the
   python datatype of the values.
-  **subnetwork**: the id of the subnetwork to which this attribute
   applies.

**get\_node\_attribute(node, attribute\_name, subnetwork=None)**

Get the value(s) of an attribute of a node, where the node may be
specified by its id or passed in as an object.

-  **node**: node object or node id
-  **attribute\_name**: attribute name
-  **subnetwork**: the id of the subnetwork (if any) to which this
   attribute applies.

**get\_node\_attribute\_objects(node, attribute\_name)**

Get the attribute objects for a node attribute name, where the node may
be specified by its id or passed in as an object. The node attribute
objects include datatype and subnetwork information. An example of
networks that include subnetworks are Cytoscape collections stored in
NDEx.

-  **node**: node object or node id
-  **attribute\_name**: attribute name

**get\_node\_attributes(node)**

Get the attribute objects of a node, where the node may be specified by
its id or passed in as an object.

-  **node**: node object or node id

**get\_nodes()**

Returns an iterator over node ids as keys and node objects as values.

**Edges**
~~~~~~~~~

**create\_edge(source, target, interaction)**

Create a new edge in the network by specifying source-interaction-target

-  **source**: The source node this edge, either its id or the node
   object itself.
-  **target**: The target node this edge, either its id or the node
   object itself.
-  **interaction**: The interaction that describes the relationship
   between the source and target nodes

**add\_edge(edge)**

Add an edge object to the network.

-  **edge**: An edge object (nicecxModel.cx.aspects.EdgesElement)

**set\_edge\_attribute(edge, attribute\_name, values, type=None,
subnetwork=None)**

Set the value(s) of attribute of an edge, where the edge may be
specified by its id or passed in an object.

-  **name**: attribute name
-  **values**: the values of the attribute
-  **type**: the datatype of the attribute values, defaults to the
   python datatype of the values.
-  **subnetwork**: the id of the subnetwork to which this attribute
   applies.

**get\_edge\_attribute(edge, attribute\_name, subnetwork=None)**

Get the value(s) of an attribute of an edge, where the edge may be
specified by its id or passed in as an object.

-  **edge**: edge object or edge id
-  **attribute\_name**: attribute name
-  **subnetwork**: the id of the subnetwork (if any) to which this
   attribute was applied.

**get\_edge\_attribute\_objects(edge, attribute\_name)**

Get the attribute objects for an edge attribute name, where the edge may
be specified by its id or passed in as an object. The edge attribute
objects include datatype and subnetwork information. An example of
networks that include subnetworks are Cytoscape collections stored in
NDEx.

-  **edge**: node object or node id
-  **attribute\_name**: attribute name

**get\_edge\_attributes(edge)**

Get the attribute objects of an edge, where the edge may be specified by
its id or passed in as an object.

-  **edge**: edge object or edge id

**get\_edges()**

Returns an iterator over edge ids as keys and edge objects as values.

**Network**
~~~~~~~~~~~

**get\_name()**

Get the network name

**set\_name(network\_name)**

Set the network name

**getSummary()**

Get a network summary

**set\_network\_attribute(name=None, values=None, type=None,
subnetwork\_id=None)**

Set an attribute of the network

-  **name**: attribute name
-  **values**: the values of the attribute
-  **type**: the datatype of the attribute values
-  **subnetwork**: the id of the subnetwork (if any) to which this
   attribute applies.

**get\_network\_attribute(attribute\_name, subnetwork\_id=None)**

Get the value of a network attribute

-  **attribute\_name**: attribute name
-  **subnetwork**: the id of the subnetwork (if any) to which this
   attribute was applied.

**get\_network\_attribute\_objects(attribute\_name)**

Get the attribute objects for the network. The attribute objects include
datatype and subnetwork information. An example of networks that include
subnetworks are Cytoscape collections stored in NDEx.

**get\_network\_attributes()**

Get the attribute objects of the network.

**get\_metadata()**

-  Get the network metadata

**set\_metadata()**

-  Set the network metadata

**getProvenance()**

-  Get the network provenance as a Python dictionary having the CX
   provenance schema.

**set\_provenance(provenance)**

-  Set the network provenance

**get\_context(context)**

Get the @context aspect of the network, the aspect that maps namespace
prefixes to their defining URIs

**set\_context()**

Set the @context aspect of the network, the aspect that maps namespace
prefixes to their defining URIs

**get\_opaque\_aspect(aspect\_name)**

Get the elements of the aspect specified by aspect\_name
(nicecxModel.cx.aspects.AspectElement)

-  **aspect\_name**: the name of the aspect to retrieve.

**set\_opaque\_aspect(aspect\_name, aspect\_elements)**

Set the aspect specified by aspect\_name to the list of aspect elements.
If aspect\_elements is None, the aspect is removed.
(nicecxModel.cx.aspects.AspectElement)

**get\_opaque\_aspect\_names()**

-  Get the names of all opaque aspects

**I/O**
~~~~~~~

**to\_cx()**

-  Return the CX corresponding to the network.

**to\_cx\_stream()**

Returns a stream of the CX corresponding to the network. Can be used to
post to endpoints that can accept streaming inputs

**to\_networkx()**

Return a NetworkX graph based on the network. Elements in the
CartesianCoordinates aspect of the network are transformed to the
NetworkX **pos** attribute.

**to\_pandas\_dataframe()**

Export the network as a Pandas DataFrame.

Example:
my\_niceCx.upload\_to(uuid=’34f29fd1-884b-11e7-a10d-0ac135e8bacf’,
server='http://test.ndexbio.org', username='myusername',
password='mypassword')

**upload(ndex\_server, username, password, update\_uuid=None)**

Upload the network to the specified NDEx server to the account specified
by username and password, return the UUID of the network on NDEx.

Example: my\_niceCx.upload\_to('http://test.ndexbio.org', 'myusername',
'mypassword')

-  server: The NDEx server to upload the network to.
-  username: The username of the account to store the network
-  password: The password for the account.
-  update\_uuid: Instead of creating a new network, update the network
   that has this UUID with the content of this NiceCX object.

**apply\_template(server, username, password, uuid)**

Get a network from NDEx, copy its cytoscapeVisualProperties aspect to
this network.

-  **server**: The ndex server host of the network from which the layout
   will be copied
-  **username**: Optional username to enable access to a private network
-  **password**: Optional password to enable access to a private network
-  **uuid**: The unique identifier of the network from which the layout
   will be copied

to be undocumented...
=====================

\*\*any method that works with CX JSON will be an undocumented function
for internal use

**addNode(json\_obj=None)**

Used to add a node to the network.

-  **name**: Name for the node

-  **represents**: The representation for the node. This can be used to
   store the normalized id for the node

-  **json\_obj**: The cx representation of a node

**add\_edge\_element(json\_obj=None, edge)** Low level function

-  **json\_obj**: The cx representation of an edge

**addNetworkAttribute(json\_obj=None)**
