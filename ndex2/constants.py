# -*- coding: utf-8 -*-

"""
Contains constants used by the NDEx2 Python Client
"""

VALID_ATTRIBUTE_DATATYPES = [
    'boolean',
    'double',
    'integer',
    'long',
    'string',
    'list_of_boolean',
    'list_of_double',
    'list_of_integer',
    'list_of_long',
    'list_of_string'
]
"""
List of valid attribute data types
"""

CARTESIAN_LAYOUT_ASPECT = 'cartesianLayout'
"""
Name of opaque aspect containing coordinates of nodes
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

NODE_ID = '@id'
"""
Key for id of node
"""

NODE_NAME = 'n'
"""
Key for node name
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
