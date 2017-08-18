__author__ = 'aarongary'

import json
from AbstractAspectElement import AbstractAspectElement
from ..aspects import ATTRIBUTE_DATA_TYPE

class AbstractAttributesAspectElement(AbstractAspectElement):

    def __init__(self, subnetwork=None, property_of=None, name=None, values=None, type=None):
        super(AbstractAttributesAspectElement, self).__init__(subnetwork=subnetwork, name=name, values=values, type=type)


    def __init__(self, subnetwork=None, property_of=None, name=None, values=None, type=None):
        self._property_of = None

        self.ATTR_NAME = "n";
        self.ATTR_SUBNETWORK = "s";
        self.ATTR_DATA_TYPE = "d";
        self.ATTR_VALUES = "v";

        self._name = name
        self._subnetwork = subnetwork
        if type is not None:
            self._data_type = type
        else:
            self._data_type = ATTRIBUTE_DATA_TYPE.STRING
        self._values = values

    def getPropertyOf(self):
        return self._property_of

    def setPropertyOf(self, id):
        self._property_of = id

    def getName(self):
        return self._name

    def getSubnetwork(self):
        return self._subnetwork

    def getDataType(self):
        return self._data_type

    def getName(self):
        return self._name

    def getValues(self):
        return self._values

    def getValueAsJsonString(self):
    	return json.dumps(self._values)

    def isSingleValue(self):
	  return ATTRIBUTE_DATA_TYPE.isSingleValueType(self._data_type)

    def __str__(self):
        return_dict = {
            self.getAspectName(): {}
        }

        return_dict[self.getAspectName()]['name'] = self._name
        return_dict[self.getAspectName()]['data type'] = self._data_type.__str__()

        if self._subnetwork:
            return_dict[self.getAspectName()]['subnetwork'] = self._subnetwork

        if self.isSingleValue():
            return_dict[self.getAspectName()]['value'] = self.getValues()
        else:
            return_dict[self.getAspectName()]['value'] = self._values

        return json.dumps(return_dict)

