Quick Tutorial
================

.. _NDEx: https://www.ndexbio.org
.. _NDEx2 Python client: https://pypi.org/ndex2-client
.. _NetworkX: https://networkx.org
.. _`BioGRID: Protein-Protein Interactions (SARS-CoV)`: https://www.ndexbio.org/viewer/networks/669f30a3-cee6-11ea-aaef-0ac135e8bacf
.. _CX2: https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)
.. _`Multi-Scale Integrated Cell (MuSIC) v1`: https://www.ndexbio.org/viewer/networks/7fc70ab6-9fb1-11ea-aaef-0ac135e8bacf

Below are some small, fully runnable, code blocks that show how to download, edit,
and upload networks in `NDEx`_ using CX2_ and the new network data model
:py:class:`~ndex2.cx.CX2Network`

.. note::

    This page was updated with `3.7.0` release of `NDEx2 Python client`_.
    The Legacy Quick Tutorial can be found :doc:`here <legacyquicktutorial>`

Download network from `NDEx`_
-------------------------------

The code block below uses the :py:class:`~ndex2.client.Ndex2` client
to download `BioGRID: Protein-Protein Interactions (SARS-CoV)`_
network from `NDEx`_ as a :py:class:`~ndex2.cx2.CX2Network`

The number of nodes and edges are then printed out and the network is
converted to `NetworkX`_ Graph.


.. code-block:: python

    import json
    import ndex2
    from ndex2.cx2 import RawCX2NetworkFactory, CX2NetworkXFactory

    # Create NDEx2 python client
    client = ndex2.client.Ndex2()

    # Create CX2Network factory
    factory = RawCX2NetworkFactory()

    # Download BioGRID: Protein-Protein Interactions (SARS-CoV) from NDEx
    # https://www.ndexbio.org/viewer/networks/669f30a3-cee6-11ea-aaef-0ac135e8bacf
    client_resp = client.get_network_as_cx2_stream('669f30a3-cee6-11ea-aaef-0ac135e8bacf')

    # Convert downloaded network to CX2Network object
    net_cx = factory.get_cx2network(json.loads(client_resp.content))

    # Display information about network and output 1st 100 characters of CX2
    print('Name: ' + net_cx.get_name())
    print('Number of nodes: ' + str(len(net_cx.get_nodes())))
    print('Number of nodes: ' + str(len(net_cx.get_edges())))
    print(json.dumps(net_cx.to_cx2(), indent=2)[0:100])

    # Create CX2NetworkXFactory
    nxfac = CX2NetworkXFactory()
    # Create Networkx network
    g = nxfac.get_graph(net_cx)

    print('Name: ' + str(g))
    print('Number of nodes: ' + str(g.number_of_nodes()))
    print('Number of edges: ' + str(g.number_of_edges()))
    print('Network annotations: ' + str(g.graph))


Upload new network to `NDEx`_
--------------------------------

The code block below shows how to upload a network that is a
:py:class:`~ndex2.cx2.CX2Network` to `NDEx`_.

.. code-block:: python

    import ndex2
    from ndex2.cx2 import CX2Network

    # Create a test network
    net_cx = CX2Network()

    # Set name of network
    net_cx.set_name('Upload new network to NDEx')

    # Create two nodes and one edge
    node_one_id = net_cx.add_node(attributes={'name': 'node 1'})
    node_two_id = net_cx.add_node(attributes={'name': 'node 2'})

    net_cx.add_edge(source=node_one_id, target=node_two_id, attributes={'interaction': 'link'})

    # Create client, be sure to replace <USERNAME> and <PASSWORD> with NDEx username & password
    client = ndex2.client.Ndex2(username='<USERNAME>', password='<PASSWORD>')

    # Save network to NDEx, value returned is link to raw CX data on server.
    res = client.save_new_cx2_network(net_cx.to_cx2(), visibility='PRIVATE')

    print(res)
    # Example return value:
    # https://www.ndexbio.org/v2/network/4027bead-89f2-11ec-b3be-0ac135e8bacf
    # To view network in NDEx replace 'v3' with 'viewer' like so:
    # https://www.ndexbio.org/viewer/networks/4027bead-89f2-11ec-b3be-0ac135e8bacf


Update network on NDEx_
-------------------------

The code block below shows how to update a network **already** on NDEx_

