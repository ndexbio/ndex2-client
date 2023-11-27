Converting CX2Network objects to other formats
----------------------------------------------------------------

Below are converters that facilitate conversion of
:class:`~ndex2.cx2.CX2Network` object to other types
(such as `NetworkX <https://networkx.org/>`__ or `Pandas <https://pandas.pydata.org>`__)


Creating a `NetworkX <https://networkx.org/>`__ Graph from a CX2Network
==========================================================================

The ``CX2NetworkXFactory`` is used for generating a NetworkX Graph from a ``CX2Network``. This is beneficial for leveraging NetworkX functionalities with CX2Network data.

Example Usage
~~~~~~~~~~~~~

.. code-block:: python

    import networkx as nx
    from ndex2.cx2 import CX2NetworkXFactory, CX2Network

    cx2_network = CX2Network()
    # Populate cx2_network...

    # Creating an instance of CX2NetworkXFactory
    factory = CX2NetworkXFactory()

    # Creating a NetworkX graph from CX2Network
    networkx_graph = factory.get_graph(cx2_network)

    # networkx_graph is now a NetworkX graph populated with data from cx2_network

Creating a `Pandas <https://pandas.pydata.org>`__ DataFrame from a CX2Network
==========================================================================

Utilize the ``PandasDataFrameFactory`` to convert a ``CX2Network`` into a Pandas DataFrame. This allows for analysis and manipulation of network data using Pandas.

Example Usage
~~~~~~~~~~~~~

.. code-block:: python

    import pandas as pd
    from ndex2.cx2 import PandasDataFrameFactory, CX2Network

    cx2_network = CX2Network()
    # Populate cx2_network...

    # Creating an instance of PandasDataFrameFactory
    factory = PandasDataFrameFactory()

    # Converting CX2Network to DataFrame
    df = factory.get_dataframe(cx2_network)

    # df is now a DataFrame representing the CX2Network data

