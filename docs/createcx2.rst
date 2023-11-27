Creating a CX2Network objects
------------------------------

Below are factories that facilitate creation of CX2Network objects in different ways:
from raw CX2 data, `NetworkX <https://networkx.org/>`__ graphs, and `Pandas <https://pandas.pydata.org>`__ dataframes.

Creating a CX2Network from Raw CX2 Data
==========================================

The ``RawCX2NetworkFactory`` is designed to create a ``CX2Network`` instance directly from raw CX2 data.

Example Usage
~~~~~~~~~~~~~

.. code-block:: python

    from ndex2.cx2 import RawCX2NetworkFactory, CX2Network

    # Sample raw CX2 data
    raw_cx2_data = {...}  # Replace with actual raw CX2 data

    # Creating an instance of RawCX2NetworkFactory
    factory = RawCX2NetworkFactory()

    # Creating a CX2Network from raw CX2 data
    cx2_network = factory.get_cx2network(raw_cx2_data)

    # cx2_network is now a populated CX2Network instance

Creating a CX2Network from a NetworkX Graph
===============================================

The ``NetworkXToCX2NetworkFactory`` is designed to convert a NetworkX graph into a ``CX2Network``. This conversion is suitable for transferring network data from NetworkX to the CX2 format.

Example Usage
~~~~~~~~~~~~~

.. code-block:: python

    import networkx as nx
    from ndex2.cx2 import NetworkXToCX2NetworkFactory, CX2Network

    # Sample NetworkX graph
    networkx_graph = nx.Graph()
    # Add nodes and edges to networkx_graph...

    # Creating an instance of NetworkXToCX2NetworkFactory
    factory = NetworkXToCX2NetworkFactory()

    # Converting NetworkX graph to CX2Network
    cx2_network = factory.get_cx2network(networkx_graph)

    # cx2_network is now a CX2Network instance representing the NetworkX graph



Creating a CX2Network from a Pandas DataFrame
===============================================

The ``PandasDataFrameToCX2NetworkFactory`` enables the conversion of a Pandas DataFrame into a ``CX2Network``. This is useful for integrating DataFrame data into the CX2 network structure.

Example Usage
~~~~~~~~~~~~~

.. code-block:: python

    import pandas as pd
    from ndex2.cx2 import PandasDataFrameToCX2NetworkFactory, CX2Network

    # Sample Pandas DataFrame
    data = {'source': [...], 'target': [...], ...}  # DataFrame with source, target, and other columns
    df = pd.DataFrame(data)

    # Creating an instance of PandasDataFrameToCX2NetworkFactory
    factory = PandasDataFrameToCX2NetworkFactory()

    # Converting DataFrame to CX2Network
    cx2_network = factory.get_cx2network(df)

    # cx2_network is now a CX2Network instance based on the DataFrame data

Column Naming Convention
~~~~~~~~~~~~~~~~~~~~~~~~

- The columns named ``source`` and ``target`` represent the source and target nodes of each edge, respectively.
- Node attributes are prefixed according to their node type:
  - ``source_`` prefix for attributes of the source node (e.g., ``source_color``).
  - ``target_`` prefix for attributes of the target node (e.g., ``target_size``).
- Edge attributes are directly named after the attribute (e.g., ``weight`` for an edge's weight attribute).
