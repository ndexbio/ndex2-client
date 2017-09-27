__author__ = 'aarongary'


import json
from model.cx.aspects import ATTRIBUTE_DATA_TYPE
from model.cx import CX_CONSTANTS

class CitationCommon(object):
    def __init__(self, subnetwork=None, citations=None, property_of=None, json_obj=None):
        if json_obj is not None:
            self._property_of = json_obj.get(CX_CONSTANTS.PROPERTY_OF)
            self._subnetwork = json_obj.get(CX_CONSTANTS.EDGE_SOURCE_NODE_ID_OR_SUBNETWORK)
            self._citations = json_obj.get(CX_CONSTANTS.CITATIONS)
        else:
            self._property_of = property_of
            self._subnetwork = subnetwork
            self._citations = citations

        self.ASPECT_NAME = None

    def getPropertyOf(self):
        return self._property_of

    def setPropertyOf(self, id):
        self._property_of = id

    def getSubnetwork(self):
        return self._subnetwork

    def setSubnetwork(self, subnetwork):
        self._subnetwork = subnetwork

    def getCitations(self):
        return self._citations

    def setCitations(self, citations):
        self._citations = citations

    def __str__(self):
        return json.dumps(self.to_json())

    def to_json(self):
        return_dict = {}

        if self._property_of is not None:
            return_dict[CX_CONSTANTS.PROPERTY_OF] = self._property_of

        if self._subnetwork:
            return_dict[CX_CONSTANTS.EDGE_SOURCE_NODE_ID_OR_SUBNETWORK] = self._subnetwork

        if self._citations:
            return_dict[CX_CONSTANTS.CITATIONS] = self._citations

        return return_dict