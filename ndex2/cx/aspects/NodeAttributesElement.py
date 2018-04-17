__author__ = 'aarongary'

from ndex2.cx.aspects.AttributeCommon import AttributeCommon


class NodeAttributesElement(AttributeCommon):
    def __init__(self, property_of, name, values=None, data_type=None, subnetwork=None,):
        super(NodeAttributesElement, self).__init__(property_of, name, values, data_type, subnetwork)

    def get_aspect_name(self):
        return 'nodeAttributes'
