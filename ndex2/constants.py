# -*- coding: utf-8 -*-

"""
Contains constants used by the NDEx2 Python Client
"""

BOOLEAN_DATATYPE = 'boolean'
"""
Boolean data type for CX
"""

DOUBLE_DATATYPE = 'double'
"""
Double data type for CX
"""

INTEGER_DATATYPE = 'integer'
"""
Integer data type for CX
"""

LONG_DATATYPE = 'long'
"""
Long data type for CX
"""

STRING_DATATYPE = 'string'
"""
String data type for CX
"""

LIST_OF_BOOLEAN = 'list_of_boolean'
"""
List of Boolean data type for CX
"""

LIST_OF_DOUBLE = 'list_of_double'
"""
List of Double data type for CX
"""

LIST_OF_INTEGER = 'list_of_integer'
"""
List of Integer data type for CX
"""

LIST_OF_LONG = 'list_of_long'
"""
List of Long data type for CX
"""

LIST_OF_STRING = 'list_of_string'
"""
List of String data type for CX
"""


VALID_ATTRIBUTE_DATATYPES = [
    BOOLEAN_DATATYPE,
    DOUBLE_DATATYPE,
    INTEGER_DATATYPE,
    LONG_DATATYPE,
    STRING_DATATYPE,
    LIST_OF_BOOLEAN,
    LIST_OF_DOUBLE,
    LIST_OF_INTEGER,
    LIST_OF_LONG,
    LIST_OF_STRING
]
"""
List of valid attribute data types
"""

VALID_ATTRIBUTE_DATATYPES_PLUS_SHORT = VALID_ATTRIBUTE_DATATYPES + [
    'str',
    'int',
    'bool',
    'float'
]

CARTESIAN_LAYOUT_ASPECT = 'cartesianLayout'
"""
Name of opaque aspect containing coordinates of nodes

.. code-block:: text

    "cartesianLayout": [ 
        {
            "node": 0,
            "x": 25.0,
            "y": 50.0
        }, {
            "node": 1,
            "x": -10.0,
            "y": -200.0
        }
    ]
    
.. note::

   Although the name implies a cartesian coordinate system,
   that is actually wrong. The Y access is inverted so lower 
   values of Y are rendered higher on a graph. 0,0 is considered
   upper left corner, but negative values are allowed 
"""

NET_ATTR_NAME = 'n'
"""
Key for network attribute name
"""

NET_ATTR_VALUE = 'v'
"""
Key for network attribute value
"""

EDGE_ID = '@id'
"""
Key for id of edge
"""

EDGE_SOURCE = 's'
"""
Key for edge source
"""

EDGE_TARGET = 't'
"""
Key for edge target
"""

EDGE_INTERACTION = 'i'
"""
Key for edge interaction
"""

EDGE_INTERACTION_EXPANDED = 'interaction'
"""
Expanded key for edge interaction
"""

NODE_ID = '@id'
"""
Key for id of node
"""

NODE_NAME = 'n'
"""
Key for node name
"""

NODE_NAME_EXPANDED = 'name'
"""
Expanded key for node name
"""

NODE_ATTR_NAME = 'n'
"""
Key for node attribute name
"""

NODE_REPRESENTS = 'r'
"""
Key for node represents
"""

NODE_ATTR_PROPERTYOF = 'po'
"""
Key for node property of
"""

NODE_ATTR_VALUE = 'v'
"""
Key for node attribute value
"""

NODE_ATTR_DATATYPE = 'd'
"""
Key for node attribute data type
"""

LAYOUT_NODE = 'node'
"""
Key for node id in :py:const:`CARTESIAN_LAYOUT_ASPECT` 
opaque aspect
"""
LAYOUT_X = 'x'
"""
Key for X coordinate in :py:const:`CARTESIAN_LAYOUT_ASPECT` 
opaque aspect
"""

LAYOUT_Y = 'y'
"""
Key for Y coordinate in :py:const:`CARTESIAN_LAYOUT_ASPECT` 
opaque aspect
"""

LAYOUT_Z = 'z'
"""
Key for Z coordinate in :py:const:`CARTESIAN_LAYOUT_ASPECT` 
opaque aspect
"""

NODES_ASPECT = 'nodes'
"""
Key for nodes attribute
"""

EDGES_ASPECT = 'edges'
"""
Key for nodes attribute
"""

ATTR_DATATYPE = 'd'
"""
Key for attribute data type
"""

ATTR_NAME = 'n'
"""
Key for attribute name
"""

ASPECT_ID = 'id'
"""
Key for aspect ID
"""

ASPECT_VALUES = 'v'
"""
Key for aspect values
"""

