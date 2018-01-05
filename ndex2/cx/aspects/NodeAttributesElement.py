__author__ = 'aarongary'

from ndex2.cx.aspects.AttributeCommon import AttributeCommon

class NodeAttributesElement(AttributeCommon):
    def __init__(self, subnetwork=None, property_of=None, name=None, values=None, type=None, cx_fragment=None):
        super(NodeAttributesElement, self).__init__(subnetwork=subnetwork, property_of=property_of, name=name, values=values, type=type, cx_fragment=cx_fragment)
        self.set_aspect_name('nodeAttributes')




