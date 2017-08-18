__author__ = 'aarongary'

import json
from AbstractElementAttributesAspectElement import AbstractElementAttributesAspectElement

class EdgeAttributesElement(AbstractElementAttributesAspectElement):
    def __init__(self, subnetwork=None, property_of=None, name=None, values=None, type=None):
        super(AbstractElementAttributesAspectElement, self).__init__(subnetwork=subnetwork, property_of=property_of, name=name, values=values, type=type)
        self.ASPECT_NAME = 'nodeAttributes'

