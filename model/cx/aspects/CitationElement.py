__author__ = 'aarongary'

from model.cx import CX_CONSTANTS
import json

class CitationElement(object):
    def __init__(self, id=None, title=None, contributor=None, identifier=None, type=None, description=None, attributes=None, json_obj=None):
        self.ASPECT_NAME = 'citations'

        if json_obj is None:
            self._id = id
            self._title = title
            self._contributor = contributor
            self._identifier = identifier
            self._type = type
            self._description = description
            self._attributes = attributes
        else:
            self._id = json_obj.get(CX_CONSTANTS.ID)
            self._title = json_obj.get(CX_CONSTANTS.CITATION_TITLE)
            self._contributor = json_obj.get(CX_CONSTANTS.CITATION_CONTRIBUTOR)
            self._identifier = json_obj.get(CX_CONSTANTS.CITATION_IDENTIFIER)
            self._type = json_obj.get(CX_CONSTANTS.CITATION_TYPE)
            self._description = json_obj.get(CX_CONSTANTS.CITATION_DESCRIPTION)
            self._attributes = json_obj.get(CX_CONSTANTS.ATTRIBUTES)

    def getId(self):
        return self._id

    def getTile(self):
        return self._title

    def getContributor(self):
        return self._title

    def getIdentifier(self):
        return self._title

    def getType(self):
        return self._title

    def getDescription(self):
        return self._title

    def getAttributes(self):
        return self._title

    def setTile(self, title):
        self._title = title

    def setContributor(self, contributor):
        self._contributor = contributor

    def setIdentifier(self, identifier):
        self._identifier = identifier

    def setType(self, type):
        self._type = type

    def setDescription(self, description):
        self._description = description

    def setAttributes(self, attributes):
        self._attributes = attributes

    def __str__(self):
        return json.dumps(self.to_json())

    def to_json(self):
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

