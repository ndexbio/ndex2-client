#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HTTP layer shared by the v3 API namespaces.

Every namespace on :py:class:`~ndex2.client.Ndex2` (``client.files``,
``client.networks`` and so on) receives one
:py:class:`HttpTransport` instance. Authentication, session reuse,
timeouts, URL construction and the translation of transport failures into
:py:mod:`ndex2.exceptions` all live here, so that re-authenticating the
transport re-authenticates every namespace at once.

The flat methods on :py:class:`~ndex2.client.Ndex2` continue to use that
class's own verb helpers and are unaffected by anything here.

.. versionadded:: 3.12.0
"""

import json
import logging

import requests
from requests import exceptions as req_except

from ndex2.exceptions import NDExError
from ndex2.exceptions import NDExUnauthorizedError
from ndex2.exceptions import raise_from_exception
from ndex2.exceptions import raise_from_requests_http_error

logger = logging.getLogger(__name__)

V2 = '/v2'
"""Version prefix for the v2 API."""

V3 = '/v3'
"""Version prefix for the v3 API."""

DEFAULT_TIMEOUT = 30
"""Seconds before a request is abandoned."""


class HttpTransport(object):
    """
    Performs authenticated HTTP requests against an NDEx server.

    .. versionadded:: 3.12.0

    :param host: Base URL of the server, including any servlet context
                 path. A missing scheme is assumed to be ``http``.
    :type host: str
    :param username: Account name for HTTP Basic authentication
    :type username: str
    :param password: Password for *username*
    :type password: str
    :param bearer_token: OAuth/Keycloak id token. Sent as an
                         ``Authorization: Bearer`` header and used in
                         preference to *username* and *password* when
                         both are supplied.
    :type bearer_token: str
    :param timeout: Seconds before a request is abandoned, or a
                    ``(connect, read)`` pair
    :type timeout: float or tuple
    :param user_agent: Appended to the ``User-Agent`` header
    :type user_agent: str
    :param debug: If ``True``, log the status code and body of every
                  response
    :type debug: bool
    :param session: Pre-built session to use instead of creating one.
                    Intended for tests.
    :type session: :py:class:`requests.Session`
    """

    USER_AGENT_PREFIX = 'ndex2-client'

    def __init__(self, host, username=None, password=None,
                 bearer_token=None, timeout=DEFAULT_TIMEOUT, user_agent='',
                 debug=False, session=None):
        if host is None:
            raise NDExError('host cannot be None')
        if 'http' not in host:
            host = 'http://' + host
        self.host = host.rstrip('/')
        self.timeout = timeout
        self.user_agent = user_agent if user_agent else ''
        self.debug = debug
        self.session = session if session is not None else requests.session()
        self.username = None
        self.password = None
        self.bearer_token = None
        self.set_auth(username=username, password=password,
                      bearer_token=bearer_token)

    # ------------------------------------------------------------------
    # authentication
    # ------------------------------------------------------------------

    def set_auth(self, username=None, password=None, bearer_token=None):
        """
        Replaces the credentials used by every namespace.

        Because all namespaces share this object, changing credentials
        here is immediately visible to all of them. Calling with no
        arguments clears authentication.

        .. versionadded:: 3.12.0

        :param username: Account name for HTTP Basic authentication
        :type username: str
        :param password: Password for *username*
        :type password: str
        :param bearer_token: OAuth/Keycloak id token, preferred over
                             *username* and *password*
        :type bearer_token: str
        :return: ``None``
        """
        self.username = username
        self.password = password
        self.bearer_token = bearer_token
        self.session.headers.pop('Authorization', None)
        self.session.auth = None
        if bearer_token is not None:
            self.session.headers['Authorization'] = 'Bearer ' + bearer_token
        elif username is not None and password is not None:
            self.session.auth = (username, password)

    @property
    def is_authenticated(self):
        """
        Whether any credentials are currently set.

        .. versionadded:: 3.12.0

        :return: ``True`` if a bearer token, or both a username and
                 password, are set
        :rtype: bool
        """
        return (self.bearer_token is not None or
                (self.username is not None and self.password is not None))

    def require_auth(self):
        """
        Fails immediately if no credentials are set.

        Lets a namespace reject an unauthenticated call before spending a
        network round trip on a request the server will refuse.

        .. versionadded:: 3.12.0

        :raises NDExUnauthorizedError: If no credentials are set
        :return: ``None``
        """
        if not self.is_authenticated:
            raise NDExUnauthorizedError('This call requires credentials; '
                                        'none were set on this client')

    # ------------------------------------------------------------------
    # requests
    # ------------------------------------------------------------------

    def build_url(self, route, version=V3):
        """
        Builds the absolute URL for a route.

        .. versionadded:: 3.12.0

        :param route: Path below the version prefix, for example
                      ``/files/folders/``
        :type route: str
        :param version: :py:const:`V2` or :py:const:`V3`
        :type version: str
        :return: Absolute URL
        :rtype: str
        """
        return self.host + version + route

    def request(self, method, route, version=V3, params=None, json_body=None,
                extra_headers=None, stream=False, return_response=False):
        """
        Issues one request and normalizes the outcome.

        .. versionadded:: 3.12.0

        :param method: HTTP verb, for example ``GET``
        :type method: str
        :param route: Path below the version prefix
        :type route: str
        :param version: :py:const:`V2` or :py:const:`V3`. Passed per call
                        rather than fixed on the instance so a single
                        namespace can span both versions.
        :type version: str
        :param params: Query parameters. Entries whose value is ``None``
                       are dropped, so callers can pass optional
                       arguments through unconditionally.
        :type params: dict
        :param json_body: Object serialized as the JSON request body
        :param extra_headers: Headers merged over the defaults
        :type extra_headers: dict
        :param stream: If ``True``, do not preload the response body and
                       return the response object
        :type stream: bool
        :param return_response: If ``True``, return the response object
                                rather than a parsed body. Needed for
                                the v3 create endpoints, which report the
                                new UUID in a ``Location`` header as well
                                as the body.
        :type return_response: bool
        :raises NDExNotFoundError: If the server responds 404
        :raises NDExUnauthorizedError: If the server responds 401
        :raises NDExError: For any other failure, including timeouts and
                           connection errors
        :return: Parsed JSON, response text, ``None`` for an empty body,
                 or the response object
        """
        url = self.build_url(route, version=version)
        headers = {'User-Agent': self.USER_AGENT_PREFIX + self.user_agent,
                   'Accept': 'application/json,text/plain'}
        if json_body is not None:
            headers['Content-Type'] = 'application/json;charset=UTF-8'
        if extra_headers is not None:
            headers.update(extra_headers)

        if params is not None:
            params = {key: val for key, val in params.items()
                      if val is not None}

        body = None
        if json_body is not None:
            body = json.dumps(json_body)

        logger.debug('%s %s params=%s', method, url, str(params))

        response = None
        try:
            response = self.session.request(method, url, params=params,
                                            data=body, headers=headers,
                                            timeout=self.timeout,
                                            stream=stream)
            if self.debug is True:
                logger.debug('%s from %s: %s', response.status_code, url,
                             response.text if not stream else '<streamed>')
            response.raise_for_status()
        except req_except.HTTPError as he:
            raise_from_requests_http_error(he)
        except NDExError:
            raise
        except Exception as e:
            raise_from_exception(e)

        if stream is True or return_response is True:
            return response
        return self.parse(response)

    def get(self, route, **kwargs):
        """
        Issues a ``GET``. See :py:meth:`request` for arguments.

        .. versionadded:: 3.12.0

        :param route: Path below the version prefix
        :type route: str
        :return: Result of :py:meth:`request`
        """
        return self.request('GET', route, **kwargs)

    def post(self, route, **kwargs):
        """
        Issues a ``POST``. See :py:meth:`request` for arguments.

        .. versionadded:: 3.12.0

        :param route: Path below the version prefix
        :type route: str
        :return: Result of :py:meth:`request`
        """
        return self.request('POST', route, **kwargs)

    def put(self, route, **kwargs):
        """
        Issues a ``PUT``. See :py:meth:`request` for arguments.

        .. versionadded:: 3.12.0

        :param route: Path below the version prefix
        :type route: str
        :return: Result of :py:meth:`request`
        """
        return self.request('PUT', route, **kwargs)

    def delete(self, route, **kwargs):
        """
        Issues a ``DELETE``. See :py:meth:`request` for arguments.

        .. versionadded:: 3.12.0

        :param route: Path below the version prefix
        :type route: str
        :return: Result of :py:meth:`request`
        """
        return self.request('DELETE', route, **kwargs)

    # ------------------------------------------------------------------
    # response handling
    # ------------------------------------------------------------------

    @staticmethod
    def parse(response):
        """
        Converts a response body into a Python object.

        A body is parsed as JSON when the ``Content-Type`` says so, and
        also when it plainly begins with ``{`` or ``[``. The second case
        matters because a proxy that drops the header would otherwise
        hand callers a string where a dict is expected, producing a
        failure far from its cause. Bare scalars are left as text, so a
        ``text/plain`` body of ``123`` does not become an int.

        .. versionadded:: 3.12.0

        :param response: Response to read
        :type response: :py:class:`requests.Response`
        :return: ``None`` for an empty body, parsed JSON for a JSON body,
                 otherwise the body text
        """
        if response.status_code == 204 or not response.content:
            return None
        text = response.text
        ctype = (response.headers.get('Content-Type') or '').lower()
        if 'application/json' in ctype or text.lstrip()[:1] in ('{', '['):
            try:
                return response.json()
            except ValueError:
                return text
        return text

    @staticmethod
    def uuid_from_created(response):
        """
        Extracts the UUID of a newly created object from a 201 response.

        The v3 create endpoints return an ``NdexObjectUpdateStatus`` body
        carrying a ``uuid`` field and also set a ``Location`` header. The
        body is preferred and the header is the fallback.

        .. versionadded:: 3.12.0

        :param response: Response from a create call
        :type response: :py:class:`requests.Response`
        :raises NDExError: If no UUID can be recovered
        :return: UUID of the created object
        :rtype: str
        """
        body = HttpTransport.parse(response)
        if isinstance(body, dict) and body.get('uuid') is not None:
            return str(body['uuid'])
        location = response.headers.get('Location')
        if location is not None and len(location) > 0:
            return location.rstrip('/').split('/')[-1]
        if isinstance(body, str) and len(body.strip()) > 0:
            return body.strip().strip('"')
        raise NDExError('Server did not report the UUID of the created '
                        'object')
