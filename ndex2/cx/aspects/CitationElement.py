__author__ = 'aarongary'

import json


class CitationElement(object):
    def __init__(self, po, title=None, contributor=None, identifier=None, dc_type=None,
                 description=None, attributes=None):
        self._id = po
        self._title = title
        self._contributor = contributor
        self._identifier = identifier
        self._type = dc_type
        self._description = description
        self._attributes = attributes

    @staticmethod
    def get_aspect_name():
        return 'citations'

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

    def set_type(self, dc_type):
        self._type = dc_type

    def set_description(self, description):
        self._description = description

    def set_attributes(self, attributes):
        self._attributes = attributes

    def to_cx_str(self):
        return '{"@id":'+str(self._id) + \
               (',"dc:title":'+json.dumps(self._title) if self._title is not None else "") + \
               (',"dc:contributor":' + json.dumps(self._contributor) if self._contributor is not None else "") +\
               (',"dc:identifier":' + json.dumps(self._identifier) if self._identifier is not None else '') + \
               (',"dc:type":' + json.dumps(self._type) if self._type is not None else '') + \
               (',"dc:description":' + json.dumps(self._description) if self._description is not None else '') + \
               (',"attributes":' + json.dumps(self._attributes) if self._attributes is not None else '') + '}'
