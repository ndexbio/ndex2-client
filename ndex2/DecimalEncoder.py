__author__ = 'aarongary'
import decimal
import numpy
import json

# TODO - consolidate decimalencoder

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        elif isinstance(o, numpy.int64):
            return int(o)
        return super(DecimalEncoder, self).default(o)