.. code-block:: python

    import json
    import io
    import ndex2
    from ndex2.client import DecimalEncoder
    from ndex2.cx2 import RawCX2NetworkFactory, CX2NetworkXFactory

    # Create client, be sure to replace <USERNAME> and <PASSWORD> with NDEx username & password
    client = ndex2.client.Ndex2(username='<USERNAME>', password='<PASSWORD>')

    # Create CX2Network factory
    factory = RawCX2NetworkFactory()

    # Download BioGRID: Protein-Protein Interactions (SARS-CoV) from NDEx
    client_resp = client.get_network_as_cx2_stream('<UUID OF NETWORK TO UPDATE>')

    # Convert downloaded network to CX2Network object
    net_cx = factory.get_cx2network(json.loads(client_resp.content))

    # Change networks name
    net_attrs = net_cx.get_network_attributes()
    if 'name' in net_attrs:
        net_attrs['name'] = 'Updated ' + str(net_attrs['name'])
    else:
        net_attrs['name'] = 'Updated network'

    # Update network attributes
    net_cx.set_network_attributes(net_attrs)

    # Create bytes stream
    cx_stream = io.BytesIO(json.dumps(net_cx.to_cx2(),
                                      cls=DecimalEncoder).encode('utf-8'))

    # Update network in NDEx by completely replacing the network with
    # one set in cx_stream
    client.update_cx2_network(cx_stream, '<UUID OF NETWORK TO UPDATE>')

    # NOTE: above call will not return any output


Load CX2 file or CX2-JSON to create CX2 Network
------------------------------------------------

You can load CX2 file via NDEx Python package by passing the file name in `get_cx2network` method.

.. code-block:: python

    import json
    from ndex2.cx2 import RawCX2NetworkFactory

    factory = RawCX2NetworkFactory()

    net = factory.get_cx2network('my_network.cx2')

    print('The nodes')
    for node_id, node in net.get_nodes().items():
        print(node['v']['name'])
    print('The edges')
    for edge_id, edge in net.get_edges().items():
        print(edge['v'])

You can also directly load CX2 in JSON format if you have previously loaded the file.

.. code-block:: python

    import json
    from ndex2.cx2 import RawCX2NetworkFactory

    with open('my_network.cx2', 'r') as f:
        data = json.load(f)

    factory = RawCX2NetworkFactory()
    net = factory.get_cx2network(data)


Add nodes, edges, and attributes to network
-------------------------------------------------

The code block below shows how to add nodes, edges and attributes to
a :py:class:`~ndex2.cx2.CX2Network` object

.. code-block:: python

    import ndex2
    from ndex2.cx2 import CX2Network

    # create an empty CX2Network object
    # a CX2Network could also be downloaded from NDEx or created from CX2 data
    net_cx = ndex2.cx2.CX2Network()

    # create a node, id of node is returned, coordinates x and y set below are optional
    node_one_id = net_cx.add_node(attributes={'name': 'foo',
                                              'altname': 'alternate name for foo',
                                              'represents': 'representing foo'},
                                              x=10, y=0)

    # create another node
    node_two_id = net_cx.add_node(attributes={'name': 'bar',
                                              'altname': 'alternate name for bar',
                                              'represents': 'representing bar'},
                                              x=10, y=10)

    # create an edge connecting the nodes, id of edge is returned
    edge_id = net_cx.add_edge(source=node_one_id, target=node_two_id,
                              attributes={'interaction': 'interacts',
                                          'weight': 0.5})

    net_cx.set_network_attributes({'name': 'test network'})

    print('Name: ' + net_cx.get_name())
    print('Number of nodes: ' + str(len(net_cx.get_nodes())))
    print('Number of edges: ' + str(len(net_cx.get_edges())))


Annotate CX2Network objects
----------------------------------

The :class:`~ndex2.cx2.CX2Network` objects can be annotated by adding attributes to the network, its nodes, and edges.

This is especially useful for constructing representations like the Hierarchical Network Schema (HCX_) from
hierarchical ``CX2Network`` data.

Network Annotation
~~~~~~~~~~~~~~~~~~~

To annotate the network, i.e add attributes to the network,
use the :py:func:`~ndex2.cx2.CX2Network.add_network_attribute` method.

**Example:**

.. code-block:: python

    from ndex2.cx2 import CX2Network

    cx2_network = CX2Network()
    rocrate_id = 0
    cx2_network.add_network_attribute('name', 'my cx2 network')
    cx2_network.add_network_attribute(key='description', value='the description of my network')
    # It can be used to add FAIRSCAPE annotations:
    cx2_network.add_network_attribute('prov:wasDerivedFrom', 'RO-crate: ' + str(rocrate_id))

    print(cx2_network.get_network_attributes())

Output:

.. code-block:: json

    {
        "name": "my cx2 network",
        "description": "the description of my network",
        "prov:wasDerivedFrom": "RO-crate: 0"
    }

Node Annotation
~~~~~~~~~~~~~~~~~~~

