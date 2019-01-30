# -*- coding: utf-8 -*-


class NDExError(Exception):
    """
    Base Exception for all NDEx2 client exceptions
    """
    pass


class UnauthorizedError(NDExError):
    """
    Unable to authenticate, either due to lack of
    or invalid credentials.
    """

class InvalidCXError(NDExError):
    """
    Invalid CX error
    """
    pass