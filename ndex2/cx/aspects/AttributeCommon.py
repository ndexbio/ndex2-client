__author__ = 'aarongary'

import json
from ndex2.cx.aspects import ATTRIBUTE_DATA_TYPE
from enum import Enum
from abc import ABC, abstractmethod


class AttributeCommon(ABC):
    def __init__(self, property_of, name, values=None, data_type=None, subnetwork=None):
        if name is None:
            raise Exception("name can not be None in attributes.")
        self._property_of = property_of
        self._subnetwork = subnetwork
        self._name = name
        self._values = values
        if isinstance(data_type, Enum):
            self._data_type = data_type
        elif data_type is not None:
            self._data_type = ATTRIBUTE_DATA_TYPE.from_cx_label(data_type)
        else:
            self._data_type = ATTRIBUTE_DATA_TYPE.STRING

    def get_property_of(self):
        return self._property_of

    def set_property_of(self, po):
        self._property_of = po

    def get_subnetwork(self):
        return self._subnetwork

    def set_subnetwork(self, subnetwork):
        self._subnetwork = subnetwork

    def get_name(self):
        return self._name

    def set_name(self, name):
        self._name = name

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
            self._data_type = ATTRIBUTE_DATA_TYPE.from_cx_label(data_type)
        else:
            self._data_type = ATTRIBUTE_DATA_TYPE.STRING

    def get_value_as_json_string(self):
        return json.dumps(self._values)

    def is_single_value(self):
        return ATTRIBUTE_DATA_TYPE.is_single_value_type(self._data_type)

    @abstractmethod
    def get_aspect_name(self):
        pass

    def to_cx_str(self):
        return '{"n":' + json.dumps(self._name) + \
               (',"po":' + str(self._property_of) if self._property_of is not None else "") + \
               (',"s":' + str(self._subnetwork) if self._subnetwork is not None else "") + \
               (',"v":' + json.dumps(self._values) if self._values is not None else "") +\
               ("" if self._data_type == ATTRIBUTE_DATA_TYPE.STRING else ',"d":"' + str(self._data_type.value) + '"') \
               + '}'
