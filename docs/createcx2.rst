Creating CX2Network objects
==========================================

Below are factories that facilitate creation of :py:class:`~ndex2.cx2.CX2Network`
objects in different ways:

Raw CX2
---------

The :py:class:`~ndex2.cx2.RawCX2NetworkFactory` is designed to create a
:py:class:`~ndex2.cx2.CX2Network` instance directly from raw `CX2 data`_.


.. code-block:: python

    from ndex2.cx2 import RawCX2NetworkFactory, CX2Network

    # Sample raw CX2 data
    raw_cx2_data = {...}  # Replace with actual raw CX2 data

    # Creating an instance of RawCX2NetworkFactory
    factory = RawCX2NetworkFactory()

    # Creating a CX2Network from raw CX2 data
    cx2_network = factory.get_cx2network(raw_cx2_data)

    # cx2_network is now a populated CX2Network instance

NetworkX
----------

The :py:class:`~ndex2.cx2.NetworkXToCX2NetworkFactory` is designed to convert a
NetworkX_ graph into a :py:class:`~ndex2.cx2.CX2Network`.
This conversion is suitable for transferring network data from NetworkX_ to the CX2_ format.


.. code-block:: python

    import networkx as nx
    from ndex2.cx2 import NetworkXToCX2NetworkFactory, CX2Network

    # Add nodes and edges to networkx_graph...
    networkx_graph = nx.Graph()
    networkx_graph.add_node(1, size=5)
    networkx_graph.add_node(2, size=6)
    networkx_graph.add_node(3, size=7)
    networkx_graph.add_edge(1, 2) weight=1.0)
    networkx_graph.add_edge(2, 3, weight=0.9)

    # Creating an instance of NetworkXToCX2NetworkFactory
    factory = NetworkXToCX2NetworkFactory()

    # Converting NetworkX graph to CX2Network
    cx2_network = factory.get_cx2network(networkx_graph)

    # cx2_network is now a CX2Network instance representing the NetworkX graph
    print(cx2_network.to_cx2())


Pandas
-------

The :py:class:`~ndex2.cx2.PandasDataFrameToCX2NetworkFactory` enables the conversion
of a :py:class:`pandas.DataFrame` into a :py:class:`~ndex2.cx2.CX2Network`.
This is useful for integrating :py:class:`pandas.DataFrame` data into the CX2_ network
structure.


.. code-block:: python

    import pandas as pd
    from ndex2.cx2 import PandasDataFrameToCX2NetworkFactory, CX2Network

    # DataFrame with source, target, and other columns
    data = {'source': [1, 2], 'target': [2, 3],
            'weight': [1.0, 0.9],
            'source_size': [5, 6], 'target_size': [6, 7]}
    df = pd.DataFrame(data)

    # Creating an instance of PandasDataFrameToCX2NetworkFactory
    factory = PandasDataFrameToCX2NetworkFactory()

    # Converting DataFrame to CX2Network
    cx2_network = factory.get_cx2network(df, source_id='source', target_id='target')

    # cx2_network is now a CX2Network instance based on the DataFrame data
    print(cx2_network.to_cx2())



Column Naming Convention
~~~~~~~~~~~~~~~~~~~~~~~~

-  Source and target nodes of an edge.
    By default, the columns ``source_name`` and ``target_name`` represent the names of the source and target nodes,
    respectively and ``source_id`` and ``target_id`` represent the unique identifiers for the source and target nodes.

    It can be changed by setting the parameter ``source_field`` and ``target_field`` to column names containing source/ target
    names, and ``source_id`` and ``target_id`` to column names containing source/target ids. Specifying ids is not necessary.

-  Node attributes.
    Node attributes can be specified with a prefix according to their node type:
        - Use the ``source_`` prefix for attributes of the source node (e.g., ``source_color``).
        - Use the ``target_`` prefix for attributes of the target node (e.g., ``target_size``).

    They can also be explicitly specified as a list passed in parameter ``source_node_attr`` for edge source node
    and ``target_node_attr`` for edge target node. The same columns can be used for both source and target node
    attributes (e.g. ``source_node_attr=['color', 'size']`` and ``target_node_attr=['color', 'size']``).

-  Edge attributes.
    Edge attributes should be directly named (e.g., ``weight`` for an edge's weight attribute).

    The ``edge_interaction`` parameter defines the default interaction type for edges. If not specified in the data frame as edge attribute,
    this default value is used. If not set, the default interaction is set to ``interacts-with``.

Example with column names passed as parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import pandas as pd
    from ndex2.cx2 import PandasDataFrameToCX2NetworkFactory

    # DataFrame with custom column names for nodes and attributes
    data = {'Protein 1': ['NodeA', 'NodeB'], 'Protein 2': ['NodeB', 'NodeC'],
            'node_id1': [100, 200], 'node_id2': [200, 300], 'connection_strength': [0.8, 0.7],
            'color': ['red', 'red'], 's_size': [1, 2], 't_size': [2, 1]}
    df = pd.DataFrame(data)

    # Creating an instance of PandasDataFrameToCX2NetworkFactory
    factory = PandasDataFrameToCX2NetworkFactory()

    # Creating CX2Network with custom parameters
    cx2_network_custom = factory.get_cx2network(df,
        source_field='Protein 1', target_field='Protein 2',
        source_id='node_id1', target_id='node_id2',
        source_node_attr=['color', 's_size'], target_node_attr=['color', 't_size'],
        edge_interaction='binds-to')

    # cx2_network_custom is now a CX2Network instance with custom settings
    print(cx2_network_custom.to_cx2())

.. warning::
    Please note that if a node is listed both as a source and a target, or appears multiple times either
    as a source or a target, its attributes will be updated to reflect the most recent data entry in the dataframe.
    This means that each node's attributes will correspond to their latest occurrence in the dataset.

    For example, if node 'A' appears in row 1 with the attribute ``color=red``, and then appears again in row 5
    of the dataframe with the attribute ``color=blue``, the attribute color of this node will be updated to blue.

NiceCXNetwork
--------------
See `Convert NiceCXNetwork to CX2Netowrk <convertnicecx.html#cx2net>`_

.. _CX2 data: https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)
.. _CX2: https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)
.. _NetworkX: https://networkx.org