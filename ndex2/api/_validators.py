# -*- coding: utf-8 -*-

"""
Argument checks shared by the v3 API namespaces.

These fail before a request is sent, so that a mistake in a caller's
arguments is reported at the call site rather than as a server error.

.. versionadded:: 3.12.0
"""

from ndex2.constants import FileType
from ndex2.exceptions import NDExInvalidParameterError


def require_str(value, name):
    """
    Verifies *value* is a non-empty string.

    :param value: Value to check
    :param name: Parameter name, used in the error message
    :type name: str
    :raises NDExInvalidParameterError: If *value* is not a non-empty
                                       string
    :return: *value* unchanged
    :rtype: str
    """
    if value is None:
        raise NDExInvalidParameterError(name + ' cannot be None')
    if not isinstance(value, str):
        raise NDExInvalidParameterError(name + ' must be a string')
    if len(value.strip()) == 0:
        raise NDExInvalidParameterError(name + ' cannot be empty')
    return value


def require_id(value, name):
    """
    Verifies *value* is a usable identifier and returns it as a string.

    Unlike :py:func:`require_str` this accepts any object with a sensible
    string form, such as a :py:class:`uuid.UUID`, while still rejecting
    ``None``. Calling ``require_str(str(value), name)`` would not: ``str``
    turns ``None`` into the perfectly valid string ``'None'``.

    :param value: Identifier to check
    :param name: Parameter name, used in the error message
    :type name: str
    :raises NDExInvalidParameterError: If *value* is ``None`` or its string
                                       form is empty
    :return: *value* as a string
    :rtype: str
    """
    if value is None:
        raise NDExInvalidParameterError(name + ' cannot be None')
    text = str(value)
    if len(text.strip()) == 0:
        raise NDExInvalidParameterError(name + ' cannot be empty')
    return text


def require_enum(value, valid, name, allow_none=True):
    """
    Verifies *value* is one of *valid*, comparing case-insensitively.

    :param value: Value to check
    :param valid: Permitted values
    :type valid: iterable of str
    :param name: Parameter name, used in the error message
    :type name: str
    :param allow_none: If ``True``, ``None`` is returned unchanged
    :type allow_none: bool
    :raises NDExInvalidParameterError: If *value* is not permitted
    :return: Upper-cased *value*, or ``None``
    :rtype: str
    """
    if value is None:
        if allow_none is True:
            return None
        raise NDExInvalidParameterError(name + ' cannot be None')
    if not isinstance(value, str):
        raise NDExInvalidParameterError(name + ' must be a string')
    upper = value.upper()
    if upper not in valid:
        raise NDExInvalidParameterError(
            name + ' must be one of ' + ', '.join(sorted(valid)) +
            ' but got ' + str(value))
    return upper


def require_id_list(values, name):
    """
    Normalizes one UUID or a collection of them to a list of strings.

    :param values: UUID or UUIDs
    :type values: str or list
    :param name: Parameter name, used in the error message
    :type name: str
    :raises NDExInvalidParameterError: If *values* is ``None``, empty, or
                                       not iterable
    :return: UUIDs as strings
    :rtype: list
    """
    if values is None:
        raise NDExInvalidParameterError(name + ' cannot be None')
    if isinstance(values, str):
        values = [values]
    try:
        id_list = [str(val) for val in values]
    except TypeError:
        raise NDExInvalidParameterError(name + ' must be a list of UUIDs')
    if len(id_list) == 0:
        raise NDExInvalidParameterError(name + ' cannot be empty')
    return id_list


def to_file_map(files, default_type=None):
    """
    Normalizes the ways of naming file items into the ``{uuid: type}``
    map the sharing and visibility endpoints expect.

    Accepts a ``dict`` of UUID to :py:class:`~ndex2.constants.FileType`,
    a list of ``(uuid, type)`` pairs, or a plain list of UUIDs when
    *default_type* is given.

    Omitting the type with no *default_type* set is an error rather than
    an assumption, since guessing wrong would act on the wrong object.

    :param files: File items to normalize
    :type files: dict or list or str
    :param default_type: Type applied to entries that do not carry one
    :type default_type: str
    :raises NDExInvalidParameterError: If *files* is empty, holds an
                                       unrecognized type, or omits a type
                                       with no *default_type* set
    :return: Map of UUID string to file type string
    :rtype: dict
    """
    default_type = require_enum(default_type, FileType.ALL, 'default_type')
    if files is None:
        raise NDExInvalidParameterError('files cannot be None')
    if isinstance(files, str):
        files = [files]

    if isinstance(files, dict):
        pairs = list(files.items())
    else:
        pairs = []
        for entry in files:
            if isinstance(entry, str):
                pairs.append((entry, default_type))
            elif isinstance(entry, (list, tuple)) and len(entry) == 2:
                pairs.append((entry[0], entry[1]))
            else:
                raise NDExInvalidParameterError(
                    'files entries must be UUID strings or (uuid, type) '
                    'pairs')

    file_map = {}
    for uuid_val, type_val in pairs:
        if type_val is None:
            type_val = default_type
        if type_val is None:
            raise NDExInvalidParameterError(
                'No file type given for ' + str(uuid_val) +
                ' and no default_type set')
        file_map[str(uuid_val)] = require_enum(str(type_val), FileType.ALL,
                                               'file type',
                                               allow_none=False)
    if len(file_map) == 0:
        raise NDExInvalidParameterError('files cannot be empty')
    return file_map