To annotate a specific node, use the :py:func:`~ndex2.cx2.CX2Network.add_node_attribute` method.

**Example:**

.. code-block:: python

    from ndex2.cx2 import CX2Network

    cx2_network = CX2Network()
    cx2_network.add_node(0, attributes={'name': 'node0'})
    cx2_network.add_node(1, attributes={'name': 'node1'})
    cx2_network.add_node_attribute(node_id=0, key='color', value='red')
    cx2_network.add_node_attribute(1, 'color', 'blue')
    cx2_network.add_node_attribute(1, 'name', 'new name for node1')

    print(cx2_network.get_nodes())

Output:

.. code-block:: json

    {
      "id": 0,
      "v": {
        "name": "node0",
        "color": "red"
      }
    },
    {
      "id": 1,
      "v": {
        "name": "new name for node1",
        "color": "blue"
      }
    }


Edge Annotation
~~~~~~~~~~~~~~~~~~~

To add attributes to a specific edge, use the :py:func:`~ndex2.cx2.CX2Network.add_edge_attribute` method.

**Example:**

.. code-block:: python

    from ndex2.cx2 import CX2Network

    cx2_network = CX2Network()
    cx2_network.add_node(0, attributes={'name': 'node0'})
    cx2_network.add_node(1, attributes={'name': 'node1'})
    cx2_network.add_edge(edge_id=1234, source=0, target=1, attributes={'interaction': 'binds'})
    cx2_network.add_edge_attribute(edge_id=1234, key='weight', value=0.5, datatype='double')

    print(cx2_network.get_edges())

Output:

.. code-block:: json

    {
        "id": 1234,
        "s": 0,
        "t": 1,
        "v": {
          "interaction": "binds",
          "weight": 0.5
        }
    }

.. _HCX: https://cytoscape.org/cx/cx2/hcx-specification/

Iterate Over Nodes, Edges, and View Attributes
-------------------------------------------------

Once you have downloaded a network from NDEx and converted it into a `CX2Network` object, or created the network yourself,
you can explore its structure by iterating over its nodes and edges, or access and display specific attributes of nodes and edges.

To iterate through the nodes in a `CX2Network` object, you can use the `get_nodes()` method.
This method returns a dictionary where key is node ID and value is the complete node data.

Similarly, you can iterate through the edges using the `get_edges()` method.
This method returns a dictionary where key is edge ID and value is the complete edge data.

Each node or edge in a `CX2Network` object has an attribute dictionary (`'v'`) containing its attributes.
To display the attributes of a node or an edge with a given ID, you can access this dictionary directly.

.. code-block:: python

    import json
    import ndex2
    from ndex2.cx2 import RawCX2NetworkFactory, CX2NetworkXFactory

    # Create NDEx2 python client
    client = ndex2.client.Ndex2()

    # Create CX2Network factory
    factory = RawCX2NetworkFactory()

    # Download BioGRID: Protein-Protein Interactions (SARS-CoV) from NDEx
    # https://www.ndexbio.org/viewer/networks/669f30a3-cee6-11ea-aaef-0ac135e8bacf
    client_resp = client.get_network_as_cx2_stream('669f30a3-cee6-11ea-aaef-0ac135e8bacf')

    # Convert downloaded network to CX2Network object
    net_cx = factory.get_cx2network(json.loads(client_resp.content))

    # Iterate through nodes
    for node_id, node_data in net_cx.get_nodes().items():
        print(f'Node ID: {node_id}, Node Data: {node_data}')

    # Iterate through edges
    for edge_id, edge_data in net_cx.get_edges().items():
        print(f'Edge ID: {edge_id}, Edge Data: {edge_data}')

    # Display attributes of a specific node by ID
    node_id_to_check = 1  # Example node ID
    if node_id_to_check in net_cx.get_nodes():
        print(f'Attributes of node {node_id_to_check}: {net_cx.get_nodes()[node_id_to_check]["v"]}')
    else:
        print(f'Node {node_id_to_check} not found.')

    # Display attributes of a specific edge by ID
    edge_id_to_check = 1  # Example edge ID
    if edge_id_to_check in net_cx.get_edges():
        print(f'Attributes of edge {edge_id_to_check}: {net_cx.get_edges()[edge_id_to_check]["v"]}')
    else:
        print(f'Edge {edge_id_to_check} not found.')


Build a lookup table for node names to node ids
--------------------------------------------------------
The code block below shows how to iterate through nodes in
a :py:class:`~ndex2.cx2.CX2Network` object and build a :py:class:`dict`
of node names to node ids. The network downloaded below is
`Multi-Scale Integrated Cell (MuSIC) v1`_

