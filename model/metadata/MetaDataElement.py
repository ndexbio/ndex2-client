__author__ = 'aarongary'
import json
from model.cx import CX_CONSTANTS

class MetaDataElement(object):
    def __init__(self, elementCount=None, idCounter=None, properties=None, version=None, consistencyGroup=1, lastUpdate=None, name=None, json_obj=None):
        print consistencyGroup
        if json_obj is not None:
            self.element_count = json_obj.get(CX_CONSTANTS.ELEMENT_COUNT)
            self.properties = json_obj.get(CX_CONSTANTS.PROPERTIES)
            self.version = json_obj.get(CX_CONSTANTS.VERSION)
            self.consistencyGroup = json_obj.get(CX_CONSTANTS.CONSISTENCY_GROUP)
            self.name = json_obj.get(CX_CONSTANTS.METADATA_NAME)
            self.id_counter = json_obj.get(CX_CONSTANTS.ID_COUNTER)
            self.last_update = json_obj.get(CX_CONSTANTS.LAST_UPDATE)
        else:
            self.element_count = elementCount
            self.properties = properties
            self.version = version
            self.consistencyGroup = consistencyGroup
            self.name = name
            self.id_counter = idCounter
            self.last_update = lastUpdate

    def getConsistencyGroup(self):
        return self.consistencyGroup

    def getElementCount(self):
        return self.elementCount

    def getIdCounter(self):
        return self.id_counter

    def getLastUpdate(self):
        return self.last_update

    def getName(self):
        return self.name

    def getVersion(self):
        return self.version

    def getProperties(self):
        return self.properties

    def setConsistencyGroup(self, cg):
        self.consistencyGroup = cg

    def incrementConsistencyGroup(self):
        raise Exception('metadata should not be incremented')
        if self.consistencyGroup:
            if type(self.consistencyGroup) is int:
                self.consistencyGroup += 1
            else:
                self.consistencyGroup = int(self.consistencyGroup) + 1
        else:
            self.consistencyGroup = 0

    def setElementCount(self, ec):
        self.element_count = ec

    def setIdCounter(self, ic):
        self.id_counter = ic

    def setLastUpdate(self, lu):
        self.last_update = lu

    def setName(self, n):
        self.name = n

    def setVersion(self, v):
        self.version = v

    def __str__(self):
        return json.dumps(self.to_json())

    def to_json(self):
        node_dict = {}

        if self.element_count:
            node_dict[CX_CONSTANTS.ELEMENT_COUNT] = self.element_count

        if self.properties:
            node_dict[CX_CONSTANTS.PROPERTIES] = self.properties

        if self.version:
            node_dict[CX_CONSTANTS.VERSION] = self.version

        #if self.consistencyGroup is not None:
        node_dict[CX_CONSTANTS.CONSISTENCY_GROUP] = self.consistencyGroup

        if self.name:
            node_dict[CX_CONSTANTS.METADATA_NAME] = self.name

        if self.id_counter:
            node_dict[CX_CONSTANTS.ID_COUNTER] = self.id_counter

        if self.last_update:
            node_dict[CX_CONSTANTS.LAST_UPDATE] = self.last_update

        return node_dict
