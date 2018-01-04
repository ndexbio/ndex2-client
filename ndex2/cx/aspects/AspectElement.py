__author__ = 'aarongary'

from ndex2.cx import CX_CONSTANTS

class AspectElement(object):
    def __init__(self, element, aspect_name):
        self.serialVersionUID = 1
        self.ASPECT_NAME = aspect_name
        self.aspect_element = element

    def get_aspect_name(self):
        return self.ASPECT_NAME

    def set_aspect_name(self, name):
        self.ASPECT_NAME = name

    def get_aspect_element(self):
        return self.aspect_element

    def set_aspect_element(self, ae):
        self.aspect_element = ae
