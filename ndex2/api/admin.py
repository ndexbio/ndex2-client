# -*- coding: utf-8 -*-

"""
The ``admin`` namespace, reached as ``client.admin``.

.. versionadded:: 3.12.0
"""

ADMIN = '/admin'


class AdminAPI(object):
    """
    Server status.

    Not instantiated directly. Reached as ``client.admin`` on
    :py:class:`~ndex2.client.Ndex2`.

    :param http: Shared transport, supplied by the client
    :type http: :py:class:`~ndex2.transport.HttpTransport`
    """

    def __init__(self, http):
        self._http = http

    def status(self, format='full'):
        """
        Retrieves the status of the v3 API.

        ``GET /v3/admin/status``

        Useful for confirming a host serves v3 before relying on the
        namespaces. The flat
        :py:meth:`~ndex2.client.Ndex2.update_status` reports the v2 status
        and caches it on the client; this does neither.

        :param format: ``full`` for the complete status object, or
                       ``standard`` for a reduced one
        :type format: str
        :raises NDExError: If the host does not answer the v3 status
                           endpoint
        :return: Server status
        :rtype: dict
        """
        return self._http.get(ADMIN + '/status', params={'format': format})
