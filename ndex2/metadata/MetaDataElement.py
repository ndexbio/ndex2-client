__author__ = 'aarongary'
import json
from ndex2.cx import CX_CONSTANTS

class MetaDataElement(object):
    def __init__(self, elementCount=None, idCounter=None, properties=None, version=None, consistencyGroup=1, lastUpdate=None, name=None, cx_fragment=None):
        if cx_fragment is not None:
            self.element_count = cx_fragment.get(CX_CONSTANTS.ELEMENT_COUNT)
            self.properties = cx_fragment.get(CX_CONSTANTS.PROPERTIES)
            self.version = cx_fragment.get(CX_CONSTANTS.VERSION)
            if cx_fragment.get(CX_CONSTANTS.CONSISTENCY_GROUP):
                self.consistencyGroup = cx_fragment.get(CX_CONSTANTS.CONSISTENCY_GROUP)
            else:
                self.consistencyGroup = 1
            self.name = cx_fragment.get(CX_CONSTANTS.METADATA_NAME)
            self.id_counter = cx_fragment.get(CX_CONSTANTS.ID_COUNTER)
            self.last_update = cx_fragment.get(CX_CONSTANTS.LAST_UPDATE)
        else:
            self.element_count = elementCount
            self.properties = properties
            self.version = version
            self.consistencyGroup = consistencyGroup
            self.name = name
            self.id_counter = idCounter
            self.last_update = lastUpdate

    def get_consistency_group(self):
        return self.consistencyGroup

    def get_element_count(self):
        return self.elementCount

    def get_id_counter(self):
        return self.id_counter

    def get_last_update(self):
        return self.last_update

    def get_name(self):
        return self.name

    def get_version(self):
        return self.version

    def get_properties(self):
        return self.properties

    def set_consistency_group(self, cg):
        self.consistencyGroup = cg

    def increment_consistency_group(self):
        raise Exception('metadata should not be incremented')
        #if self.consistencyGroup:
        #    if type(self.consistencyGroup) is int:
        #        self.consistencyGroup += 1
        #    else:
        #        self.consistencyGroup = int(self.consistencyGroup) + 1
        #else:
        #    self.consistencyGroup = 0

    def set_element_count(self, ec):
        self.element_count = ec

    def set_id_counter(self, ic):
        self.id_counter = ic

    def set_last_update(self, lu):
        self.last_update = lu

    def set_name(self, n):
        self.name = n

    def set_version(self, v):
        self.version = v

    def __str__(self):
        return json.dumps(self.to_cx())

    def to_cx(self):
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

        if isinstance(self.id_counter, int) or isinstance(self.id_counter, str):
            #print(self.id_counter)
            node_dict[CX_CONSTANTS.ID_COUNTER] = self.id_counter
        else:
            try:
                if self.id_counter is not None and self.id_counter == 0:
                    #print(self.id_counter)
                    node_dict[CX_CONSTANTS.ID_COUNTER] = self.id_counter
            except Exception:
                print('Error processing metadata id counter')

        if self.last_update:
            node_dict[CX_CONSTANTS.LAST_UPDATE] = self.last_update

        return node_dict
