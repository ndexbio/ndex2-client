__author__ = 'aarongary'

import json

class NameSpace():
    def __init__(self,namespace_table):
        self._table = namespace_table

    @staticmethod
    def getAspectName():
        return '@context'

    def to_cx_str(self):
        return json.dumps(self._table)


