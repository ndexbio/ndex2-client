__author__ = 'aarongary'

from ndex2.cx import CX_CONSTANTS
import json

class CitationElement(object):
    def __init__(self, id=None, title=None, contributor=None, identifier=None, type=None, description=None, attributes=None, cx_fragment=None):
        self.ASPECT_NAME = 'citations'

        if cx_fragment is None:
            self._id = id
            self._title = title
            self._contributor = contributor
            self._identifier = identifier
            self._type = type
            self._description = description
            self._attributes = attributes
        else:
            self._id = cx_fragment.get(CX_CONSTANTS.ID)
            self._title = cx_fragment.get(CX_CONSTANTS.CITATION_TITLE)
            self._contributor = cx_fragment.get(CX_CONSTANTS.CITATION_CONTRIBUTOR)
            self._identifier = cx_fragment.get(CX_CONSTANTS.CITATION_IDENTIFIER)
            self._type = cx_fragment.get(CX_CONSTANTS.CITATION_TYPE)
            self._description = cx_fragment.get(CX_CONSTANTS.CITATION_DESCRIPTION)
            self._attributes = cx_fragment.get(CX_CONSTANTS.ATTRIBUTES)

    def get_id(self):
        return self._id

    def get_tile(self):
        return self._title

    def get_contributor(self):
        return self._title

    def get_identifier(self):
        return self._title

    def get_type(self):
        return self._title

    def get_description(self):
        return self._title

    def get_attributes(self):
        return self._title

    def set_tile(self, title):
        self._title = title

    def set_contributor(self, contributor):
        self._contributor = contributor

    def set_identifier(self, identifier):
        self._identifier = identifier

    def set_type(self, type):
        self._type = type

    def set_description(self, description):
        self._description = description

    def set_attributes(self, attributes):
        self._attributes = attributes

    def __str__(self):
        return json.dumps(self.to_cx())

    def to_cx(self):
        return_json = {}

        if self._id == -1:
            raise Exception('Edge element does not have a valid ID.  Unable to process this edge - ' + self._node_name)

        return_json[CX_CONSTANTS.ID] = self._id

        if self._contributor is not None:
            return_json[CX_CONSTANTS.CITATION_CONTRIBUTOR] = self._contributor

        if self._identifier is not None:
            return_json[CX_CONSTANTS.CITATION_IDENTIFIER] = self._identifier

        if self._type is not None:
            return_json[CX_CONSTANTS.CITATION_TYPE] = self._type

        if self._title is not None:
            return_json[CX_CONSTANTS.CITATION_TITLE] = self._title

        if self._description is not None:
            return_json[CX_CONSTANTS.CITATION_DESCRIPTION] = self._description

        if self._attributes is not None:
            return_json[CX_CONSTANTS.ATTRIBUTES] = self._attributes

        return return_json

