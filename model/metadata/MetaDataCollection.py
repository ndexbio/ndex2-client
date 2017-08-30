__author__ = 'aarongary'
import json
from model.cx import CX_CONSTANTS

class MetaDataElement():
    def __init__(self, elementCount=None, idCounter=None, properties=None, version=None, consistencyGroup=None, lastUpdate=None, name=None, json_obj=None):
        if json_obj is not None:
            self.element_count = json_obj.get(CX_CONSTANTS.ELEMENT_COUNT)
            self.properties = json_obj.get(CX_CONSTANTS.PROPERTIES)
            self.version = json_obj.get(CX_CONSTANTS.VERSION)
            self.consistencyGroup = json_obj.get(CX_CONSTANTS.CONSISTENCY_GROUP)
            self.name = json_obj.get(CX_CONSTANTS.METADATA_NAME)
            self.id_counter = json_obj.get(CX_CONSTANTS.ID_COUNTER)
            self.last_update = json_obj.get(CX_CONSTANTS.LAST_UPDATE)
        else:
            self.element_count = elementCount
            self.properties = properties
            self.version = version
            self.consistencyGroup = consistencyGroup
            self.name = name
            self.id_counter = idCounter
            self.last_update = lastUpdate

    def getConsistencyGroup(self):
        return self.consistencyGroup

    def getElementCount(self):
        return self.elementCount

    def getIdCounter(self):
        return self.id_counter

    def getLastUpdate(self):
        return self.last_update

    def getName(self):
        return self.name

    def getVersion(self):
        return self.version

    def getProperties(self):
        return self.properties

    def setConsistencyGroup(self, cg):
        self.consistencyGroup = cg

    def setElementCount(self, ec):
        self.element_count = ec

    def setIdCounter(self, ic):
        self.id_counter = ic

    def setLastUpdate(self, lu):
        self.last_update = lu

    def setName(self, n):
        self.name = n

    def setVersion(self, v):
        self.version = v

    def toString(self):
        return json.dumps(self._data)


'''

    /**
     * Convenience method to set the name from an AspectElement.
     *
     * @param e an AspectElement (to get the name from)
     */
    public final void setName(final AspectElement e) {
        self._data.put(self.NAME, e.getAspectName());
    }

'''