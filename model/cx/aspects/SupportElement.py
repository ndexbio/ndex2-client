__author__ = 'aarongary'

from model.cx import CX_CONSTANTS
import json

class SupportElement(object):
    def __init__(self, id=None, text=None, citation_id=None, attributes=None, props=None, json_obj=None):
        self.ASPECT_NAME = 'supports'

        if json_obj is None:
            self._text = text
            self._id = id
            self._citation_id = citation_id
            self._attributes = attributes
            self._props = props
        else:
            self._text = json_obj.get(CX_CONSTANTS.TEXT.value)
            self._id = json_obj.get(CX_CONSTANTS.ID.value)
            self._citation_id = json_obj.get(CX_CONSTANTS.CITATION.value)
            self._attributes = json_obj.get(CX_CONSTANTS.ATTRIBUTES.value)
            self._props = json_obj.get(CX_CONSTANTS.PROPERTIES.value)

        self.support_element = {}

    def getText(self):
        return self._text

    def setText(self, text):
        self._text = text

    def getId(self):
        return self._id

    def setId(self, id):
        self._id = id

    def getCitationId(self):
        return self._citation_id

    def setCitationId(self, citation_id):
        self._citation_id = citation_id

    def getAttribute(self):
        return self._attributes

    def setAttributes(self, attibrutes):
        self._attributes = attibrutes

    def getProps(self):
        return self._props

    def setProps(self, props):
        self._props = props

    def __str__(self):
        return json.dumps(self.to_json())

    def to_json(self):
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

