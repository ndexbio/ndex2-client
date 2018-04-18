__author__ = 'aarongary'
import json
from ndex2.cx import CX_CONSTANTS

class MetaDataElement(object):
    def __init__(self, name, elementCount=None, idCounter=None, properties=[], version='1.0', consistencyGroup=1):
        self.meta = {
            "name": name,
            "version": version,
            "consistencyGroup": consistencyGroup,
            "elementCount": elementCount,
            "idCounter": idCounter,
            "properties": properties
        }

    def get_consistency_group(self):
        return self.meta["consistencyGroup"]

    def get_element_count(self):
        return self.meta["elementCount"]

    def get_id_counter(self):
        return self.meta["idCounter"]

    def get_name(self):
        return self.meta["name"]

    def get_version(self):
        return self.meta["version"]

    def get_properties(self):
        return self.meta["properties"]

    def set_consistency_group(self, cg):
        self.meta["consistencyGroup"] = cg

    def set_element_count(self, ec):
        self.meta["elementCount"]= ec

    def set_id_counter(self, ic):
        self.meta["idCounter"] = ic

    def set_name(self, n):
        self.meta["name"] = n

    def set_version(self, v):
        self.meta["version"] = v

    def to_cx_str(self):
        return json.dumps(self.meta)
