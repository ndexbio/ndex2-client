Converting NiceCXNetwork objects to other formats
==================================================

.. note::

    Using the newer data model :py:class:`~ndex2.cx2.CX2Network`
    is encouraged since all networks on NDEx_ can be retrieved in newer `CX2 format`_ via
    the `NDEx REST Service`_

Below are converters that facilitate conversion of
:class:`~ndex2.nice_cx_network.NiceCXNetwork` object to other types

`Networkx <https://networkx.org/>`__
--------------------------------------

.. autoclass:: ndex2.nice_cx_network.DefaultNetworkXFactory
    :members: get_graph

This networkx converter is still callable, but has been deprecated

.. autoclass:: ndex2.nice_cx_network.LegacyNetworkXVersionTwoPlusFactory
    :members: get_graph

**Base class for** `Networkx`_ **converters above**

.. autoclass:: ndex2.nice_cx_network.NetworkXFactory
    :members: add_network_attributes_from_nice_cx_network, add_node, add_edge, copy_cartesian_coords_into_graph

`Pandas`_
-----------

For conversion to `Pandas`_ see
:py:func:`~ndex2.nice_cx_network.NiceCXNetwork.to_pandas_dataframe`

.. _cx2net:

CX2Network
------------

The :py:class:`~ndex2.cx2.NoStyleCXToCX2NetworkFactory` class provides a straightforward
way to convert an existing :py:class:`~ndex2.nice_cx_network.NiceCXNetwork` object into a
:py:class:`~ndex2.cx2.CX2Network`. It intentionally omits the style of the original
network. It is useful in scenarios where only the network's structure and data are
needed without the style information.

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
