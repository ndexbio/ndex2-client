__author__ = 'aarongary'

import json
from ndex2.cx.aspects import ATTRIBUTE_DATA_TYPE
from ndex2.cx import CX_CONSTANTS
from enum import Enum

class AttributeCommon(object):
    def __init__(self, subnetwork=None, property_of=None, name=None, values=None, type=None, cx_fragment=None):
        if cx_fragment is not None:
            if CX_CONSTANTS.DATA_TYPE in cx_fragment:
                data_type = ATTRIBUTE_DATA_TYPE.fromCxLabel(cx_fragment.get(CX_CONSTANTS.DATA_TYPE))
            else:
                data_type = ATTRIBUTE_DATA_TYPE.convert_to_data_type(cx_fragment.get(CX_CONSTANTS.VALUE))

            self._property_of = cx_fragment.get(CX_CONSTANTS.PROPERTY_OF)
            self._subnetwork = cx_fragment.get(CX_CONSTANTS.EDGE_SOURCE_NODE_ID_OR_SUBNETWORK)
            self._name = cx_fragment.get(CX_CONSTANTS.NAME)
            self._values = cx_fragment.get(CX_CONSTANTS.VALUE)
            self._data_type = data_type
        else:
            self._property_of = property_of
            self._subnetwork = subnetwork
            self._name = name
            self._values = values
            if isinstance(type, Enum):
                self._data_type = type
            elif type is not None:
                self._data_type = ATTRIBUTE_DATA_TYPE.fromCxLabel(type)
            else:
                self._data_type = None

        self.ASPECT_NAME = None

    def get_property_of(self):
        return self._property_of

    def set_property_of(self, id):
        self._property_of = id

    def get_subnetwork(self):
        return self._subnetwork

    def set_subnetwork(self, subnetwork):
        self._subnetwork = subnetwork

    def get_name(self):
        return self._name

    def set_name(self, name):
        self.name = name

    def get_values(self):
        return self._values

    def set_values(self, values):
        self._values = values

    def get_data_type(self):
        return self._data_type

    def set_data_type(self, data_type):
        if isinstance(type, Enum):
            self._data_type = data_type
        elif type is not None:
            self._data_type = ATTRIBUTE_DATA_TYPE.fromCxLabel(data_type)
        else:
            self._data_type = None
        #self._data_type = data_type

    def get_value_as_json_string(self):
        return json.dumps(self._values)

    def is_single_value(self):
        return ATTRIBUTE_DATA_TYPE.isSingleValueType(self._data_type)

    def get_aspect_name(self):
        return self.ASPECT_NAME

    def set_aspect_name(self, aspect_name):
        self.ASPECT_NAME = aspect_name

    def __str__(self):
        return json.dumps(self.to_cx())

    def to_cx(self):
        return_dict = {}

        if self._property_of is not None:
            return_dict[CX_CONSTANTS.PROPERTY_OF] = self._property_of

        if self._name is not None:
            return_dict[CX_CONSTANTS.NAME] = self._name

        if self._data_type:
            return_dict[CX_CONSTANTS.DATA_TYPE] = self._data_type.value

        if self._subnetwork:
            return_dict[CX_CONSTANTS.EDGE_SOURCE_NODE_ID_OR_SUBNETWORK] = self._subnetwork

        if self.is_single_value():
            return_dict[CX_CONSTANTS.VALUE] = self.get_values()
        else:
            return_dict[CX_CONSTANTS.VALUE] = self._values

        return return_dict