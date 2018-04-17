__author__ = 'aarongary'

from ndex2.cx.aspects.AttributeCommon import AttributeCommon


class NetworkAttributesElement(AttributeCommon):
    def __init__(self, property_of=None, name=None, values=None, data_type=None, subnetwork=None):
        super(NetworkAttributesElement, self).__init__(property_of, name, values, data_type, subnetwork)

    def get_aspect_name(self):
        return 'networkAttributes'
