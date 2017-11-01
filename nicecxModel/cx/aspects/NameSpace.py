__author__ = 'aarongary'

import json

class NameSpace():
    def __init__(self):
	    self.serialVersionUID = 1
	    self.ASPECT_NAME = '@context'

    def getAspectName(self):
        return self.ASPECT_NAME

    def compareTo(self, o):
        if o is not None and o.get_aspect_name() is not None and self.getAspectName() is not None:
            if self.getAspectName() > o.get_aspect_name():
                return 1
            elif self.getAspectName() < o.get_aspect_name():
                return -1
            else:
                return 0

	#def write(self, out):
	#	out.writeObject(this);

