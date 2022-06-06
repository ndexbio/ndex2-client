# -*- coding: utf-8 -*-

import logging
from ndex2 import constants
from ndex2.exceptions import NDExError


class DataConverter(object):
    """
    Base class for subclasses that convert CX data types
    to/from native data types

    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def convert_value(self, value=None, datatype=None):
        """
        Defines method to converts *value* from CX to native data
        type using *datatype* as a guide

        :param value: Value to convert
        :type value: object
        :param datatype: CX data type which is one of the following:
                         :py:const:`ndex2.constants.VALID_ATTRIBUTE_DATATYPES`
        :type datatype: str
        :raises NotImplementedError: Always raises this error cause subclasses
                                     should implement
        :return: Always raises :py:class:`NotImplementedError`
        """
        raise NotImplementedError('Must be implemented by subclass')


class PandasDataConverter(DataConverter):
    """
    Converts CX values to native Python data types
    via :py:func:`PandasDataConverter.convert_value` method

    .. versionadded:: 3.5.0

    """

    LIST_DTYPES = [constants.LIST_OF_BOOLEAN, constants.LIST_OF_DOUBLE,
                   constants.LIST_OF_INTEGER, constants.LIST_OF_LONG,
                   constants.LIST_OF_STRING]

    def __init__(self):
        super(DataConverter, self).__init__()

    def convert_value(self, value=None, datatype=None):
        """
        Converts *value* parameter passed in to type based on value of
        *datatype* parameter passed in. This is used in data conversion by
        :py:meth:`~ndex2.nice_cx_network.NiceCXNetwork.to_pandas_dataframe`

        .. versionadded:: 3.5.0

        Conversion rules for different values of *datatype* parameter:

        * :py:const:`~ndex2.constants.STRING_DATATYPE` or ``None``

           * `value` is converted by :py:class:`str` and returned

        * :py:const:`~ndex2.constants.BOOLEAN_DATATYPE`

           * If `value` is of type :py:class:`bool` it is just returned.
             If `value` is of type :py:class:`str` and equals `true` (ignore case) or
             `1` then ``True`` is returned and if value equals `false`
             (ignore case) or `0` is then ``False`` is returned.
             Otherwise value is converted by :py:class:`bool` and returned.
             If conversion fails :py:exc:`~ndex2.exceptions.NDExError` is raised

        * :py:const:`~ndex2.constants.DOUBLE_DATATYPE`

           * `value` is converted by :py:class:`float` and returned. If conversion
             fails :py:exc:`~ndex2.exceptions.NDExError` is raised

        * :py:const:`~ndex2.constants.INTEGER_DATATYPE` or :py:const:`~ndex2.constants.LONG_DATATYPE`

           * `value` is converted by :py:class:`int` and returned. If conversion
             fails :py:exc:`~ndex2.exceptions.NDExError` is raised

        * :py:const:`~ndex2.constants.LIST_OF_STRING`, :py:const:`~ndex2.constants.LIST_OF_BOOLEAN`
          :py:const:`~ndex2.constants.LIST_OF_DOUBLE`, :py:const:`~ndex2.constants.LIST_OF_INTEGER`,
          :py:const:`~ndex2.constants.LIST_OF_LONG`

           * If `value` is **NOT** of type :py:class:`list` then the `value` converted
             as if it's datatype is :py:const:`~ndex2.constants.STRING_DATATYPE`.
             If `value` is a list, each element is converted as if it's datatype is
             :py:const:`~ndex2.constants.STRING_DATATYPE` and values of :py:class:`list`
             are converted to a comma delimited :py:class:`str`

        Example usage:

        .. code-block:: python

            from ndex2.util import PandasDataConverter

            converter = PandasDataConverter()

            # converts number to type str
            res = converter.convert_value(123, 'string')

            # would output <class 'str'>
            print(type(res))


        :param value: Value to convert
        :type value: object
        :param datatype: CX data type which is one of the following:
                         :py:const:`ndex2.constants.VALID_ATTRIBUTE_DATATYPES`
        :type datatype: str
        :raises NDExError: If there is an error with conversion
        :return: Converted value
        :rtype: list, str, int, float, or bool
        """
        if datatype is None:
            return str(value)
        try:
            lc_datatype = datatype.lower()

            if lc_datatype == constants.STRING_DATATYPE:
                return str(value)

            if lc_datatype == constants.BOOLEAN_DATATYPE:
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    lc_value = value.lower()
                    if lc_value == 'true' or lc_value == '1':
                        return True
                    if lc_value == 'false' or lc_value == '0':
                        return False
                return bool(value)

            if lc_datatype == constants.DOUBLE_DATATYPE:
                return float(value)

            if lc_datatype == constants.INTEGER_DATATYPE or \
                    lc_datatype == constants.LONG_DATATYPE:
                return int(value)

            if lc_datatype in PandasDataConverter.LIST_DTYPES:
                if not isinstance(value, list):
                    return self.convert_value(value=value,
                                              datatype=constants.STRING_DATATYPE)
                return ','.join([self.convert_value(value=i,
                                 datatype=constants.STRING_DATATYPE) for i in value])

        except ValueError as ve:
                raise NDExError('Unable to convert ' + str(value) +
                                ' to type compatible with ' + datatype +
                                ' CX data type : ' + str(ve))
        except Exception as e:
            raise NDExError('Unable to convert ' + str(value) + ' : ' + str(e))

        raise NDExError(datatype + ' unknown data type, cannot convert: ' + str(value))

