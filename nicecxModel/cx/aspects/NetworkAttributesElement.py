__author__ = 'aarongary'

import json
from nicecxModel.cx.aspects.AttributeCommon import AttributeCommon
from nicecxModel.cx.aspects.DataModelsUtil import DatamodelsUtil
from nicecxModel.cx.aspects import ATTRIBUTE_DATA_TYPE

class NetworkAttributesElement(AttributeCommon):
    def __init__(self, subnetwork=None, property_of=None, name=None, values=None, type=None, cx_fragment=None):
        super(NetworkAttributesElement, self).__init__(subnetwork=subnetwork, property_of=property_of, name=name, values=values, type=type, cx_fragment=cx_fragment)
        self.set_aspect_name('networkAttributes')

