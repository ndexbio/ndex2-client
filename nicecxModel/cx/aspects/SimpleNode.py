__author__ = 'aarongary'

import json

class SimpleNode(object):
    def __init__(self, id=None, node_name=None, node_represents=None):
        self.return_this = {
            'n': node_name,
            '@id': id,
            'r': node_represents
        }

    def __str__(self):
        return json.dumps(self.return_this)
