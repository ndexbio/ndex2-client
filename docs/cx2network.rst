CX2Network
-------------

The :class:`~ndex2.cx2.CX2Network` class represents the `CX2 (Cytoscape Exchange) network format. <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)/>`__

The class provides structured access, manipulation, reading, processing, and writing of network data elements including nodes, edges, attributes, visual properties, and other features of the network.

CX2Network methods
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
    :noindex:

CX2NetworkFactory classes and methods
***************************************

.. autoclass:: ndex2.cx2.CX2NetworkFactory
    :members:
    :noindex:

.. autoclass:: ndex2.cx2.NoStyleCXToCX2NetworkFactory
    :members:
    :noindex:

.. autoclass:: ndex2.cx2.RawCX2NetworkFactory
    :members:
    :noindex:


Supported data types for attributes
************************************

- string
- double
- boolean
- integer
- long
- list_of_string
- list_of_double
- list_of_boolean
- list_of_integer
- list_of_long

Example
********

.. code-block:: python

    import json
    from ndex2.cx2 import CX2Network

    net = CX2Network()
    net.create_from_raw_cx2('path_to_your_cx2_file.cx2')
    net.write_as_raw_cx2('output_path.cx2')

