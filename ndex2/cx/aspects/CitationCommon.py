__author__ = 'aarongary'


import json


class CitationCommon(object):
    def __init__(self, citations, property_of):
        self._property_of = property_of
        self._citations = citations

    def get_property_of(self):
        return self._property_of

    def set_property_of(self, po):
        self._property_of = po

    def get_citations(self):
        return self._citations

    def set_citations(self, citations):
        self._citations = citations

    def to_cx_str(self):
        return '{"po":' + json.dumps(self._property_of) + ',"citations":'+json.dumps(self._citations) + "}"