.. code-block:: python

    import json
    import ndex2
    from ndex2.cx2 import RawCX2NetworkFactory


    # Create NDEx2 python client
    client = ndex2.client.Ndex2()

    # Download MuSIC network from NDEx
    client_resp = client.get_network_as_cx2_stream('7fc70ab6-9fb1-11ea-aaef-0ac135e8bacf')

    # Create CX2Network factory
    factory = RawCX2NetworkFactory()

    # Convert downloaded network to NiceCXNetwork object
    net_cx = factory.get_cx2network(json.loads(client_resp.content))

    node_name_dict = {}

    # Build dictionary and print out all the nodes
    for node_id, node_obj in net_cx.get_nodes().items():
        print('node_id: ' + str(node_id) + ' node_obj: ' + str(node_obj))
        node_name_dict[node_obj['v']['name']] = node_id

    # Print out dictionary
    print(str(node_name_dict))

Convert NiceCXNetwork to CX2Network
-------------------------------------
The :py:class:`~ndex2.cx2.NoStyleCXToCX2NetworkFactory` class provides a straightforward
way to convert an existing :py:class:`~ndex2.nice_cx_network.NiceCXNetwork` object into a
:py:class:`~ndex2.cx2.CX2Network`. It omits the style of the original network.

.. code-block:: python

    from ndex2.nice_cx_network import NiceCXNetwork
    from ndex2.cx2 import NoStyleCXToCX2NetworkFactory

    # Create a NiceCXNetwork object
    nice_cx_network = NiceCXNetwork()

    # Your code to populate nice_cx_network...

    # Creating an instance of NoStyleCXToCX2NetworkFactory
    factory = NoStyleCXToCX2NetworkFactory()

    # Converting NiceCXNetwork to CX2Network without style
    cx2_network = factory.get_cx2network(nice_cx_network)

    # The resulting cx2_network is now a CX2Network object ready for further use

.. note::
    The conversion preserves the network's data, data attributes and structure.

.. warning::
    Be aware that the visual style from the :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
    will not be preserved in the :py:class:`~ndex2.cx2.CX2Network`. This includes any
    node or edge styles, layouts, or color schemes.

Why Convert to CX2Network?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Performance**: Efficient conversion to CX2_ format for improved performance in data processing.
- **Compatibility**: Ensures compatibility with tools and libraries designed for CX2_ format.
                     It allows to generate hierarchy in `HCX format`_ which is compatible
                     with Cytoscape_ Web.
- **New Features**: Leverage new features and functionalities available in the CX2_ format.

.. note::
    `CX version 2`_ is commonly referred to as CX2_. In the Cytoscape_ ecosystem, CX2_ files
    typically carry the ``.cx2`` file extension. This distinguishes them from `CX version 1`_
    networks, which usually use the ``.cx`` suffix.

More Tutorials and Examples
-------------------------------------------------

*  Basic Use of the NDEx2 Python Client:  `NDEx2 Client v2.0
   Tutorial <https://github.com/ndexbio/ndex-jupyter-notebooks/blob/master/notebooks/NDEx2%20Client%20v2.0%20Tutorial.ipynb>`__
*  Working with the NiceCX Network Class: `NiceCX v2.0
   Tutorial <https://github.com/ndexbio/ndex-jupyter-notebooks/blob/master/notebooks/NiceCX%20v2.0%20Tutorial.ipynb>`__

To use these tutorials or if Github isn't showing the above notebooks in the browser, clone the `ndex-jupyter-notebooks
repository <https://github.com/ndexbio/ndex-jupyter-notebooks>`__ to
your local machine and start Jupyter Notebooks in the project directory.

For information on installing and using Jupyter Notebooks, go to
`jupyter.org <https://jupyter.org/>`__

* `Click here <https://github.com/ndexcontent/ndexncipidloader>`__ for example code to load content into `NDEx`_

.. _CX2: https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)
.. _`CX version 2`: https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)
.. _`CX version 1`: https://cytoscape.org/cx/specification/cytoscape-exchange-format-specification-(version-1)
.. _CX: https://cytoscape.org/cx
.. _Cytoscape: https://cytoscape.org
.. _Networkx: https://networkx.org
.. _`HCX format`: https://cytoscape.org/cx/cx2/hcx-specification
.. _Pandas: https://pandas.pydata.org
.. _NDEx: https://www.ndexbio.org
.. _`CX format`: https://cytoscape.org/cx/specification/cytoscape-exchange-format-specification-(version-1)
.. _`CX2 format`: https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)
.. _`NDEx REST Service`: https://home.ndexbio.org/using-the-ndex-server-api