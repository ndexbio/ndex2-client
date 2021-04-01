NiceCXNetwork
-------------

The :class:`~ndex2.nice_cx_network.NiceCXNetwork` class provides a data model for working with NDEx networks
that are stored in `CX format <http://www.home.ndexbio.org/data-model>`__

.. note::

    The term **niceCX** is CX with no duplicate aspects.

Methods are provided to add nodes, edges, node attributes, edge attributes, etc.
Once a :class:`~ndex2.nice_cx_network.NiceCXNetwork` object is populated it can be saved to the `NDEx <https://ndexbio.org>`__ server
by calling either :func:`~ndex2.nice_cx_network.NiceCXNetwork.upload_to()` to create a new network or
:func:`~ndex2.nice_cx_network.NiceCXNetwork.upload_to()` to
update an existing network.

Methods
===========================

Example usage of the methods below can be found in the Jupyter notebook links here:

`Tutorial Notebook <https://github.com/ndexbio/ndex-jupyter-notebooks/blob/master/notebooks/NiceCX%20v2.0%20Tutorial.ipynb>`__
`Navigating NiceCXNetwork Notebook <https://github.com/ndexbio/ndex-jupyter-notebooks/blob/master/notebooks/NiceCX%20v2.0%20navigating%20the%20network.ipynb>`__

Node methods
****************************
.. autoclass:: ndex2.nice_cx_network.NiceCXNetwork
    :members: create_node, get_nodes, get_node_attributes, get_node_attribute, get_node_attribute_value, set_node_attribute,

Edge methods
****************************
.. autoclass:: ndex2.nice_cx_network.NiceCXNetwork
    :members: create_edge, get_edges, get_edge_attributes, get_edge_attribute, get_edge_attribute_value, set_edge_attribute

Network methods
****************************
.. autoclass:: ndex2.nice_cx_network.NiceCXNetwork
    :members: get_context, get_name, get_network_attribute, get_network_attribute_names, get_opaque_aspect, set_context, set_name, set_network_attribute, set_opaque_aspect

Miscellaneous methods
****************************
.. autoclass:: ndex2.nice_cx_network.NiceCXNetwork
    :members: apply_template, apply_style_from_network, print_summary, to_cx, to_cx_stream, to_networkx, to_pandas_dataframe, update_to, upload_to


Supported data types
=====================
The following data types are supported in methods that accept **type**

    Example:

        ``set_edge_attribute(0, 'weight', 0.5, type='double')``


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

These constants are defined here: :py:const:`~ndex2.constants.VALID_ATTRIBUTE_DATATYPES`


