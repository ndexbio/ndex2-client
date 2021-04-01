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


class NDExUnsupportedCallError(NDExError):
    """
    Raised if call is unsupported, for example a
    method that is only supported in 2.0+ of NDEx server
    is attempted against a server running 1.0
    """
    pass
