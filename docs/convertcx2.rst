Converting CX2Network objects to other formats
==========================================================================

Below are converters that facilitate conversion of
:class:`~ndex2.cx2.CX2Network` object to other types
(such as NetworkX_ or Pandas_)


Networkx
-----------

The :class:`~ndex2.cx2.CX2NetworkXFactory` is a utility class for converting a :class:`~ndex2.cx2.CX2Network` into
a :py:class:`networkx.Graph`. This allows you to seamlessly leverage NetworkX_ for analysis, visualization, and
manipulation of CX2Network data.

Features:

* Converts nodes, edges, and their attributes from a `CX2Network` to a `NetworkX` graph.
* Supports multiple types of NetworkX graphs (e.g., :class:`networkx.MultiDiGraph`, :class:`networkx.DiGraph`).
* Includes layout information (e.g., `x`, `y`, `z` coordinates) either as node attributes or in `G.pos` and `G.zpos` (when `store_layout_in_pos` attribute set to True).
* Retains network-level attributes as graph-level attributes.

.. warning::
    If a CX2Network includes x, y, or z as node attributes and the store_layout_in_pos attribute is not set, these
    attributes will be overwritten by the layout coordinates (x, y, z), resulting in the loss of the original values.
    To prevent this, it is recommended to either rename the x, y, or z attributes or store the layout coordinates in
    G.pos and G.zpos instead.

.. code-block:: python

    import networkx as nx
    from ndex2.cx2 import CX2NetworkXFactory, CX2Network

    cx2_network = CX2Network()

    # Populate cx2_network...
    # setting node_id to 4 to show ids of networkx nodes will match internal ids of
    # nodes in CX2Network
    node_one_id = cx2_network.add_node(node_id=4, attributes={'name': 'node 1', 'age': 5}, x=10, y=20)
    node_two_id = cx2_network.add_node(attributes={'name': 'node 2', 'age': 10}, x=15, y=30)

    cx2_network.add_edge(source=node_one_id, target=node_two_id, attributes={'weight': 0.3})

    # Creating an instance of CX2NetworkXFactory
    factory = CX2NetworkXFactory()

    # Creating a NetworkX graph from CX2Network (store_layout_in_pos is False by default)
    networkx_graph = factory.get_graph(cx2_network)

    # networkx_graph is now a NetworkX graph populated with data from cx2_network
    print(networkx_graph.nodes(data=True))

    # Convert CX2Network to NetworkX graph with layout stored in G.pos
    networkx_graph_with_pos = factory.get_graph(cx2_network, store_layout_in_pos=True)

    # Display layout positions
    print("Positions:", networkx_graph_with_pos.pos)
    print("Z Positions:", networkx_graph_with_pos.zpos)

.. note::

    * Node IDs:
        NetworkX node IDs correspond to the internal node IDs in the `CX2Network`.
    * Coordinate Handling:
        Node coordinates will be added as attributes named ``x``, ``y``, ``z`` if `store_layout_in_pos` is not set. If `store_layout_in_pos`, coordinates will be stored in `G.pos` (x and y) and `G.zpos` (z). Y-coordinates are inverted when stored in `G.pos`.
    * Default Graph Type:
        The factory creates a :class:`networkx.MultiDiGraph` by default. You can provide your own empty graph of any type using the `networkx_graph` parameter.

Pandas
--------

The :py:class:`~ndex2.cx2.CX2NetworkPandasDataFrameFactory` allows for the conversion of a
:class:`~ndex2.cx2.CX2Network` into a Pandas_ :py:class:`pandas.DataFrame`. This provides flexibility for analyzing,
visualizing, and manipulating network data using Pandas.

Features:

* Converts the network into an edge list table with source and target node details.
* Includes edge and node attributes, prefixed with source_ and target_ for clarity.
* Adds node layout coordinates (x, y, z) if available.
* Optionally generates a node list table containing detailed node attributes.

.. code-block:: python

    import pandas as pd
    from ndex2.cx2 import CX2NetworkPandasDataFrameFactory, CX2Network

    cx2_network = CX2Network()

    # Populate cx2_network...
    node_one_id = cx2_network.add_node(attributes={'name': 'node 1', 'age': 5}, x=10, y=20)
    node_two_id = cx2_network.add_node(attributes={'name': 'node 2', 'age': 10}, x=15, y=30)

    cx2_network.add_edge(source=node_one_id, target=node_two_id, attributes={'weight': 0.3})

    # Creating an instance of CX2NetworkPandasDataFrameFactory
    factory = CX2NetworkPandasDataFrameFactory()

    # Converting CX2Network to DataFrame
    df = factory.get_dataframe(cx2_network)

    # df is now a DataFrame representing the CX2Network data
    print(df)

    # Generate a node list table from CX2Network
    node_list_df = factory.get_nodelist_table(cx2_network)

    # Display the node list DataFrame
    print(node_list_df)

.. note::
    At a minimum there will be two columns ``source_id`` and ``target_id`` which contain
    the internal ids of the source and target nodes for a given edge.
    Node attributes will be put into columns with their attribute names prefixed with ``source_`` and ``target_``

.. _NetworkX: https://networkx.org
.. _Pandas: https://pandas.org