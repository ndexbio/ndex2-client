__author__ = 'aarongary'

from . import CX_CONSTANTS

class AspectElement(object):
    def __init__(self, element, aspect_name):
        self.serialVersionUID = 1
        self.ASPECT_NAME = aspect_name
        self.aspect_element = element

    def getAspectName(self):
        return self.ASPECT_NAME

    def setAspectName(self, name):
        self.ASPECT_NAME = name

    def getAspectElement(self):
        return self.aspect_element

    def setAspectElement(self, ae):
        self.aspect_element = ae
