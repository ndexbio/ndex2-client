__author__ = 'aarongary'

from ndex2.cx import CX_CONSTANTS
import json
from ndex2.DecimalEncoder import DecimalEncoder
# TODO - consolidate decimalencoder

class EdgeElement(object):
    def __init__(self, id=None, edge_source=None, edge_target=None, edge_interaction=None, cx_fragment=None):
        self.ASPECT_NAME = 'edges'

        self._source = None
        self._target = None
        self._interaction = None
        self._id = -1

        if id is not None:
            self._id = id

        if edge_source is not None:
            self._source = edge_source

        if edge_target is not None:
            self._target = edge_target

        if edge_interaction is not None:
            self._interaction = edge_interaction

        if cx_fragment is not None:
            if type(cx_fragment) is dict:
                self._source = cx_fragment.get(CX_CONSTANTS.EDGE_SOURCE_NODE_ID_OR_SUBNETWORK)
                self._target = cx_fragment.get(CX_CONSTANTS.EDGE_TARGET_NODE_ID)
                self._interaction = cx_fragment.get(CX_CONSTANTS.EDGE_INTERACTION)
                if cx_fragment.get(CX_CONSTANTS.ID) is not None:
                    self._id = cx_fragment.get(CX_CONSTANTS.ID)
            else:
                raise Exception('EdgesElement json input provided was not of type json object.')

    def get_aspect_name(self):
        return self.ASPECT_NAME

    def get_id(self):
        return self._id

    def set_id(self, id):
        self._id = id

    def get_source(self):
        return self._source

    def set_source(self, source):
        self._source = source

    def get_target(self):
        return self._target

    def set_target(self, target):
        self._target = target

    def get_interaction(self):
        return self._interaction

    def set_interaction(self, interaction):
        self._interaction = interaction

    def __eq__ (self, other):
        return self == other or self._id == other._id

    def __str__(self):
        return json.dumps(self.to_cx(), cls=DecimalEncoder)

    def to_cx(self):
        if self._id == -1:
            raise Exception('Edge element does not have a valid ID.  Unable to process this edge')

        node_dict = {
            CX_CONSTANTS.ID: self._id,
        }

        if self._source is not None:
            node_dict[CX_CONSTANTS.EDGE_SOURCE_NODE_ID_OR_SUBNETWORK] = self._source

        if self._target is not None:
            node_dict[CX_CONSTANTS.EDGE_TARGET_NODE_ID] = self._target

        if self._interaction is not None:
            node_dict[CX_CONSTANTS.EDGE_INTERACTION] = self._interaction

        return node_dict


