Quick Tutorial
================

Download network from `NDEx <https://ndexbio.org>`__
-------------------------------------------------------

The code block below uses the `NDEx2 Python client <https://pypi.org/ndex2-client>`_ to download
`BioGRID: Protein-Protein Interactions (SARS-CoV) <http://ndexbio.org/viewer/networks/669f30a3-cee6-11ea-aaef-0ac135e8bacf>`_
network from `NDEx <https://ndexbio.org>`_ as a `NiceCXNetwork <https://ndex2.readthedocs.io/en/latest/ndex2.html#nicecxnetwork>`_.

The number of nodes and edges are then printed out and the network is converted to `Networkx <https://networkx.org>`__
object.


.. code-block:: python

    import json
    import ndex2


    # Create NDEx2 python client
    client = ndex2.client.Ndex2()

    # Download BioGRID: Protein-Protein Interactions (SARS-CoV) from NDEx
    # http://ndexbio.org/viewer/networks/669f30a3-cee6-11ea-aaef-0ac135e8bacf
    client_resp = client.get_network_as_cx_stream('669f30a3-cee6-11ea-aaef-0ac135e8bacf')

    # Convert downloaded network to NiceCXNetwork object
    net_cx = ndex2.create_nice_cx_from_raw_cx(json.loads(client_resp.content))

    # Display information about network and output 1st 100 characters of CX
    print('Name: ' + net_cx.get_name())
    print('Number of nodes: ' + str(len(list(net_cx.get_nodes()))))
    print('Number of nodes: ' + str(len(list(net_cx.get_edges()))))
    print(json.dumps(net_cx.to_cx())[0:100])

    # Create Networkx network
    g = net_cx.to_networkx(mode='default')

    print('Name: ' + str(g))
    print('Number of nodes: ' + str(g.number_of_nodes()))
    print('Number of edges: ' + str(g.number_of_edges()))
    print('Network annotations: ' + str(g.graph))


Add nodes, edges, and attributes to network
-------------------------------------------------

The code block below shows how to add nodes, edges and attributes to
a `NiceCXNetwork <https://ndex2.readthedocs.io/en/latest/ndex2.html#nicecxnetwork>`__
object

.. code-block:: python

    import ndex2

    # create an empty NiceCXNetwork object
    # a NiceCXNetwork could also be downloaded from NDEx or created from CX data
    net_cx = ndex2.nice_cx_network.NiceCXNetwork()

    # create a node, id of node is returned
    node_one_id = net_cx.create_node(node_name='foo', node_represents='representing foo')

    # create another node
    node_two_id = net_cx.create_node(node_name='bar', node_represents='representing bar')

    # create an edge connecting the nodes, id of edge is returned
    edge_id = net_cx.create_edge(edge_source=node_one_id, edge_target=node_two_id, edge_interaction='interacts')

    # add attribute named 'altname' to 'foo' node, nothing is returned
    net_cx.set_node_attribute(node_one_id, 'altname', 'alternate name for foo', type='string')

    # add attribute to 'bar' node
    net_cx.set_node_attribute(node_two_id, 'altname', 'alternate name for bar', type='string')

    # add an edge attribute named 'weight' with value of 0.5. Set as string
    # value and then set type.
    net_cx.set_edge_attribute(edge_id, 'weight', '0.5', type='double')

    # Create Networkx network
    g = net_cx.to_networkx(mode='default')

    print('Name: ' + str(g))
    print('Number of nodes: ' + str(g.number_of_nodes()))
    print('Number of edges: ' + str(g.number_of_edges()))
    print('Node annotations: ' + str(g.nodes.data()))
    print('Edge annotations: ' + str(g.edges.data()))


How to build a lookup table for node names to node ids
--------------------------------------------------------
The code block below shows how to iterate through nodes in
a `NiceCXNetwork <https://ndex2.readthedocs.io/en/latest/ndex2.html#nicecxnetwork>`__
object and build a `dict <https://docs.python.org/3/tutorial/datastructures.html#dictionaries>`__
of node names to node ids. The network downloaded below is
`Multi-Scale Integrated Cell (MuSIC) v1 <https://www.ndexbio.org/viewer/networks/7fc70ab6-9fb1-11ea-aaef-0ac135e8bacf>`__

.. code-block:: python

    import ndex2
    import json

    # Create NDEx2 python client
    client = ndex2.client.Ndex2()

    # Download MuSIC network from NDEx
    client_resp = client.get_network_as_cx_stream('7fc70ab6-9fb1-11ea-aaef-0ac135e8bacf')

    # Convert downloaded network to NiceCXNetwork object
    net_cx = ndex2.create_nice_cx_from_raw_cx(json.loads(client_resp.content))

    node_name_dict = {}

    # build dictionary and print out all the nodes
    for node_id, node_obj in net_cx.get_nodes():
        print('node_id: ' + str(node_id) + ' node_obj: ' + str(node_obj))
        node_name_dict[node_obj['n']] = node_id


    # print out dictionary
    print(str(node_name_dict))





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
`jupyter.org <http://jupyter.org/>`__

* `Click here <https://github.com/ndexcontent/ndexncipidloader>`__ for example code to load content into `NDEx`_