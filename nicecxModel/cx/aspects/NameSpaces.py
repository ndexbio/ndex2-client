__author__ = 'aarongary'

import json

class NameSpaces():
    def __init__(self):
	    self.serialVersionUID = 1
	    self.ASPECT_NAME = '@context'

    def getAspectName(self):
        return self.ASPECT_NAME

    def compareTo(self, o):
        if o is not None and o.getAspectName() is not None and self.getAspectName() is not None:
            if self.getAspectName() > o.getAspectName():
                return 1
            elif self.getAspectName() < o.getAspectName():
                return -1
            else:
                return 0

	#def write(self, out):
	#	out.writeObject(this);

