# -*- coding: utf-8 -*-


class NDExError(Exception):
    """
    Base Exception for all NDEx2 client exceptions
    """
    pass


class NDExUnauthorizedError(NDExError):
    """
    Unable to authenticate, either due to lack of
    or invalid credentials.
    """


class NDExInvalidCXError(NDExError):
    """
    Invalid CX error
    """
    pass