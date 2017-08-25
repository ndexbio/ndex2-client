__author__ = 'aarongary'

import json
#from AbstractElementAttributesAspectElement import AbstractElementAttributesAspectElement
from AttributeCommon import AttributeCommon
from DataModelsUtil import DatamodelsUtil
from . import ATTRIBUTE_DATA_TYPE

class NetworkAttributesElement(AttributeCommon):
    def __init__(self, subnetwork=None, name=None, values=None, type=None):
        super(NetworkAttributesElement.__class__, self).__init__(subnetwork=subnetwork, name=name, values=values, type=type)
        self.ASPECT_NAME = 'networkAttributes'

    def __str__(self):
        return json.dumps(self.to_json())

    def to_json(self):
        return_dict = {}

        return_dict['name'] = self._name
        if self._subnetwork is not None:
            return_dict['subnetwork'] = self._property_of

        if self.isSingleValue():
            return_dict['value'] = self.getValues()
        else:
            return_dict['value'] = self._values

        return_dict['data type'] = self._data_type.__str__()

        return return_dict

    def createInstanceWithSingleValue(self, subnetwork, name, value, type):
        return NetworkAttributesElement(subnetwork, name, DatamodelsUtil.removeParenthesis(value, type), type)

    def createInstanceWithMultipleValues(self, subnetwork, name, values, type):
        return NetworkAttributesElement(subnetwork, name, DatamodelsUtil.parseStringToStringList(values, type), type)

    def createInstanceWithJsonValue(self, subnetwork, name, serializedValue, type):
        if ATTRIBUTE_DATA_TYPE.isSingleValueType(type):
            return NetworkAttributesElement(subnetwork, name, serializedValue, type)
        else:
            try:
                sl = json.loads(serializedValue)

                return NetworkAttributesElement(subnetwork, name, sl, type)
            except Exception as e:
                raise Exception('Failed to load json string to json object %s %s %s' % (str(subnetwork), str(name), str(sl)))


