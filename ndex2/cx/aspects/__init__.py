__author__ = 'aarongary'
from enum import Enum
from six import string_types, integer_types
from sys import version_info
PY3 = version_info > (3,)

class ATTRIBUTE_DATA_TYPE(Enum):
    BOOLEAN = 'boolean'
    BYTE = 'byte'
    CHAR = 'char'
    DOUBLE = 'double'
    FLOAT = 'float'
    INTEGER = 'integer'
    LONG = 'long'
    SHORT = 'short'
    STRING = 'string'
    LIST_OF_BOOLEAN = 'list_of_boolean'
    LIST_OF_BYTE = 'list_of_byte'
    LIST_OF_CHAR = 'list_of_char'
    LIST_OF_DOUBLE = 'list_of_double'
    LIST_OF_FLOAT = 'list_of_float'
    LIST_OF_INTEGER = 'list_of_integer'
    LIST_OF_LONG = 'list_of_long'
    LIST_OF_SHORT = 'list_of_short'
    LIST_OF_STRING = 'list_of_string'

    @classmethod
    def toCxLabel(self, dt):
        if dt == ATTRIBUTE_DATA_TYPE.BOOLEAN:
            return 'boolean'
        elif dt == ATTRIBUTE_DATA_TYPE.BYTE:
            return 'byte'
        elif dt == ATTRIBUTE_DATA_TYPE.CHAR:
            return 'char'
        elif dt == ATTRIBUTE_DATA_TYPE.DOUBLE:
            return 'double'
        elif dt == ATTRIBUTE_DATA_TYPE.FLOAT:
            return 'float'
        elif dt == ATTRIBUTE_DATA_TYPE.INTEGER:
            return 'integer'
        elif dt == ATTRIBUTE_DATA_TYPE.LONG:
            return 'long'
        elif dt == ATTRIBUTE_DATA_TYPE.SHORT:
            return 'short'
        elif dt == ATTRIBUTE_DATA_TYPE.STRING:
            return 'string'
        elif dt == ATTRIBUTE_DATA_TYPE.LIST_OF_BOOLEAN:
            return 'list_of_boolean'
        elif dt == ATTRIBUTE_DATA_TYPE.LIST_OF_BYTE:
            return 'list_of_byte'
        elif dt == ATTRIBUTE_DATA_TYPE.LIST_OF_CHAR:
            return 'list_of_char'
        elif dt == ATTRIBUTE_DATA_TYPE.LIST_OF_DOUBLE:
            return 'list_of_double'
        elif dt == ATTRIBUTE_DATA_TYPE.LIST_OF_FLOAT:
            return 'list_of_float'
        elif dt == ATTRIBUTE_DATA_TYPE.LIST_OF_INTEGER:
            return 'list_of_integer'
        elif dt == ATTRIBUTE_DATA_TYPE.LIST_OF_LONG:
            return 'list_of_long'
        elif dt == ATTRIBUTE_DATA_TYPE.LIST_OF_SHORT:
            return 'list_of_short'
        elif dt == ATTRIBUTE_DATA_TYPE.LIST_OF_STRING:
            return 'list_of_string'
        else:
            raise Exception('don\'t know type ' + dt)

    @classmethod
    def fromCxLabel(self, s):
        if s == 'boolean':
            return ATTRIBUTE_DATA_TYPE.BOOLEAN
        elif s == 'byte':
            return ATTRIBUTE_DATA_TYPE.BYTE
        elif s == 'char':
            return ATTRIBUTE_DATA_TYPE.CHAR
        elif s == 'double':
            return ATTRIBUTE_DATA_TYPE.DOUBLE
        elif s == 'float':
            return ATTRIBUTE_DATA_TYPE.FLOAT
        elif s == 'integer':
            return ATTRIBUTE_DATA_TYPE.INTEGER
        elif s == 'long':
            return ATTRIBUTE_DATA_TYPE.LONG
        elif s == 'short':
            return ATTRIBUTE_DATA_TYPE.SHORT
        elif s == 'string':
            return ATTRIBUTE_DATA_TYPE.STRING
        elif s == 'list_of_boolean':
            return ATTRIBUTE_DATA_TYPE.LIST_OF_BOOLEAN
        elif s == 'list_of_byte':
            return ATTRIBUTE_DATA_TYPE.LIST_OF_BYTE
        elif s == 'list_of_char':
            return ATTRIBUTE_DATA_TYPE.LIST_OF_CHAR
        elif s == 'list_of_double':
            return ATTRIBUTE_DATA_TYPE.LIST_OF_DOUBLE
        elif s == 'list_of_float':
            return ATTRIBUTE_DATA_TYPE.LIST_OF_FLOAT
        elif s == 'list_of_integer':
            return ATTRIBUTE_DATA_TYPE.LIST_OF_INTEGER
        elif s == 'list_of_long':
            return ATTRIBUTE_DATA_TYPE.LIST_OF_LONG
        elif s == 'list_of_short':
            return ATTRIBUTE_DATA_TYPE.LIST_OF_SHORT
        elif s == 'list_of_string':
            return ATTRIBUTE_DATA_TYPE.LIST_OF_STRING
        else:
            raise Exception('don\'t know type ' + s)

    @classmethod
    def isSingleValueType(self, dt):
        if dt in [ATTRIBUTE_DATA_TYPE.BOOLEAN, ATTRIBUTE_DATA_TYPE.BYTE, ATTRIBUTE_DATA_TYPE.CHAR,
                  ATTRIBUTE_DATA_TYPE.DOUBLE, ATTRIBUTE_DATA_TYPE.FLOAT, ATTRIBUTE_DATA_TYPE.INTEGER,
                  ATTRIBUTE_DATA_TYPE.LONG, ATTRIBUTE_DATA_TYPE.SHORT, ATTRIBUTE_DATA_TYPE.STRING]:
            return True
        else:
            return False

    @classmethod
    def convert_to_data_type(self, val):
        if type(val) is list:
            if isinstance(val[0], string_types):
                return ATTRIBUTE_DATA_TYPE.fromCxLabel('list_of_string')
            elif type(val[0]) is bool:
                return ATTRIBUTE_DATA_TYPE.fromCxLabel('list_of_boolean')
            elif isinstance(val[0], integer_types):
                if PY3:
                    return ATTRIBUTE_DATA_TYPE.fromCxLabel('list_of_integer')
                else:
                    if type(val[0]) is int:
                        return ATTRIBUTE_DATA_TYPE.fromCxLabel('list_of_integer')
                    else:
                        return ATTRIBUTE_DATA_TYPE.fromCxLabel('list_of_long')
            elif type(val[0]) is float:
                return ATTRIBUTE_DATA_TYPE.fromCxLabel('list_of_double')
            else:
                return ATTRIBUTE_DATA_TYPE.fromCxLabel('list_of_string') #'list_of_unknown')

        if isinstance(val, string_types):
            return ATTRIBUTE_DATA_TYPE.fromCxLabel('string')
        elif type(val) is bool:
            return ATTRIBUTE_DATA_TYPE.fromCxLabel('boolean')
        elif type(val) is int:
            return ATTRIBUTE_DATA_TYPE.fromCxLabel('integer')
        elif isinstance(val, integer_types):
            if PY3:
                return ATTRIBUTE_DATA_TYPE.fromCxLabel('integer')
            else:
                if type(val) is int:
                    return ATTRIBUTE_DATA_TYPE.fromCxLabel('integer')
                else:
                    return ATTRIBUTE_DATA_TYPE.fromCxLabel('long')
        elif type(val) is float:
            return ATTRIBUTE_DATA_TYPE.fromCxLabel('double')
        else:
            return ATTRIBUTE_DATA_TYPE.fromCxLabel('string')  #'unknown')

