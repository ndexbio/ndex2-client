__author__ = 'aarongary'

from ndex2.cx import CX_CONSTANTS
import json

class SupportElement(object):
    def __init__(self, id=None, text=None, citation_id=None, attributes=None, props=None, cx_fragment=None):
        self.ASPECT_NAME = 'supports'

        if cx_fragment is None:
            self._text = text
            self._id = id
            self._citation_id = citation_id
            self._attributes = attributes
            self._props = props
        else:
            self._text = cx_fragment.get(CX_CONSTANTS.TEXT.value)
            self._id = cx_fragment.get(CX_CONSTANTS.ID.value)
            self._citation_id = cx_fragment.get(CX_CONSTANTS.CITATION.value)
            self._attributes = cx_fragment.get(CX_CONSTANTS.ATTRIBUTES.value)
            self._props = cx_fragment.get(CX_CONSTANTS.PROPERTIES.value)

        self.support_element = {}

    def get_text(self):
        return self._text

    def set_text(self, text):
        self._text = text

    def get_id(self):
        return self._id

    def set_id(self, id):
        self._id = id

    def get_citation_id(self):
        return self._citation_id

    def set_citation_id(self, citation_id):
        self._citation_id = citation_id

    def get_attribute(self):
        return self._attributes

    def set_attributes(self, attibrutes):
        self._attributes = attibrutes

    def getProps(self):
        return self._props

    def set_props(self, props):
        self._props = props

    def __str__(self):
        return json.dumps(self.to_cx())

    def to_cx(self):
        return_json = {}

        if self._id == -1:
            raise Exception('Edge element does not have a valid ID.  Unable to process this edge - ' + self._node_name)

        return_json[CX_CONSTANTS.ID.value] = self._id

        if self._text is not None:
            return_json[CX_CONSTANTS.TEXT.value] = self._text

        if self._citation_id is not None:
            return_json[CX_CONSTANTS.CITATION_IDENTIFIER.value] = self._citation_id

        if self._attributes is not None and len(self._attributes) > 0:
            return_json[CX_CONSTANTS.ATTRIBUTES.value] = self._attributes

        if self._props is not None and len(self._props) > 0:
            return_json[CX_CONSTANTS.PROPERTIES.value] = self._props

        return return_json

