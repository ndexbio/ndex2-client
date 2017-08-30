__author__ = 'aarongary'

from enum import Enum

known_aspects = [
    'nodes',
    'edges',
    'nodeAttributes',
    'edgeAttributes',
    'networkAttributes',
    'provenanceHistory',
    'citations',
    'nodeCitations',
    'edgeCitations',
    'supports',
    'nodeSupports',
    'edgeSupports',
    'cartesianLayout',
    '@context',
    'cyVisualProperties',
    'visualProperties'
    ]

class CX_CONSTANTS(str, Enum):
    ID = '@id'
    NAME = 'n'
    VALUE = 'v'
    NODE_REPRESENTS = 'r'
    EDGE_INTERACTION = 'i'
    EDGE_SOURCE_NODE_ID = 's'
    EDGE_TARGET_NODE_ID = 't'
    PROPERTY_OF = 'po'
    SUBNETWORK = 's'
    DATA_TYPE = 'd'
    CITATION_TITLE = "dc:title"
    CITATION_CONTRIBUTOR = "dc:contributor"
    CITATION_IDENTIFIER = "dc:identifier"
    CITATION_TYPE = "dc:type"
    CITATION_DESCRIPTION = "dc:description"
    ATTRIBUTES = 'attributes'
    TEXT = 'text'
    CITATION = 'citation'
    CITATIONS = 'citations'
    PROPERTIES = 'properties'

    #======================
    # METADATA CONSTANTS
    #======================
    CONSISTENCY_GROUP = 'consistencyGroup'
    ELEMENT_COUNT = 'elementCount'
    ID_COUNTER = 'idCounter'
    LAST_UPDATE = 'lastUpdate'
    METADATA_NAME = 'name'
    VERSION = 'version'
