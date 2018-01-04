__author__ = 'aarongary'

import json
from ndex2.cx import CX_CONSTANTS

class NodeElement(object):
    def __init__(self, id=None, node_name=None, node_represents=None, cx_fragment=None):
        self.ASPECT_NAME = 'nodes'

        self._node_name = node_name
        self._node_represents = node_represents
        self._id = None

        if cx_fragment is not None:
            if type(cx_fragment) is dict:
                self._node_name = cx_fragment.get(CX_CONSTANTS.NAME)
                self._node_represents = cx_fragment.get(CX_CONSTANTS.NODE_REPRESENTS)
                if cx_fragment.get(CX_CONSTANTS.ID) is not None:
                    self._id = cx_fragment.get(CX_CONSTANTS.ID)
                else:
                    self._id = self._node_name
            else:
                raise Exception('NodesElement json input provided was not of type json object.')
        else:
            if id is None:
                self._id = node_name
            else:
                self._id = id

    def get_aspect_name(self):
        return self.ASPECT_NAME

    def get_id(self):
        return self._id

    def set_id(self, id):
        self._id = id

    def get_node_represents(self):
        return self._node_represents

    def set_node_represents(self, represents):
        self._node_represents = represents

    def get_name(self):
        return self._node_name

    def set_node_name(self, node_name ):
        self._node_name = node_name

    def __eq__ (self, other):
        return self == other or self._id == other._id

    def __str__(self):
        return json.dumps(self.to_cx())

    def to_cx(self):
        if self._id == -1:
            raise Exception('Edge element does not have a valid ID.  Unable to process this edge - ' + self._node_name)

        node_dict = {
            CX_CONSTANTS.ID: self._id,
            CX_CONSTANTS.NAME: self._node_name
        }

        if self._node_represents is not None:
            node_dict[CX_CONSTANTS.NODE_REPRESENTS] = self._node_represents

        return node_dict



