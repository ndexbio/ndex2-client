

class MetaData(object):
    def __init__(self, metadata_collection=None):
        if metadata_collection is None:
            self._table = {}
        else:
            self._table = metadata_collection

    def add_metadata(self, metadata_element):
        self._table[metadata_element.get_name()] = metadata_element

    def get_metadata(self, name):
        return self._table.get(name)

    def remove_metadata(self, name):
        return self._table.pop(name, None)

    def to_cx_str(self):
        return '{"metaData":[' + ','.join(map(lambda x: x.to_cx_str(), self._table.values())) + ']}'
