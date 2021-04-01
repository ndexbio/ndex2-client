Converting NiceCXNetwork objects to other formats
----------------------------------------------------------------

Below are converters that facilitate conversion of
:class:`~ndex2.nice_cx_network.NiceCXNetwork` object to other types
(such as `NetworkX <https://networkx.org/>`__)

`Networkx <https://networkx.org/>`__
=======================================

.. autoclass:: ndex2.nice_cx_network.DefaultNetworkXFactory
    :members: get_graph

This networkx converter is still callable, but has been deprecated

.. autoclass:: ndex2.nice_cx_network.LegacyNetworkXVersionTwoPlusFactory
    :members: get_graph

**Base class for `Networkx <https://networkx.org/>`__ converters above**

.. autoclass:: ndex2.nice_cx_network.NetworkXFactory
    :members: add_network_attributes_from_nice_cx_network, add_node, add_edge, copy_cartesian_coords_into_graph