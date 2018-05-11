__author__ = 'aarongary'

import json


class NodeElement(object):

    def __init__(self, node_id, node_name=None, node_represents=None):
        if id is None:
            raise Exception('Node id can not be None')
        self._name = node_name
        self._represents = node_represents
        self._id = node_id

    @staticmethod
    def get_aspect_name():
        return 'nodes'

    def get_id(self):
        return self._id

    def set_id(self, node_id):
        self._id = node_id

    def get_node_represents(self):
        return self._represents

    def set_node_represents(self, represents):
        self._represents = represents

    def get_name(self):
        return self._name

    def set_name(self, node_name):
        self._name = node_name

    def __eq__(self, other):
        return self == other or self._id == other._id

    def to_cx_str(self):
        return '{"@id":' + str(self._id) + \
               (',"n":' + json.dumps(self._name) if self._name is not None else "") \
               + (',"r":' + json.dumps(self._represents) if self._represents is not None else "") + '}'
