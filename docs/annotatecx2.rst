Annotating CX2Network objects
===============================

The :class:`~ndex2.cx2.CX2Network` objects can be annotated by adding attributes to the network, its nodes, and edges.

This is especially useful for constructing representations like the Hierarchical Network Schema (HCX_) from
hierarchical ``CX2Network`` data.

Network Annotation
------------------

To annotate the network, i.e add attributes to the network,
use the :py:func:`~ndex2.cx2.CX2Network.add_network_attribute` method.

**Example:**

.. code-block:: python

    from ndex2.cx2 import CX2Network

    cx2_network = CX2Network()
    rocrate_id = 0
    cx2_network.add_network_attribute('name', 'my cx2 network')
    cx2_network.add_network_attribute(key='description', value='the description of my network')
    cx2_network.add_network_attribute('version', 1, datatype='integer')
    # It can be used to add FAIRSCAPE annotations:
    cx2_network.add_network_attribute('prov:wasDerivedFrom', 'RO-crate: ' + str(rocrate_id))

    print(cx2_network.get_network_attributes())

Output:

.. code-block:: json

      {
        "networkAttributes": [
          {
            "name": "my cx2 network",
            "description": "the description of my network",
            "version": 1,
            "prov:wasDerivedFrom": "RO-crate: 0"
          }
        ]
      }

Node Annotation
---------------

To annotate a specific node, use the :py:func:`~ndex2.cx2.CX2Network.add_node_attribute` method.

**Example:**

.. code-block:: python

    from ndex2.cx2 import CX2Network

    cx2_network = CX2Network()
    cx2_network.add_node(0, attributes={'name': 'node0'})
    cx2_network.add_node(1, attributes={'name': 'node1'})
    cx2_network.add_node_attribute(node_id=0, key='color', value='red')
    cx2_network.add_node_attribute(1, 'color', 'blue')
    cx2_network.add_node_attribute(1, 'name', 'new name for node1')

    print(cx2_network.get_nodes())

Output:

.. code-block:: json

    {
      "nodes": [
        {
          "id": 0,
          "v": {
            "name": "node0",
            "color": "red"
          }
        },
        {
          "id": 1,
          "v": {
            "name": "new name for node1",
            "color": "blue"
          }
        }
      ]
    }


Edge Annotation
---------------

To add attributes to a specific edge, use the :py:func:`~ndex2.cx2.CX2Network.add_edge_attribute` method.

**Example:**

.. code-block:: python

    from ndex2.cx2 import CX2Network

    cx2_network = CX2Network()
    cx2_network.add_node(0, attributes={'name': 'node0'})
    cx2_network.add_node(1, attributes={'name': 'node1'})
    cx2_network.add_edge(edge_id=1234, source=0, target=1, attributes={'interaction': 'binds'})
    cx2_network.add_edge_attribute(edge_id=1234, key='weight', value=0.5, datatype='double')

    print(cx2_network.get_nodes())

Output:

.. code-block:: json

      {
        "edges": [
          {
            "id": 1234,
            "s": 0,
            "t": 1,
            "v": {
              "interaction": "binds",
              "weight": 0.5
            }
          }
        ]
      }

.. _HCX: https://cytoscape.org/cx/cx2/hcx-specification/