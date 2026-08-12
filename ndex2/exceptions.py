# -*- coding: utf-8 -*-


class NDExError(Exception):
    """
    Base Exception for all NDEx2 Python Client Exceptions

    .. warning::

        Many methods in this code base still incorrectly
        raise errors not derived from this base class

    """


class NDExNotFoundError(NDExError):
    """
    Raised if resource requested was not found
    """
    pass


class NDExUnauthorizedError(NDExError):
    """
    Raised if unable to authenticate, either due to lack of
    or invalid credentials.
    """
    pass


class NDExInvalidParameterError(NDExError):
    """
    Raised if invalid parameter is passed in
    """
    pass


class NDExInvalidCXError(NDExError):
    """
    Raised due to invalid CX
    """
    pass


class NDExInvalidCX2Error(NDExError):
    """
    Raised due to invalid CX

    .. versionadded:: 3.6.0
    """
    pass


class NDExUnsupportedCallError(NDExError):
    """
    Raised if call is unsupported, for example a
    method that is only supported in 2.0+ of NDEx server
    is attempted against a server running 1.0
    """
    pass


class NDExAlreadyExists(NDExError):
    """
    Raised when node, edge etc. already exists.

    .. versionadded:: 3.6.0
    """
    pass


def raise_from_requests_http_error(http_error):
    """
    Raises the :py:class:`NDExError` subclass matching a
    :py:class:`requests.HTTPError`.

    This is the single place the mapping from HTTP status code to
    exception type lives, so that every code path reporting a server
    failure reports it identically.

    :param http_error: Error raised by :py:mod:`requests`
    :type http_error: :py:class:`requests.HTTPError`
    :raises NDExNotFoundError: If the status code is 404
    :raises NDExUnauthorizedError: If the status code is 401
    :raises NDExError: For any other status code, or if *http_error* is
                       ``None``
    """
    if http_error is None:
        raise NDExError('Caught unknown server error')
    errmsg = 'Caught ' + str(http_error.response.status_code) + \
             ' from server: ' + str(http_error.response.text)
    if http_error.response.status_code == 404:
        raise NDExNotFoundError(errmsg)
    if http_error.response.status_code == 401:
        raise NDExUnauthorizedError(errmsg)
    raise NDExError(errmsg)


def raise_from_exception(error):
    """
    Raises :py:class:`NDExError` describing an arbitrary exception.

    :param error: Error to describe
    :type error: :py:class:`Exception`
    :raises NDExError: Always
    """
    if error is None:
        raise NDExError('Caught unknown error')
    raise NDExError('Caught ' + str(error.__class__.__name__) +
                    ': ' + str(error))
