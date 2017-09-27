__author__ = 'aarongary'

from model.cx import CX_CONSTANTS
import json

class EdgesElement(object):
    def __init__(self, id=None, edge_source=None, edge_target=None, edge_interaction=None, json_obj=None):
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

        if json_obj is not None:
            if type(json_obj) is dict:
                self._source = json_obj.get(CX_CONSTANTS.EDGE_SOURCE_NODE_ID_OR_SUBNETWORK)
                self._target = json_obj.get(CX_CONSTANTS.EDGE_TARGET_NODE_ID)
                self._interaction = json_obj.get(CX_CONSTANTS.EDGE_INTERACTION)
                if json_obj.get(CX_CONSTANTS.ID) is not None:
                    self._id = json_obj.get(CX_CONSTANTS.ID)
            else:
                raise Exception('EdgesElement json input provided was not of type json object.')

    def getAspectName(self):
        return self.ASPECT_NAME

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id

    def getSource(self):
        return self._source

    def setSource(self, source):
        self._source = source

    def getTarget(self):
        return self._target

    def setTarget(self, target):
        self._target = target

    def getInteraction(self):
        return self._interaction

    def setInteraction(self, interaction):
        self._interaction = interaction

    def __eq__ (self, other):
        return self == other or self._id == other._id

    def __str__(self):
        return json.dumps(self.to_json())

    def to_json(self):
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

