__author__ = 'aarongary'
from enum import Enum
from six import string_types, integer_types
from sys import version_info
PY3 = version_info > (3,)


class ATTRIBUTE_DATA_TYPE(Enum):
    BOOLEAN = 'boolean'
    DOUBLE = 'double'
    INTEGER = 'integer'
    LONG = 'long'
    STRING = 'string'
    LIST_OF_BOOLEAN = 'list_of_boolean'
    LIST_OF_DOUBLE = 'list_of_double'
    LIST_OF_INTEGER = 'list_of_integer'
    LIST_OF_LONG = 'list_of_long'
    LIST_OF_STRING = 'list_of_string'

    @staticmethod
    def to_cx_label(dt):
        if dt == ATTRIBUTE_DATA_TYPE.BOOLEAN:
            return 'boolean'
        elif dt == ATTRIBUTE_DATA_TYPE.DOUBLE:
            return 'double'
        elif dt == ATTRIBUTE_DATA_TYPE.INTEGER:
            return 'integer'
        elif dt == ATTRIBUTE_DATA_TYPE.LONG:
            return 'long'
        elif dt == ATTRIBUTE_DATA_TYPE.STRING:
            return 'string'
        elif dt == ATTRIBUTE_DATA_TYPE.LIST_OF_BOOLEAN:
            return 'list_of_boolean'
        elif dt == ATTRIBUTE_DATA_TYPE.LIST_OF_DOUBLE:
            return 'list_of_double'
        elif dt == ATTRIBUTE_DATA_TYPE.LIST_OF_INTEGER:
            return 'list_of_integer'
        elif dt == ATTRIBUTE_DATA_TYPE.LIST_OF_LONG:
            return 'list_of_long'
        elif dt == ATTRIBUTE_DATA_TYPE.LIST_OF_STRING:
            return 'list_of_string'
        else:
            raise Exception('don\'t know type ' + dt)

    @staticmethod
    def from_cx_label(s):
        if s == 'boolean':
            return ATTRIBUTE_DATA_TYPE.BOOLEAN
        elif s == 'double' or s == 'float':
            return ATTRIBUTE_DATA_TYPE.DOUBLE
        elif s == 'integer' or s == 'byte' or s == 'short':
            return ATTRIBUTE_DATA_TYPE.INTEGER
        elif s == 'long':
            return ATTRIBUTE_DATA_TYPE.LONG
        elif s == 'string' or s == 'char':
            return ATTRIBUTE_DATA_TYPE.STRING
        elif s == 'list_of_boolean':
            return ATTRIBUTE_DATA_TYPE.LIST_OF_BOOLEAN
        elif s == 'list_of_double' or s == 'list_of_float':
            return ATTRIBUTE_DATA_TYPE.LIST_OF_DOUBLE
        elif s == 'list_of_integer' or s == 'list_of_byte' or s == 'list_of_short':
            return ATTRIBUTE_DATA_TYPE.LIST_OF_INTEGER
        elif s == 'list_of_long':
            return ATTRIBUTE_DATA_TYPE.LIST_OF_LONG
        elif s == 'list_of_string' or s == 'list_of_char':
            return ATTRIBUTE_DATA_TYPE.LIST_OF_STRING
        else:
            raise Exception('don\'t know type ' + s)

    @staticmethod
    def is_single_value_type(dt):
        return dt in [ATTRIBUTE_DATA_TYPE.BOOLEAN, ATTRIBUTE_DATA_TYPE.DOUBLE, ATTRIBUTE_DATA_TYPE.INTEGER,
                      ATTRIBUTE_DATA_TYPE.LONG,  ATTRIBUTE_DATA_TYPE.STRING]

    @staticmethod
    def convert_to_data_type(val):
        if type(val) is list:
            if isinstance(val[0], string_types):
                return ATTRIBUTE_DATA_TYPE.from_cx_label('list_of_string')
            elif type(val[0]) is bool:
                return ATTRIBUTE_DATA_TYPE.from_cx_label('list_of_boolean')
            elif isinstance(val[0], integer_types):
                if PY3:
                    return ATTRIBUTE_DATA_TYPE.from_cx_label('list_of_integer')
                else:
                    if type(val[0]) is int:
                        return ATTRIBUTE_DATA_TYPE.from_cx_label('list_of_integer')
                    else:
                        return ATTRIBUTE_DATA_TYPE.from_cx_label('list_of_long')
            elif type(val[0]) is float:
                return ATTRIBUTE_DATA_TYPE.from_cx_label('list_of_double')
            else:
                return ATTRIBUTE_DATA_TYPE.from_cx_label('list_of_string')

        if isinstance(val, string_types):
            return ATTRIBUTE_DATA_TYPE.from_cx_label('string')
        elif type(val) is bool:
            return ATTRIBUTE_DATA_TYPE.from_cx_label('boolean')
        elif type(val) is int:
            return ATTRIBUTE_DATA_TYPE.from_cx_label('integer')
        elif isinstance(val, integer_types):
            if PY3:
                return ATTRIBUTE_DATA_TYPE.from_cx_label('integer')
            else:
                if type(val) is int:
                    return ATTRIBUTE_DATA_TYPE.from_cx_label('integer')
                else:
                    return ATTRIBUTE_DATA_TYPE.from_cx_label('long')
        elif type(val) is float:
            return ATTRIBUTE_DATA_TYPE.from_cx_label('double')
        else:
            return ATTRIBUTE_DATA_TYPE.from_cx_label('string')
