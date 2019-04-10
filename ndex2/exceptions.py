# -*- coding: utf-8 -*-


class NDExError(Exception):
    """
    Base Exception for all NDEx2 Python Client Exceptions
    """
    pass


class NDExUnauthorizedError(NDExError):
    """
    Raised if unable to authenticate, either due to lack of
    or invalid credentials.
    """
    pass


class NDExInvalidCXError(NDExError):
    """
    Raised due to invalid CX
    """
    pass
