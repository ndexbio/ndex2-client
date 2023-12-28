Converting CX2Network objects to other formats
==========================================================================

Below are converters that facilitate conversion of
:class:`~ndex2.cx2.CX2Network` object to other types
(such as NetworkX_ or Pandas_)


Networkx
-----------

The :class:`~ndex2.cx2.CX2NetworkXFactory` is used for generating a
:py:class:`networkx.Graph` from a :class:`~ndex2.cx2.CX2Network`. This is
beneficial for leveraging NetworkX_ functionalities with CX2Network data.


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

    # Creating a NetworkX graph from CX2Network
    networkx_graph = factory.get_graph(cx2_network)

    # networkx_graph is now a NetworkX graph populated with data from cx2_network
    print(networkx_graph.nodes(data=True))

.. note::

    Ids of nodes will correspond to internal Node Ids in CX2Network.
    Node coordinates will be added as attributes named ``x``, ``y``, ``z``

Pandas
--------

Utilize the :py:class:`~ndex2.cx2.CX2NetworkPandasDataFrameFactory` to convert a
:class:`~ndex2.cx2.CX2Network` into a Pandas_ :py:class:`pandas.DataFrame` as an
edgelist table. This allows for analysis and manipulation of network data using Pandas_.

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

.. note::
    At a minimum there will be two columns ``source`` and ``target`` which contain
    the internal ids of the source and target nodes for a given edge.
    Node attributes will be put into columns with their attribute names prefixed with
    ``source_`` and ``target_``

.. _NetworkX: https://networkx.org
.. _Pandas: https://pandas.org