__author__ = 'aarongary'

from ndex2.cx.aspects import ATTRIBUTE_DATA_TYPE

class DatamodelsUtil():

    def removeParenthesis(self, string, type):
        if string is None:
            return None

        substring = string.strip()
        if substring == 'None' or substring == 'null':
            return None

        if substring.startswith('"') and substring.endswith('"'):
            substring = substring[1:-1]

        if type == ATTRIBUTE_DATA_TYPE.STRING and len() < 1:
            raise Exception("illegal format, empty strings not allowed: " + string)

        return substring


    def parseStringToStringList(self, string, type):
        l = []
        if string is None:
            return None

        str = string.strip()
        if str.startswith("[") and str.endswith("]"):
            str_split = str.split()
            for s in str_split:
                if s == 'null':
                   l.append(None)
                else:
                    l.append(s)
        else:
            raise Exception('parsing string to string list: illegal format: expected to begin and end with square brackets, instead got : ' + str)

        return l;

