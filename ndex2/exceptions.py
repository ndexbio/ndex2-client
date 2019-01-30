# -*- coding: utf-8 -*-


class NDExError(Exception):
    """
    Base Exception for all NDEx2 client exceptions
    """
    pass


class InvalidCXError(NDExError):
    """
    Invalid CX error
    """
    pass