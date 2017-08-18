__author__ = 'aarongary'

from . import CX_CONSTANTS

class AspectElement():
    def __init__(self):
	    self.serialVersionUID = 1
	    self.ASPECT_NAME = None

    def getAspectName(self):
        return self.ASPECT_NAME

    def setAspectName(self, name):
        self.ASPECT_NAME = name



