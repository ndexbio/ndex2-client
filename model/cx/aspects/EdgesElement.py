__author__ = 'aarongary'

from . import CX_CONSTANTS

class EdgesElement(object):
    def __init__(self):
        self.ID = CX_CONSTANTS.get('ID')
        self.INTERACTION = 'i'
        self.SOURCE_NODE_ID = 's'
        self.TARGET_NODE_ID = 't'
        self.ASPECT_NAME = 'edges'
