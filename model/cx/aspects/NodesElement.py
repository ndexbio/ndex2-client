__author__ = 'aarongary'

import json
from . import CX_CONSTANTS

class NodesElement(object):
    def __init__(self, id=None, node_name=None, node_represents=None):
        self.ID = CX_CONSTANTS.get('ID')
        self.NODE_NAME = 'n'
        self.NODE_REPRESENTS = 'r'
        self.ASPECT_NAME = 'nodes'

        if id is None:
            self._id = -1
        else:
            self._id = id

        self._node_name = node_name
        self._node_represents = node_represents

    def getAspectName(self):
        return self.ASPECT_NAME

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id

    def getNodeRepresents(self):
        return self._node_represents

    def setNodeRepresents(self, represents):
        self._node_represents = represents

    def setNodeName(self, node_name ):
        self._node_name = node_name

    def __eq__ (self, other):
        return self == other or self._id == other._id

    def __str__(self):
        node_dict = {
            self.ID: self._id,
            self.NODE_NAME: self._node_name,
            self.NODE_REPRESENTS: self._node_represents
        }

        return json.dumps(node_dict)

