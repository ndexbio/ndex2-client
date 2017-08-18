__author__ = 'aarongary'

import json
from ..aspects.AbstractAttributesAspectElement import AbstractAttributesAspectElement

class AbstractElementAttributesAspectElement(AbstractAttributesAspectElement):
    def __init__(self, subnetwork=None, property_of=None, name=None, values=None, type=None):
        super(AbstractAttributesAspectElement, self).__init__(subnetwork=subnetwork, name=name, values=values, type=type)
        self.ATTR_PROPERTY_OF = 'po'
        self._property_of = property_of

    def getPropertyOf(self):
        return self._property_of

    def setPropertyOf(self, id):
        self._property_of = id

    def __str__(self):
        aspect_name = self.getAspectName()
        return_dict = {aspect_name: {}}

        return_dict[aspect_name]['po'] = self._property_of
        return_dict[aspect_name]['name'] = self._name
        if self._subnetwork is not None:
            return_dict[aspect_name]['subnetwork'] = self._property_of

        if self.isSingleValue():
            return_dict[self.getAspectName()]['value'] = self.getValues()
        else:
            return_dict[self.getAspectName()]['value'] = self._values

        return_dict[self.getAspectName()]['data type'] = self._data_type.__str__()

        return json.dumps(return_dict)



