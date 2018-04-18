

class MetaData(object):
    def __init__(self, metadata_collection=None):
        if metadata_collection is None:
            self._collection = []
        else:
            self._collection = metadata_collection

    def add_metadata(self, metadata_element):
        self._collection.append(metadata_element)

    def to_cx_str(self):
        return '{"metaData":[' + ','.join(map(lambda x: x.to_cx_str(), self._collection)) + ']}'
