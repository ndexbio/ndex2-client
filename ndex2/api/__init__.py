# -*- coding: utf-8 -*-

"""
API namespaces for the NDEx **v3** REST API.

Each module here defines one namespace reached as an attribute of
:py:class:`~ndex2.client.Ndex2`, for example ``client.files``. Namespaces
receive a shared :py:class:`~ndex2.transport.HttpTransport` and never
build URLs or touch :py:mod:`requests` themselves.

.. versionadded:: 3.12.0
"""
