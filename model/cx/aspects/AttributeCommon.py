__author__ = 'aarongary'

import json
from model.cx.aspects import ATTRIBUTE_DATA_TYPE
from model.cx import CX_CONSTANTS

class AttributeCommon(object):
    def __init__(self, subnetwork=None, property_of=None, name=None, values=None, type=None, json_obj=None):
        if json_obj is not None:
            data_type = ATTRIBUTE_DATA_TYPE.convert_to_data_type(json_obj.get(CX_CONSTANTS.VALUE))
            self._property_of = json_obj.get(CX_CONSTANTS.PROPERTY_OF)
            self._subnetwork = json_obj.get(CX_CONSTANTS.EDGE_SOURCE_NODE_ID_OR_SUBNETWORK)
            self._name = json_obj.get(CX_CONSTANTS.NAME)
            self._values = json_obj.get(CX_CONSTANTS.VALUE)
            self._data_type = data_type
        else:
            self._property_of = property_of
            self._subnetwork = subnetwork
            self._name = name
            self._values = values
            self._data_type = type

        self.ASPECT_NAME = None

    def getPropertyOf(self):
        return self._property_of

    def setPropertyOf(self, id):
        self._property_of = id

    def getSubnetwork(self):
        return self._subnetwork

    def setSubnetwork(self, subnetwork):
        self._subnetwork = subnetwork

    def getName(self):
        return self._name

    def setName(self, name):
        self.name = name

    def getValues(self):
        return self._values

    def setValues(self, values):
        self._values = values

    def getDataType(self):
        return self._data_type

    def setDataType(self, data_type):
        self._data_type = data_type

    def getValueAsJsonString(self):
        return json.dumps(self._values)

    def isSingleValue(self):
        return ATTRIBUTE_DATA_TYPE.isSingleValueType(self._data_type)

    def getAspectName(self):
        return self.ASPECT_NAME

    def setAspectName(self, aspect_name):
        self.ASPECT_NAME = aspect_name

    def __str__(self):
        return json.dumps(self.to_json())

    def to_json(self):
        return_dict = {}

        if self._property_of is not None:
            return_dict[CX_CONSTANTS.PROPERTY_OF] = self._property_of

        if self._name is not None:
            return_dict[CX_CONSTANTS.NAME] = self._name

        if self._data_type:
            return_dict[CX_CONSTANTS.DATA_TYPE] = self._data_type.value

        if self._subnetwork:
            return_dict[CX_CONSTANTS.EDGE_SOURCE_NODE_ID_OR_SUBNETWORK] = self._subnetwork

        if self.isSingleValue():
            return_dict[CX_CONSTANTS.VALUE] = self.getValues()
        else:
            return_dict[CX_CONSTANTS.VALUE] = self._values

        return return_dict