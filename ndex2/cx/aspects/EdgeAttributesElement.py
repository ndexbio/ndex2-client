__author__ = 'aarongary'

from ndex2.cx.aspects.AttributeCommon import AttributeCommon


class EdgeAttributesElement(AttributeCommon):
    def __init__(self, property_of, name, values=None, data_type=None, subnetwork=None):
        super(EdgeAttributesElement, self).__init__(property_of=property_of, name=name, values=values,
                                                    data_type=data_type, subnetwork=subnetwork)

    def get_aspect_name(self):
        return 'edgeAttributes'
