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
    cx2_network = factory.get_cx2network(df)

    # cx2_network is now a CX2Network instance based on the DataFrame data
    print(cx2_network.to_cx2())

Column Naming Convention
~~~~~~~~~~~~~~~~~~~~~~~~

- The columns named ``source`` and ``target`` represent the source and target nodes of each edge, respectively.
- Node attributes are prefixed according to their node type:
  - ``source_`` prefix for attributes of the source node (e.g., ``source_color``).
  - ``target_`` prefix for attributes of the target node (e.g., ``target_size``).
- Edge attributes are directly named after the attribute (e.g., ``weight`` for an edge's weight attribute).

NiceCXNetwork
--------------
See `Convert NiceCXNetwork to CX2Netowrk <convertnicecx.html#cx2net>`_

.. _CX2 data: https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)
.. _CX2: https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)
.. _NetworkX: https://networkx.org