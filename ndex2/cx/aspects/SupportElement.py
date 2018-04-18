__author__ = 'aarongary'

import json


class SupportElement(object):
    def __init__(self, support_id, text=None, citation_id=None, attributes=None):
        self._text = text
        self._id = support_id
        self._citation_id = citation_id
        self._attributes = attributes

    def get_text(self):
        return self._text

    def set_text(self, text):
        self._text = text

    def get_id(self):
        return self._id

    def set_id(self, support_id):
        self._id = support_id

    def get_citation_id(self):
        return self._citation_id

    def set_citation_id(self, citation_id):
        self._citation_id = citation_id

    def get_attribute(self):
        return self._attributes

    def set_attributes(self, attibrutes):
        self._attributes = attibrutes

    @staticmethod
    def get_aspect_name():
        return 'supports'

    def to_cx_str(self):
        return '{"@id":' + self._id + \
               (',"text":' + json.dumps(self._text) if self._text is not None else "") + \
               (',"citation":' + self._citation_id if self._citation_id is not None else "") + \
               (',"attributes":' + self._attributes if self._attributes is not None else "") + '}'
