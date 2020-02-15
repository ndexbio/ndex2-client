:py:mod:`~ndex2.nice_cx_network` Module
---------------------------------------

The :py:mod:`~ndex2.nice_cx_network` module offers a class
:class:`~ndex2.nice_cx_network.NiceCXNetwork`
which provides a data model for working with NDEx networks
that are stored in CX format.

`Click here for more information about CX format <https://www.home.ndexbio.org/data-model>`_.

.. note::

    The term **niceCX** is CX with no duplicate aspects.


Methods are provided to add nodes, edges, node attributes, edge attributes, etc.
Once a :class:`~ndex2.nice_cx_network.NiceCXNetwork` object is populated it can be saved to the NDEx server
by calling either :func:`~ndex2.nice_cx_network.NiceCXNetwork.upload_to()` to create a new network or
:func:`~ndex2.nice_cx_network.NiceCXNetwork.upload_to()` to
update an existing network.


To see deprecated methods go to `Deprecated and Removed NiceCXNetwork methods`_


Methods for building niceCX
===========================
see also
`this notebook <https://github.com/ndexbio/ndex-jupyter-notebooks/blob/master/notebooks/NiceCX%20v2.0%20Tutorial.ipynb>`_

Node methods
****************************
.. autoclass:: ndex2.nice_cx_network.NiceCXNetwork
    :members: create_node, set_node_attribute

Edge methods
****************************
.. autoclass:: ndex2.nice_cx_network.NiceCXNetwork
    :members: create_edge, set_edge_attribute

Network methods
****************************
.. autoclass:: ndex2.nice_cx_network.NiceCXNetwork
    :members: set_context, set_name, set_network_attribute, set_opaque_aspect

Methods for accessing niceCX properties
========================================
see also
`this notebook <https://github.com/ndexbio/ndex-jupyter-notebooks/blob/master/notebooks/NiceCX%20v2.0%20navigating%20the%20network.ipynb>`_

Node methods
****************************
.. autoclass:: ndex2.nice_cx_network.NiceCXNetwork
    :members: get_node_attribute, get_node_attribute_value, get_node_attributes, get_nodes

Edge methods
****************************
.. autoclass:: ndex2.nice_cx_network.NiceCXNetwork
    :members: get_edge_attribute, get_edge_attribute_value, get_edge_attributes, get_edges

Network methods
****************************
.. autoclass:: ndex2.nice_cx_network.NiceCXNetwork
    :members: get_context, get_name, get_network_attribute, get_network_attribute_names, get_opaque_aspect

Misc niceCX methods
========================================
.. autoclass:: ndex2.nice_cx_network.NiceCXNetwork
    :members: apply_template, apply_style_from_network, print_summary, to_cx, to_cx_stream, to_networkx, to_pandas_dataframe, update_to, upload_to

Conversion of niceCX to other formats
=======================================

There are several classes described below that facilitate conversion of
:class:`~ndex2.nice_cx_network.NiceCXNetwork` object to other types
(such as NetworkX)

Networkx
**********

.. autoclass:: ndex2.nice_cx_network.DefaultNetworkXFactory
    :members: get_graph

Deprecated
************

These networkx converters are still callable, but have been deprecated

.. autoclass:: ndex2.nice_cx_network.LegacyNetworkXVersionTwoPlusFactory
    :members: get_graph


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


.. _NDEx REST Server API: https://www.home.ndexbio.org/using-the-ndex-server-api
.. _CX:  https://home.ndexbio.org/data-model/