__author__ = 'aarongary'

import json
#from AbstractElementAttributesAspectElement import AbstractElementAttributesAspectElement
from . import ATTRIBUTE_DATA_TYPE
from nicecxModel.cx.aspects.AttributeCommon import AttributeCommon


class EdgeAttributesElement(AttributeCommon):
    def __init__(self, subnetwork=None, property_of=None, name=None, values=None, type=None, cx_fragment=None):
        super(EdgeAttributesElement, self).__init__(subnetwork=subnetwork, property_of=property_of, name=name, values=values, type=type, cx_fragment=cx_fragment)
        self.set_aspect_name('edgeAttributes')






