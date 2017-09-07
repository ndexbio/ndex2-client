__author__ = 'aarongary'

import json
#from AbstractElementAttributesAspectElement import AbstractElementAttributesAspectElement
from . import ATTRIBUTE_DATA_TYPE
from model.cx.aspects.AttributeCommon import AttributeCommon


class EdgeAttributesElement(AttributeCommon):
    def __init__(self, subnetwork=None, property_of=None, name=None, values=None, type=None, json_obj=None):
        super(EdgeAttributesElement, self).__init__(subnetwork=subnetwork, property_of=property_of, name=name, values=values, type=type, json_obj=json_obj)
        self.setAspectName('edgeAttributes')






