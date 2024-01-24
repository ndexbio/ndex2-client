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
    :members:

CX2NetworkFactory classes and methods
***************************************

.. autoclass:: ndex2.cx2.CX2NetworkFactory
    :members:

.. autoclass:: ndex2.cx2.NoStyleCXToCX2NetworkFactory
    :members:

.. autoclass:: ndex2.cx2.RawCX2NetworkFactory
    :members:

.. autoclass:: ndex2.cx2.NetworkXToCX2NetworkFactory
    :members:

.. autoclass:: ndex2.cx2.PandasDataFrameToCX2NetworkFactory
    :members:

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