__author__ = 'aarongary'
import json

class MetaDataCollection():
    def __init__(self):
        self.NAME = 'metaData'
        self.serialVersionUID = 7233278148613095352
        self._data = []

    def add(self, e):
        self._data.append(e.getData())
        return True

    def addAt(self, position, e):
        self._data.insert(position, e.getData());
        return True

    def addMetaDataElement(self, aspect_name, consistency_group, version, last_update, id_counter, element_count):
        e = MetaDataElement()
        e.setName(aspect_name)
        e.setConsistencyGroup(consistency_group)
        e.setVersion(version)
        e.setLastUpdate(last_update)
        e.setIdCounter(id_counter)
        e.setElementCount(element_count)
        self.add(e)

    def addMetaDataElementFromArray(self, elements, consistency_group, version, last_update, id_counter):
        if elements is not None and len(elements) > 0:
            e = MetaDataElement()
            e.setName(elements[0].getAspectName())
            e.setConsistencyGroup(consistency_group)
            e.setVersion(version)
            e.setLastUpdate(last_update)
            e.setIdCounter(id_counter)
            e.setElementCount(len(elements))
            self.add(e)

    def clear(self):
        del self._data[:]

class MetaDataElement():
    def __init__(self, data = None):
        self.CONSISTENCY_GROUP = 'consistencyGroup'
        self.ELEMENT_COUNT = 'elementCount'
        self.ID_COUNTER = 'idCounter'
        self.LAST_UPDATE = 'lastUpdate'
        self.NAME = 'name'
        self.PROPERTIES = 'properties'
        self.VERSION = 'version'

        if data is None:
            self._data = {}
            self._data[self.PROPERTIES] = {}
        else:
            self._data = data

    def addProperty(self, key, value):
        if key is None:
            raise Exception('property key must not be null')

        if self._data.get(self.PROPERTIES) is None:
            self._data[self.PROPERTIES] = []

        if len(self._data.get(self.PROPERTIES)) < 1:
            self._data.get(self.PROPERTIES).append({})

        self.getProperties()[key] = value

    def getProperties(self):
        if self._data.get(self.PROPERTIES) is None:
            self._data[self.PROPERTIES] = []

        if len(self._data.get(self.PROPERTIES)) < 1:
            self._data.get(self.PROPERTIES).append({})

        return self._data.get(self.PROPERTIES).get(0)


    def getData(self):
        return self._data

    def get(self, key):
        return self._data.get(key)

    def getConsistencyGroup(self):
        return self._data.get(self.CONSISTENCY_GROUP)

    def getElementCount(self):
        return self._data.get(self.ELEMENT_COUNT)

    def getIdCounter(self):
        return self._data.get(self.ID_COUNTER)

    def getLastUpdate(self):
        return self._data.get(self.LAST_UPDATE)

    def getName(self):
        return self._data.get(self.NAME)

    def getVersion(self):
        return self._data.get(self.VERSION)

    def getProperties(self):
        if self._data.get(self.PROPERTIES) is None:
            self._data[self.PROPERTIES] = []

        if len(self._data.get(self.PROPERTIES)) < 1:
            self._data.get(self.PROPERTIES).append({})

        return self._data.get(self.PROPERTIES)[0];

    def keySet(self):
        return self._data.keys()

    def put(self, key, value):
        self._data[key] = value

    def setConsistencyGroup(self, c):
        self._data[self.CONSISTENCY_GROUP] = c

    def setElementCount(self, c):
        self._data[self.ELEMENT_COUNT] = c

    def setIdCounter(self, c):
        self._data[self.CONSISTENCY_GROUP] = c

    def setLastUpdate(self, c):
        self._data[self.ID_COUNTER] = c

    def setName(self, c):
        self._data[self.NAME] = c

    def setVersion(self, c):
        self._data[self.VERSION] = c

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