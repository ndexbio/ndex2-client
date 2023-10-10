CX2Network
-------------

The :class:`~ndex2.cx2.CX2Network` class represents the `CX2 (Cytoscape Exchange) network format. <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)/#edges>`__


The class provides structured access, manipulation, reading, processing, and writing of network data elements including nodes, edges, attributes, visual properties, and other features of the network.

Class and methods
****************************
.. autoclass:: ndex2.cx2.CX2Network
    :members: create_from_raw_cx2, write_as_raw_cx2, to_cx2, _process_attributes, _convert_value, _replace_with_alias
    :noindex:

Supported data types for attributes
=====================

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

**Example**:

.. code-block:: python

    import json
    from cx2_network_class import CX2Network

    net = CX2Network()
    net.create_from_raw_cx2('path_to_your_cx2_file.cx2')
    net.write_as_raw_cx2('output_path.cx2')

