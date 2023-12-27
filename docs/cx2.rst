CX2Network
-------------

The :class:`~ndex2.cx2.CX2Network` provides a data model for the
`CX2 format`_

The class provides structured access, manipulation, reading, processing, and writing of
network data elements including nodes, edges, attributes, visual properties, and
other features of the network.

The introduction of the `CX2 format`_ represents a significant revision over its predecessor
with several key goals:

- **Simplicity**: The CX2_ data model is designed to be more straightforward and
  user-friendly, enabling easier understanding and utilization by developers.
- **Streaming Efficiency**: CX2_ enhances support for streaming network processing.
  This includes operations like filtering nodes and edges based on properties, and
  converting CX_ networks to other formats, with a significantly reduced memory footprint.
- **Compactness**: The format aims to make CX_ networks more compact, improving data
  transfer speeds and efficiency.


.. versionadded:: 3.6.0

Methods
********************
.. autoclass:: ndex2.cx2.CX2Network
    :members: create_from_raw_cx2, write_as_raw_cx2, to_cx2,
              get_attribute_declarations, set_attribute_declarations, get_network_attributes,
              set_network_attributes, get_name, get_nodes, add_node, get_node, remove_node,
              update_node, get_edges, add_edge, get_edge, remove_edge, update_edge,
              get_visual_properties, set_visual_properties, get_node_bypasses, add_node_bypass,
              get_edge_bypasses, add_edge_bypass, get_opaque_aspects, set_opaque_aspects,
              add_opaque_aspect, get_status, set_status, get_declared_type, get_alias,
              get_aliases, get_default_value, get_default_values

CX2NetworkFactory classes and methods
***************************************

.. autoclass:: ndex2.cx2.CX2NetworkFactory
    :members:

.. autoclass:: ndex2.cx2.NoStyleCXToCX2NetworkFactory
    :members:

.. autoclass:: ndex2.cx2.RawCX2NetworkFactory
    :members:

.. autoclass:: ndex2.cx2.NetworkXToCX2NetworkFactory

CX2Network conversion classes
*******************************

.. autoclass:: ndex2.cx2.CX2NetworkXFactory
    :members:

.. autoclass:: ndex2.cx2.CX2NetworkPandasDataFrameFactory
    :members:

Supported data types
**********************

The following `Attribute Declaration Data Types`_ are
supported under the ``d`` attribute:

* string
* double
* boolean
* integer
* long
* list_of_string
* list_of_double
* list_of_boolean
* list_of_integer
* list_of_long

.. _`CX2 format`: https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)
.. _CX2: https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)
.. _CX: https://cytoscape.org/cx
.. _`Attribute Declaration Data Types`: https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)/#attributedeclarations