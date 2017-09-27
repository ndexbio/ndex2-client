__author__ = 'aarongary'

import json
from model.cx.aspects.AttributeCommon import AttributeCommon
from model.cx.aspects.DataModelsUtil import DatamodelsUtil
from model.cx.aspects import ATTRIBUTE_DATA_TYPE

class NetworkAttributesElement(AttributeCommon):
    def __init__(self, subnetwork=None, property_of=None, name=None, values=None, type=None, json_obj=None):
        super(NetworkAttributesElement, self).__init__(subnetwork=subnetwork, property_of=property_of, name=name, values=values, type=type, json_obj=json_obj)
        self.ASPECT_NAME = 'networkAttributes'

    def __str__(self):
        return json.dumps(self.to_json())

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


