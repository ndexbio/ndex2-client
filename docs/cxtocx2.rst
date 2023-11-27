Converting a NiceCXNetwork to a CX2Network
-------------------------------------------

The ``NoStyleCXToCX2NetworkFactory`` class provides a straightforward way to convert an existing ``NiceCXNetwork`` object into a ``CX2Network``. It intentionally omits the style of the original network. It is useful in scenarios where only the network's structure and data are needed without the style information.

Example Usage
~~~~~~~~~~~~~

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
    Be aware that the visual style from the NiceCXNetwork will not be preserved in the CX2Network. This includes any node or edge styles, layouts, or color schemes.

Why Convert to CX2Network?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Performance**: Efficient conversion to CX2 format for improved performance in data processing.
- **Compatibility**: Ensures compatibility with tools and libraries designed for CX2 format. It allows to generate hierarchy in HCX format which is compatible with Cytoscape Web.
- **New Features**: Leverage new features and functionalities available in the CX2 format.

Motivation Behind CX2
~~~~~~~~~~~~~~~~~~~~~~~~

The introduction of the CX2 format represents a significant revision over its predecessor with several key goals:

- **Simplicity**: The CX2 data model is designed to be more straightforward and user-friendly, enabling easier understanding and utilization by developers.
- **Streaming Efficiency**: CX2 enhances support for streaming network processing. This includes operations like filtering nodes and edges based on properties, and converting CX networks to other formats, with a significantly reduced memory footprint.
- **Compactness**: The format aims to make CX networks more compact, improving data transfer speeds and efficiency.

.. note::
    CX version 2 is commonly referred to as CX2. In the Cytoscape ecosystem, CX2 files typically carry the ``.cx2`` file extension. This distinguishes them from CX version 1 networks, which usually use the ``.cx`` suffix.



