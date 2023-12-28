#!/usr/bin/env python

import requests
import json
import logging
from requests_toolbelt import MultipartEncoder
import io
import sys
import decimal
import numpy

from ndex2.version import __version__
from ndex2.exceptions import NDExInvalidCXError
from ndex2.exceptions import NDExUnauthorizedError
from ndex2.exceptions import NDExError
from ndex2.exceptions import NDExUnsupportedCallError
from ndex2.exceptions import NDExInvalidParameterError
from ndex2.exceptions import NDExNotFoundError

try:
    from urllib.parse import urljoin
except ImportError:
     from urlparse import urljoin

from requests import exceptions as req_except
import time

userAgent = 'NDEx2-Python/' + __version__
"""
User agent value to prepend to all requests
"""

DEFAULT_SERVER = "http://public.ndexbio.org"


class Ndex2(object):
    """ A class to facilitate communication with an
        `NDEx server <http://ndexbio.org>`_.

        If host is not provided it will default to the
        `NDEx public server <http://ndexbio.org>`_.  UUID is required

    """
    USER_AGENT_KEY = 'User-Agent'
    VALID_NETWORK_SYSTEM_PROPERTIES = ['showcase', 'visibility',
                                       'index_level', 'readOnly']
    V3_ENDPOINT = '/v3'

    def __init__(self, host=None, username=None, password=None,
                 update_status=False, debug=False, user_agent='',
                 timeout=30, skip_version_check=False):
        """
        Creates a connection to a particular `NDEx server <http://ndexbio.org>`_.


        .. versionadded:: 3.5.0
           *skip_version_check* parameter added

        :param host: The URL of the server.
        :type host: str
        :param username: The username of the NDEx account to use. (Optional)
        :type username: str
        :param password: The account password. (Optional)
        :type password: str
        :param update_status: If set to True tells constructor to query
                              service for status
        :type update_status: bool
        :param user_agent: String to append to
                           `User-Agent <https://tools.ietf.org/html/rfc1945#page-46>`_
                           header sent with all requests to server
        :type user_agent: str
        :param timeout: The timeout in seconds value for requests to server. This value
                        is passed to Request calls `Click here for more information
                        <http://docs.python-requests.org/en/master/user/advanced/#timeouts>`_
        :type timeout: float or tuple(float, float)
        :param skip_version_check: If ``True``, it is assumed
                                   NDEx server supports **v2** endpoints,
                                   otherwise NDEx server is queried to see
                                   if **v2** endpoints are supported
        :type skip_version_check: bool

        """
        self.debug = debug
        self.version = '1.3'
        self.version_endpoint = '/rest'
        self.status = {}
        self.username = username
        self.password = password
        self.user_agent = user_agent
        if self.user_agent is None:
            self.user_agent = ''
        else:
            if len(self.user_agent) > 0:
                self.user_agent = ' ' + self.user_agent

        self.logger = logging.getLogger(__name__)
        self.timeout = timeout

        if host is None:
            host = DEFAULT_SERVER
        elif 'http' not in host:
            host = 'http://' + host

        if "localhost" in host:
            self.host = "http://localhost:8080/ndexbio-rest"
        else:
            self.host = host
            # Partial fix for https://github.com/ndexbio/ndex2-client/issues/85
            # caller can now skip this check by setting skip_version_check to True
            # in future this will be set to True by default
            if skip_version_check is True:
                self.version = '2.0'
                self.version_endpoint = '/v2'
            else:
                status_url = "/rest/admin/status"

                try:
                    version_url = urljoin(host, status_url)

                    response = requests.get(version_url,
                                            headers={Ndex2.USER_AGENT_KEY:
                                                     userAgent +
                                                     self.user_agent})
                    response.raise_for_status()
                    data = response.json()

                    prop = data.get('properties')
                    if prop is not None:
                        pv = prop.get('ServerVersion')
                        if pv is not None:
                            if not pv.startswith('2.'):
                                raise Exception("This release only supports "
                                                "NDEx 2.x server.")
                            else:
                                self.version = pv
                                self.version_endpoint = '/v2'
                        else:
                            self.logger.warning("Warning: This release "
                                                "doesn't fully "
                                                "support 1.3 version of NDEx")
                    else:
                        self.logger.warning("Warning: No properties found. "
                                            "This release doesn't fully "
                                            "support 1.3 version of NDEx")

                except req_except.HTTPError as he:
                    self.logger.warning("Can't determine server version. " +
                                        host + ' Server returned error -- ' +
                                        str(he) +
                                        ' will assume 1.3 version of NDEx '
                                        'which is not fully supported by this '
                                        'release')
                    # TODO - how to handle errors getting server version...

        # create a session for this Ndex
        self.s = requests.session()
        if username and password:
            # add credentials to the session, if available
            self.s.auth = (username, password)

        if update_status:
            self.update_status()

# Base methods for making requests to this NDEx

    def set_request_timeout(self, time_in_secs):
        """
        Sets request timeout.
        `Click here for more information <http://docs.python-requests.org/en/master/user/quickstart/#timeouts>`_
        :param time_in_secs: Seconds to wait on a request to the
                             service before giving up.
        :type time_in_secs: int
        """
        self.timeout = time_in_secs

    def set_debug_mode(self, debug):
        self.debug = debug

    def debug_response(self, response):
        if self.debug:
            self.logger.debug("status code: " + str(response.status_code))
            if not response.status_code == requests.codes.ok:
                self.logger.debug("response text: " + str(response.text))

    def _require_auth(self):
        """
        :raises NDExUnauthorizedError: If no credentials are found in this object
        """
        if not self.s.auth:
            raise NDExUnauthorizedError("This method requires user authentication")

    def _get_user_agent(self):
        """
        Creates string to use for User-Agent header

        :return: string containing User-Agent header value
        """
        return userAgent + self.user_agent

    def _return_response(self, response,
                         raiseforstatus=True,
                         returnfullresponse=False,
                         returnjsonundertry=False):
        """
        Given a response from service request
        this method returns response.json() if the
        headers Content-Type is application/json otherwise
        response.text is returned
        :param response: response object from requests.put or requests.post
                         call
        :param returnfullresponse: If True then response object passed in
                                   is returned
        :type returnfullresponse: bool
        :return: response.json() or response.text unless returnfullresponse
                 then response passed in is just returned.
        """
        self.debug_response(response)
        if raiseforstatus:
            response.raise_for_status()
        if returnfullresponse is True:
            return response
        if response.status_code == 204:
            return ""

        if returnjsonundertry is True:
            try:
                result = response.json()
            except ValueError:
                result = response.text
            return result

        if ('content-type' in response.headers or
            'Content-Type' in response.headers) and\
                response.headers['content-type'] == 'application/json':
            return response.json()
        else:
            return response.text

    def _convert_requests_http_error_to_ndex_error(self, http_error):
        """
        Raises :py:class:`~ndex2.exceptions.NDExError` using
        information from :py:`requests.HTTPError`
        passed in

        :param http_error: Error from :py:mod:`requests` library
        :type http_error: :py:class:`requests.HTTPError`
        :raises NDExError: Raises this error unless
        :raises NDExNotFoundError: Raises this error if status code
                                   is 404
        :raises NDExUnauthorizedError: Raises this error if status code is 401
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

    def _convert_exception_to_ndex_error(self, error):
        """
        Raises :py:class:`~ndex2.exceptions.NDExError` using
        information from :py:`python.Exception` passed in

        :param error:
        :type error: Exception
        :raises NDExError: always raises error
        """
        if error is None:
            raise NDExError('Caught unknown error')
        raise NDExError('Caught ' + str(error.__class__.__name__) +
                        ': ' + str(error))

    def _get_version_endpoint(self, alt_version_endpoint=None):
        if alt_version_endpoint is None:
            return self.version_endpoint
        return alt_version_endpoint

    def _get_auth_tuple(self):
        """
        Gets a tuple with username and password set via constructor
        if they are both NOT ``None``

        :return: (username, password) or ``None`` if values of both are
                 ``None``
        :rtype: tuple
        """
        if self.username is None and self.password is None:
            return None
        return self.username, self.password

    def put(self, route, put_json=None, alt_version_endpoint=None):
        url = self.host +\
              self._get_version_endpoint(alt_version_endpoint=
                                         alt_version_endpoint) + route
        self.logger.debug("PUT route: " + url)
        self.logger.debug("PUT json: " + str(put_json))

        headers = self.s.headers
        headers['Content-Type'] = 'application/json;charset=UTF-8'
        headers['Accept'] = 'application/json'
        headers[Ndex2.USER_AGENT_KEY] = self._get_user_agent()

        if put_json is not None:
            response = self.s.put(url, data=put_json, headers=headers,
                                  timeout=self.timeout)
        else:
            response = self.s.put(url, headers=headers,
                                  timeout=self.timeout)
        return self._return_response(response)

    def post(self, route, post_json, alt_version_endpoint=None):
        url = self.host + \
              self._get_version_endpoint(alt_version_endpoint=
                                         alt_version_endpoint) + route
        self.logger.debug("POST route: " + url)
        self.logger.debug("POST json: " + post_json)
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json,text/plain',
                   'Cache-Control': 'no-cache',
                   Ndex2.USER_AGENT_KEY: self._get_user_agent(),
                   }
        response = self.s.post(url, data=post_json, headers=headers,
                               timeout=self.timeout)
        return self._return_response(response)

    def delete(self, route, data=None,
               raiseforstatus=True,
               returnfullresponse=False,
               returnjsonundertry=False,
               alt_version_endpoint=None):
        url = self.host + \
              self._get_version_endpoint(alt_version_endpoint=
                                         alt_version_endpoint) + route
        self.logger.debug("DELETE route: " + url)
        headers = self.s.headers
        headers[Ndex2.USER_AGENT_KEY] = userAgent + self.user_agent
        headers['Connection'] = 'close'
        if data is not None:
            response = self.s.delete(url, headers=headers, data=data,
                                     timeout=self.timeout)
        else:
            response = self.s.delete(url, headers=headers,
                                     timeout=self.timeout)
        return self._return_response(response,
                                     raiseforstatus=raiseforstatus,
                                     returnfullresponse=returnfullresponse,
                                     returnjsonundertry=returnjsonundertry)

    def get(self, route, get_params=None, alt_version_endpoint=None):
        url = self.host + \
              self._get_version_endpoint(alt_version_endpoint=
                                         alt_version_endpoint) + route
        self.logger.debug("GET route: " + url)
        headers = self.s.headers
        headers[Ndex2.USER_AGENT_KEY] = self._get_user_agent()
        headers['Connection'] = 'close'
        response = self.s.get(url, params=get_params, headers=headers,
                              timeout=self.timeout)
        return self._return_response(response)

    # The stream refers to the Response, not the Request
    def get_stream(self, route, get_params=None, alt_version_endpoint=None):
        url = self.host + \
              self._get_version_endpoint(alt_version_endpoint=
                                         alt_version_endpoint) + route
        self.logger.debug("GET stream route: " + url)
        headers = self.s.headers
        headers[Ndex2.USER_AGENT_KEY] = self._get_user_agent()
        response = self.s.get(url, params=get_params, stream=True,
                              headers=headers, timeout=self.timeout)
        return self._return_response(response,
                                     returnfullresponse=True)

    # The stream refers to the Response, not the Request
    def post_stream(self, route, post_json, alt_version_endpoint=None):
        url = self.host + \
              self._get_version_endpoint(alt_version_endpoint=
                                         alt_version_endpoint) + route
        self.logger.debug("POST stream route: " + url)
        headers = self.s.headers

        headers['Content-Type'] = 'application/json'
        headers['Accept'] = 'application/json'
        headers[Ndex2.USER_AGENT_KEY] = self._get_user_agent()
        headers['Connection'] = 'close'
        response = self.s.post(url, data=post_json, headers=headers,
                               stream=True, timeout=self.timeout)
        return self._return_response(response,
                                     returnfullresponse=True)

    # The Request is streamed, not the Response
    def put_multipart(self, route, fields, alt_version_endpoint=None,
                      returnjsonundertry=True, returnfullresponse=False):
        url = self.host + \
              self._get_version_endpoint(alt_version_endpoint=
                                         alt_version_endpoint) + route
        multipart_data = MultipartEncoder(fields=fields)
        self.logger.debug("PUT route: " + url)

        headers = {'Content-Type': multipart_data.content_type,
                   'Accept': 'application/json',
                   Ndex2.USER_AGENT_KEY: self._get_user_agent(),
                   'Connection': 'close'
                   }
        response = requests.put(url, data=multipart_data, headers=headers, auth=self._get_auth_tuple())
        return self._return_response(response,
                                     returnjsonundertry=returnjsonundertry,
                                     returnfullresponse=returnfullresponse)

    # The Request is streamed, not the Response
    def post_multipart(self, route, fields, query_string=None, alt_version_endpoint=None,
                       returnjsonundertry=True, returnfullresponse=False):
        url = self.host + \
              self._get_version_endpoint(alt_version_endpoint=
                                         alt_version_endpoint) + route
        if query_string:
            url = url + '?' + query_string

        multipart_data = MultipartEncoder(fields=fields)
        self.logger.debug("POST route: " + url)
        headers = {'Content-Type': multipart_data.content_type,
                   Ndex2.USER_AGENT_KEY: self._get_user_agent(),
                   'Connection': 'close'
                   }

        response = requests.post(url, data=multipart_data, headers=headers, auth=self._get_auth_tuple())
        return self._return_response(response,
                                     returnjsonundertry=returnjsonundertry,
                                     returnfullresponse=returnfullresponse)

# Network methods

    def save_new_network(self, cx, visibility=None):
        """
        Create a new network (CX) on the server

        :param cx: Network CX which is a list of dict objects
        :type cx: list
        :param visibility: Sets the visibility (PUBLIC or PRIVATE)
        :type visibility: str
        :raises NDExInvalidCXError: For invalid CX data
        :return: Response data
        :rtype: str or dict
        """
        if cx is None:
            raise NDExInvalidCXError('CX is None')
        if not isinstance(cx, list):
            raise NDExInvalidCXError('CX is not a list')
        if len(cx) == 0:
            raise NDExInvalidCXError('CX appears to be empty')

        indexed_fields = None
        #TODO add functionality for indexed_fields when it's supported by the server
        if cx[-1] is not None:
            if cx[-1].get('status') is None:
                cx.append({"status": [{"error": "", "success": True}]})
            else:
                if len(cx[-1].get('status')) < 1:
                    cx[-1].get('status').append({"error": "", "success": True})

            if sys.version_info.major == 3:
                stream = io.BytesIO(json.dumps(cx, cls=DecimalEncoder).encode('utf-8'))
            else:
                stream = io.BytesIO(json.dumps(cx, cls=DecimalEncoder))

        return self.save_cx_stream_as_new_network(stream, visibility=visibility)

    def save_cx_stream_as_new_network(self, cx_stream, visibility=None):
        """
        Create a new network from a CX stream.

        :param cx_stream:  IO stream of cx
        :type cx_stream: BytesIO
        :param visibility: Sets the visibility (PUBLIC or PRIVATE)
        :type visibility: str
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :return: Response data
        :rtype: str or dict
        """
        self._require_auth()
        query_string = None
        if visibility:
                query_string = 'visibility=' + str(visibility)

        if self.version.startswith('1.'):
            route = '/network/asCX'
        else:
            route = '/network'

        fields = {
            'CXNetworkStream': ('filename', cx_stream, 'application/octet-stream')
        }

        return self.post_multipart(route, fields, query_string=query_string)

    def save_new_cx2_network(self, cx, visibility=None):
        """
        Create a new network (CX2) on the server

        .. versionadded:: 3.5.0

        .. code-block:: python

            from ndex2.client import Ndex2
            from ndex2.exceptions import NDExError

            client = Ndex2(username=<NDEx USER NAME>,
                           password=<NDEx PASSWORD>,
                           skip_version_check=True)

            # cx is set to an empty CX2 network
            cx = [{"CXVersion":"2.0","hasFragments":false},
                  {"status":[{"success":true}]}]

            try:
                net_url = client.save_new_cx2_network(cx, visibility='PRIVATE')
                print('URL of new network: ' + str(net_url))
            except NDExError as ne:
                print('Caught error: ' + str(ne))

        :param cx: Network CX2 which is a list of dict objects
        :type cx: list
        :param visibility: Sets the visibility (PUBLIC or PRIVATE)
                           If ``None`` sets visibility to PRIVATE
        :type visibility: str
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :raises NDExInvalidCXError: if **cx** is ``None``, not a list,
                                    or is an empty list
        :raises NDExError: if there is an error saving the network
        :return: Full URL to newly created network
                 (ie http://ndexbio.org/v3/networks/XXXX)
        :rtype: str
        """
        if cx is None:
            raise NDExInvalidCXError('CX is None')
        if not isinstance(cx, list):
            raise NDExInvalidCXError('CX is not a list')
        if len(cx) == 0:
            raise NDExInvalidCXError('CX appears to be empty')

        if sys.version_info.major == 3:
            stream = io.BytesIO(json.dumps(cx, cls=DecimalEncoder).encode('utf-8'))
        else:
            stream = io.BytesIO(json.dumps(cx, cls=DecimalEncoder))

        return self.save_cx2_stream_as_new_network(stream, visibility=visibility)

    def save_cx2_stream_as_new_network(self, cx_stream, visibility=None):
        """
        Create a new network from a CX2 stream

        .. versionadded:: 3.5.0

        .. code-block:: python

            import io
            import json
            from ndex2.client import Ndex2
            from ndex2.exceptions import NDExError

            client = Ndex2(username=<NDEx USER NAME>,
                           password=<NDEx PASSWORD>,
                           skip_version_check=True)

            # cx is set to an empty CX2 network
            cx = [{"CXVersion":"2.0","hasFragments":false},
                  {"status":[{"success":true}]}]

            try:
                cx_stream = io.BytesIO(json.dumps(cx,
                                                  cls=DecimalEncoder).encode('utf-8'))
                net_url = client.save_cx2_stream_as_new_network(cx_stream,
                                                                visibility='PUBLIC')
                print('Network URL: ' + str(net_url))
            except NDExError as ne:
                print('Caught error: ' + str(ne))

        :param cx_stream:  IO stream of cx2
        :type cx_stream: BytesIO like object
        :param visibility: Sets the visibility (PUBLIC or PRIVATE)
        :type visibility: str
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :raises NDExError: if there is an error saving the network
        :return: Full URL to newly created network
                 (ie http://ndexbio.org/v3/networks/XXXX)
        :rtype: str
        """
        self._require_auth()
        query_string = None
        if visibility:
            query_string = 'visibility=' + str(visibility)

        fields = {
            'CXNetworkStream': ('filename', cx_stream, 'application/octet-stream')
        }
        try:
            res = self.post_multipart('/networks', fields, query_string=query_string,
                                      alt_version_endpoint=Ndex2.V3_ENDPOINT,
                                      returnfullresponse=True)
            if 'Location' not in res.headers:
                raise NDExError('Unable to get URL for newly created network: ' +
                                str(res.text))
            return res.headers['Location']
        except requests.HTTPError as he:
            self._convert_requests_http_error_to_ndex_error(he)
        except Exception as e:
            self._convert_exception_to_ndex_error(e)

    def update_cx_network(self, cx_stream, network_id):
        """
        Update the network specified by UUID network_id using the CX stream
        **cx_stream** passed in

        :param cx_stream: The network stream.
        :param network_id: The UUID of the network.
        :type network_id: str
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :return: The response.
        :rtype: `response object <http://docs.python-requests.org/en/master/user/quickstart/#response-content>`_

        """
        self._require_auth()
        fields = {
            'CXNetworkStream': ('filename', cx_stream, 'application/octet-stream')
        }

        if self.version.startswith('1.'):
            route = '/network/asCX/%s' % network_id
        else:
            route = "/network/%s" % network_id

        return self.put_multipart(route, fields)

    def update_cx2_network(self, cx_stream, network_id):
        """
        Update the network specified by UUID network_id using the CX2
        stream **cx_stream** passed in

        .. versionadded:: 3.5.0

        .. code-block:: python

            import io
            import json
            from ndex2.client import Ndex2
            from ndex2.exceptions import NDExError

            client = Ndex2(username=<NDEx USER NAME>,
                           password=<NDEx PASSWORD>,
                           skip_version_check=True)

            # cx is set to an empty CX2 network
            cx = [{"CXVersion":"2.0","hasFragments":false},
                  {"status":[{"success":true}]}]

            try:
                cx_stream = io.BytesIO(json.dumps(cx,
                                                  cls=DecimalEncoder).encode('utf-8'))
                client.update_cx2_network(cx_stream, <UUID OF NETWORK TO UPDATE>)
                print('Success')
            except NDExError as ne:
                print('Caught error: ' + str(ne))


        :param cx_stream: The network stream.
        :param network_id: The UUID of the network.
        :type network_id: str
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :raises NDExError: If there is an error updating the network
        :return: Nothing is returned. To check status
                 call :py:func:`get_network_summary`
        """
        self._require_auth()
        fields = {
            'CXNetworkStream': ('filename', cx_stream, 'application/octet-stream')
        }

        try:
            # update endpoint has no output so do not return anything
            self.put_multipart('/networks/' + str(network_id), fields,
                               alt_version_endpoint=Ndex2.V3_ENDPOINT)
        except requests.HTTPError as he:
            self._convert_requests_http_error_to_ndex_error(he)
        except Exception as e:
            self._convert_exception_to_ndex_error(e)

    def get_network_as_cx_stream(self, network_id):
        """
        Get the existing network with UUID network_id from the NDEx connection as a CX stream.

        :param network_id: The UUID of the network.
        :type network_id: str
        :return: The response.
        :rtype: `response object <http://docs.python-requests.org/en/master/user/quickstart/#response-content>`_

        """

        if self.version.startswith('1.'):
            route = "/network/%s/asCX" % network_id
        else:
            route = "/network/%s" % network_id

        return self.get_stream(route)

    def get_network_as_cx2_stream(self, network_id, access_key=None):
        """
        Get the existing network with UUID network_id from the NDEx connection as CX2 stream
        contained within a :py:class:`requests.Response` object

        .. versionadded:: 3.5.0

        Example usage:

        .. code-block:: python

            from ndex2.client import Ndex2
            client = Ndex2(skip_version_check=True)

            # 7fc.. is UUID MuSIC v1 network: http://doi.org/10.1038/s41586-021-04115-9
            client_resp = client.get_network_as_cx2_stream('7fc70ab6-9fb1-11ea-aaef-0ac135e8bacf')

            # for HTTP status code, 200 means success
            print(client_resp.status_code)

            # for smaller networks one can get the CX2 by calling:
            print(client_resp.json())


        .. note::

            For retrieving larger networks see :py:meth:`requests.Response.iter_content`

            This method sets `stream=True` in the request to
            avoid loading response into memory.


        :param network_id: The UUID of the network
        :param access_key: Optional access key UUID
        :raises NDExError: If there was an error
        :return: Requests library response with CX2 in content and status
                 code of 200 upon success
        :rtype: :py:class:`requests.Response`
        """
        get_params = None
        if access_key is not None:
            get_params = {'accesskey': str(access_key)}
        try:
            return self.get_stream('/networks/' + str(network_id),
                                   get_params=get_params,
                                   alt_version_endpoint=Ndex2.V3_ENDPOINT)
        except requests.HTTPError as he:
            self._convert_requests_http_error_to_ndex_error(he)
        except Exception as e:
            self._convert_exception_to_ndex_error(e)

    def get_network_aspect_as_cx_stream(self, network_id, aspect_name):
        """
        Get the specified aspect of the existing network with UUID network_id from the NDEx connection as a CX stream.

        For a list of aspect names look at **Core Aspects** section of
        `CX Data Model Documentation <https://home.ndexbio.org/data-model/>`__

        :param network_id: The UUID of the network.
        :param aspect_name: The aspect NAME.
        :type network_id: str
        :return: The response.
        :rtype: `response object <http://docs.python-requests.org/en/master/user/quickstart/#response-content>`_

        """

        if self.version.startswith('1.'):
            route = "/network/%s/asCX" % network_id
        else:
            route = "/network/%s/aspect/%s" % (network_id, aspect_name)

        return self.get_stream(route)

    def get_network_aspect_as_cx2_stream(self, network_id, aspect_name=None,
                                         access_key=None, size=None):
        """
        Gets JSON array of CX2 elements from the aspect specified by **aspect_name** from the
        network specified by **network_id**

        .. versionadded:: 3.5.0

        Example usage:

        .. code-block:: python

            from ndex2.client import Ndex2
            client = Ndex2(skip_version_check=True)

            # 7fc.. is UUID MuSIC v1 network: http://doi.org/10.1038/s41586-021-04115-9
            client_resp = client.get_network_aspect_as_cx2_stream('7fc70ab6-9fb1-11ea-aaef-0ac135e8bacf', 'nodes')

            # for HTTP status code, 200 means success
            print(client_resp.status_code)

            # for smaller networks one can get the CX2 by calling:
            print(client_resp.json())


        .. note::

            For retrieving larger networks see :py:meth:`requests.Response.iter_content`

            This method sets `stream=True` in the request to
            avoid loading response into memory.


        :param network_id: The UUID of the network
        :type network_id: str
        :param aspect_name: Name of CX2 aspect.
                            Example aspects: ``nodes``, ``edges``,
                                             ``networkAttributes`` etc.
        :type aspect_name: str
        :param access_key: Optional access key UUID
        :param size: Denotes number of elements of given aspect to return. If < 0 or
                     ``None`` all elements will be returned
        :type size: int
        :raises NDExError: If there was an error
        :return: Requests library response with CX2 in content and status
                 code of 200 upon success
        :rtype: :py:class:`requests.Response`
        """
        get_params = None
        if access_key is not None:
            get_params = {'accesskey': str(access_key)}
        if size is not None:
            if get_params is None:
                get_params = {}
            get_params['size'] = size
        try:
            return self.get_stream('/networks/' + str(network_id) +
                                   '/aspects/' + str(aspect_name),
                                   get_params=get_params,
                                   alt_version_endpoint=Ndex2.V3_ENDPOINT)
        except requests.HTTPError as he:
            self._convert_requests_http_error_to_ndex_error(he)
        except Exception as e:
            self._convert_exception_to_ndex_error(e)

    def get_neighborhood_as_cx_stream(self, network_id, search_string, search_depth=1, edge_limit=2500, error_when_limit=True):
        """
        Get a CX stream for a subnetwork of the network specified by UUID network_id and a traversal of search_depth
        steps around the nodes found by search_string.

        :param network_id: The UUID of the network.
        :type network_id: str
        :param search_string: The search string used to identify the network neighborhood.
        :type search_string: str
        :param search_depth: The depth of the neighborhood from the core nodes identified.
        :type search_depth: int
        :param edge_limit: The maximum size of the neighborhood.
        :type edge_limit: int
        :param error_when_limit: Default value is true. If this value is true the server will stop streaming the network when it hits the edgeLimit, add success: false and error: "EdgeLimitExceeded" in the status aspect and close the CX stream. If this value is set to false the server will return a subnetwork with edge count up to edgeLimit. The status aspect will be a success, and a network attribute {"EdgeLimitExceeded": "true"} will be added to the returned network only if the server hits the edgeLimit..
        :type error_when_limit: bool
        :return: The response.
        :rtype: `response object <http://docs.python-requests.org/en/master/user/quickstart/#response-content>`_

        """
        if self.version.startswith('1.'):
            route = "/network/%s/query" % network_id
        else:
            route = "/search/network/%s/query" % network_id

        post_data = {'searchString': search_string,
                     'searchDepth': search_depth,
                     'edgeLimit': edge_limit,
                     'errorWhenLimitIsOver': error_when_limit}
        post_json = json.dumps(post_data)
        return self.post_stream(route, post_json=post_json)

    def get_neighborhood(self, network_id, search_string, search_depth=1, edge_limit=2500):
        """
        Get the CX for a subnetwork of the network specified by UUID network_id and a traversal of search_depth steps
        around the nodes found by search_string.

        :param network_id: The UUID of the network.
        :type network_id: str
        :param search_string: The search string used to identify the network neighborhood.
        :type search_string: str
        :param search_depth: The depth of the neighborhood from the core nodes identified.
        :type search_depth: int
        :param edge_limit: The maximum size of the neighborhood.
        :type edge_limit: int
        :return: The CX json object.
        :rtype: `response object <http://docs.python-requests.org/en/master/user/quickstart/#response-content>`_
        """
        if self.version.startswith('1.'):
            raise Exception("get_neighborhood is not supported for versions prior to 2.0, "
                            "use get_neighborhood_as_cx_stream")

        response = self.get_neighborhood_as_cx_stream(network_id, search_string, search_depth=search_depth,
                                                      edge_limit=edge_limit)

        response_json = response.json()
        if isinstance(response_json, dict):
            return response_json.get('data')
        elif isinstance(response_json, list):
            return response_json
        return response_json

    def get_interconnectquery_as_cx_stream(self, network_id, search_string,
                                           search_depth=1, edge_limit=2500,
                                           error_when_limit=True):
        """
        Get a CX stream for a neighborhood subnetwork where all the
        paths must start and end at one of the query nodes in the network
        specified by networkid.

        :param network_id: The UUID of the network.
        :type network_id: str
        :param search_string: The search string used to identify the network neighborhood.
        :type search_string: str
        :param search_depth: The depth of the neighborhood from the core nodes identified.
        :type search_depth: int
        :param edge_limit: The maximum size of the neighborhood.
        :type edge_limit: int
        :param error_when_limit: Default value is true. If this value is true the server will stop streaming the network when it hits the edgeLimit, add success: false and error: "EdgeLimitExceeded" in the status aspect and close the CX stream. If this value is set to false the server will return a subnetwork with edge count up to edgeLimit. The status aspect will be a success, and a network attribute {"EdgeLimitExceeded": "true"} will be added to the returned network only if the server hits the edgeLimit..
        :type error_when_limit: bool
        :return: The response.
        :rtype: `response object <http://docs.python-requests.org/en/master/user/quickstart/#response-content>`_

        """
        route = "/search/network/%s/interconnectquery" % network_id

        post_data = {'searchString': search_string,
                     'searchDepth': search_depth,
                     'edgeLimit': edge_limit,
                     'errorWhenLimitIsOver': error_when_limit}
        post_json = json.dumps(post_data)
        return self.post_stream(route, post_json=post_json)

    def get_interconnectquery(self, network_id, search_string,
                              search_depth=1, edge_limit=2500,
                              error_when_limit=True):
        """
        Gets a CX network for a neighborhood subnetwork where all the
        paths must start and end at one of the query nodes in the network
        specified by networkid.

        :param network_id: The UUID of the network.
        :type network_id: str
        :param search_string: The search string used to identify the network neighborhood.
        :type search_string: str
        :param search_depth: The depth of the neighborhood from the core nodes identified.
        :type search_depth: int
        :param edge_limit: The maximum size of the neighborhood.
        :type edge_limit: int
        :param error_when_limit: Default value is true. If this value is true the server will stop streaming the network when it hits the edgeLimit, add success: false and error: "EdgeLimitExceeded" in the status aspect and close the CX stream. If this value is set to false the server will return a subnetwork with edge count up to edgeLimit. The status aspect will be a success, and a network attribute {"EdgeLimitExceeded": "true"} will be added to the returned network only if the server hits the edgeLimit..
        :type error_when_limit: bool
        :return: The CX json object.
        :rtype: list
        """
        response = self.get_interconnectquery_as_cx_stream(network_id,
                                                           search_string,
                                                           search_depth=search_depth,
                                                           edge_limit=edge_limit,
                                                           error_when_limit=error_when_limit)
        response_json = response.json()
        if isinstance(response_json, dict):
            return response_json.get('data')
        elif isinstance(response_json, list):
            return response_json
        else:
            return response_json

    def search_networks(self, search_string="", account_name=None, start=0, size=100, include_groups=False):
        """
        Search for networks based on the search_text, optionally limited to networks owned by the specified
        account_name.

        :param search_string: The text to search for.
        :type search_string: str
        :param account_name: The account to search
        :type account_name: str
        :param start: The number of blocks to skip. Usually zero, but may be used to page results.
        :type start: int
        :param size: The size of the block.
        :type size: int
        :param include_groups:
        :type include_groups:
        :return: The response.
        :rtype: `response object <http://docs.python-requests.org/en/master/user/quickstart/#response-content>`_

        """
        post_data = {"searchString": search_string}
        if self.version.startswith('1.'):
            route = "/network/search/%s/%s" % (start, size)
        else:
            route = "/search/network?start=%s&size=%s" % (start, size)
            if include_groups:
                post_data["includeGroups"] = True

        if account_name:
            post_data["accountName"] = account_name
        post_json = json.dumps(post_data)
        return self.post(route, post_json)

    def search_network_nodes(self, network_id, search_string='', limit=5):
        post_data = {"searchString": search_string}
        if self.version.startswith('1.'):
            route = "/network/%s/nodes/%s" % (network_id, limit)
        else:
            route = "/search/network/%s/nodes?limit=%s" % (network_id, limit)

        post_json = json.dumps(post_data)
        return self.post(route, post_json)

    def find_networks(self, search_string="", account_name=None, skip_blocks=0, block_size=100):
        """
        .. deprecated:: 3.3.2
            Use :func:`search_networks` instead.

        :param search_string:
        :param account_name:
        :param skip_blocks:
        :param block_size:
        :return:
        """
        self.logger.warning("find_networks is deprecated, please use search_networks")
        return self.search_networks(search_string, account_name, skip_blocks, block_size)

    def search_networks_by_property_filter(self, search_parameter_dict={}, account_name=None, limit=100):
        raise Exception("This function is not supported in NDEx 2.0")

    def network_summaries_to_ids(self, network_summaries):
        network_ids = []
        for network in network_summaries:
            network_ids.append(network['externalId'])
        return network_ids

    def get_network_summary(self, network_id):
        """
        Gets information and status of a network

        Example usage:

        .. code-block:: python

            from ndex2.client import Ndex2
            client = Ndex2(skip_version_check=True)

            # 7fc.. is UUID MuSIC v1 network: http://doi.org/10.1038/s41586-021-04115-9
            net_sum = client.get_network_summary('7fc70ab6-9fb1-11ea-aaef-0ac135e8bacf')

            print(net_sum)


        Example result:

        .. code-block:: text

            {
              "ownerUUID": "daa09f36-8cdd-11e7-a10d-0ac135e8bacf",
              "isReadOnly": true,
              "subnetworkIds": [],
              "isValid": true,
              "warnings": [],
              "isShowcase": true,
              "doi": "10.18119/N9188W",
              "isCertified": true,
              "indexLevel": "ALL",
              "hasLayout": true,
              "hasSample": false,
              "cxFileSize": 82656,
              "cx2FileSize": 68979,
              "visibility": "PUBLIC",
              "nodeCount": 70,
              "edgeCount": 87,
              "completed": true,
              "version": "1.0",
              "owner": "yue",
              "description": "<div><br/></div><div>Two central approaches for mapping cellular structure \u2013 protein fluorescent imaging and protein biophysical association \u2013 each generate extensive datasets but of distinct qualities and resolutions that are typically treated separately. The MuSIC map is designed to address this challenge, by integrating immunofluorescent images in the Human Protein Atlas with ongoing affinity purification experiments from the BioPlex resource. The result is a unified hierarchical map of eukaryotic cell architecture. In the MuSIC hierarchy, nodes represent systems and arrows indicate containment of the lower system by the upper. Node color indicates known (gold) or putative novel (purple) systems. The size of each circle is based on the number of proteins in the system. The relative height of each system in the layout is determined based on the predicted diameter of the system in MuSIC.<br/></div>",
              "name": "Multi-Scale Integrated Cell (MuSIC) v1",
              "properties": [
                {
                  "subNetworkId": null,
                  "predicateString": "author",
                  "dataType": "string",
                  "value": "Yue Qin"
                },
                {
                  "subNetworkId": null,
                  "predicateString": "rights",
                  "dataType": "string",
                  "value": "MIT license (MIT)"
                },
                {
                  "subNetworkId": null,
                  "predicateString": "rightsHolder",
                  "dataType": "string",
                  "value": "Yue Qin"
                },
                {
                  "subNetworkId": null,
                  "predicateString": "reference",
                  "dataType": "string",
                  "value": "Yue Qin, Edward L. Huttlin, Casper F. Winsnes, Maya L. Gosztyla, Ludivine Wacheul, Marcus R. Kelly, Steven M. Blue, Fan Zheng, Michael Chen, Leah V. Schaffer, Katherine Licon, Anna B\u00e4ckstr\u00f6m, Laura Pontano Vaites, John J. Lee, Wei Ouyang, Sophie N. Liu, Tian Zhang, Erica Silva, Jisoo Park, Adriana Pitea, Jason F. Kreisberg, Steven P. Gygi, Jianzhu Ma, J. Wade Harper, Gene W. Yeo, Denis L. J. Lafontaine, Emma Lundberg, Trey Ideker<br><strong>A multi-scale map of cell structure fusing protein images and interactions</strong><br><i>Nature 600, 536\u2013542 (2021).</i>, (2021)<br><a href=\"http://doi.org/10.1038/s41586-021-04115-9\"  target=\"_blank\">10.1038/s41586-021-04115-9</a>"
                }
              ],
              "externalId": "7fc70ab6-9fb1-11ea-aaef-0ac135e8bacf",
              "isDeleted": false,
              "modificationTime": 1630270298717,
              "creationTime": 1590539529001
            }

        .. note::

            **isvalid** is a boolean to denote that the network was inspected, not
            that it is actually valid.

            **errorMessage** Will be in result if there was an error parsing network

            **completed** is set to ``True`` after all server tasks have completed and
            network is ready to be used

        :param network_id: The UUID of the network
        :type network_id: str
        :return: Summary information about network
        :rtype: dict

        """
        if self.version.startswith('1.'):
            route = "/network/%s" % network_id
        else:
            route = "/network/%s/summary" % network_id

        return self.get(route)

    def make_network_public(self, network_id):
        """
        Makes the network specified by the **network_id** public
        by invoking :py:func:`set_network_system_properties` with

        ``{'visibility': 'PUBLIC'}``

        :param network_id: The UUID of the network.
        :type network_id: str
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :raises requests.exception.HTTPError: If there is some other error
        :return: empty string upon success
        :rtype: str
        """
        if self.version.startswith('1.'):
            return self.update_network_profile(network_id, {'visibility': 'PUBLIC'})

        return self.set_network_system_properties(network_id, {'visibility': 'PUBLIC'})

    def _make_network_public_indexed(self, network_id):
        """
        Makes the network specified by the **network_id** public
        by invoking :py:func:`set_network_system_properties` with

        ``{'visibility': 'PUBLIC', 'index_level': 'ALL', 'showcase': True}``

        :param network_id: The UUID of the network.
        :type network_id: str
        :raises NDExUnsupportedCallError: If version of NDEx server is < 2
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :raises requests.exception.HTTPError: If there is some other error
        :return: empty string upon success
        :rtype: str
        """
        if self.version.startswith('1.'):
            raise NDExUnsupportedCallError('Only 2+ of NDEx supports '
                                           'setting/changing index level')

        return self.set_network_system_properties(network_id,
                                                  {'visibility': 'PUBLIC',
                                                   'index_level': 'ALL',
                                                   'showcase': True})

    def make_network_private(self, network_id):
        """
        Makes the network specified by the **network_id** private
        by invoking :py:func:`set_network_system_properties` with

        ``{'visibility': 'PRIVATE'}``

        :param network_id: The UUID of the network.
        :type network_id: str
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :raises requests.exception.HTTPError: If there is some other error
        :return: empty string upon success
        :rtype: str

        """
        if self.version.startswith('1.'):
            return self.update_network_profile(network_id,
                                               {'visibility': 'PRIVATE'})

        return self.set_network_system_properties(network_id,
                                                  {'visibility': 'PRIVATE'})

    def get_task_by_id(self, task_id):
        """
        Retrieves a task by id

        :param task_id: Task id
        :type task_id: str
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :return: Task
        :rtype: dict
        """
        self._require_auth()
        route = "/task/%s" % task_id
        return self.get(route)

    def delete_network(self, network_id, retry=5):
        """
        Deletes the specified network from the server

        :param network_id: Network id
        :type network_id: str
        :param retry: Number of times to retry if deleting fails
        :type retry: int
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :return: Error json if there is an error.  Blank
        :rtype: str
        """
        self._require_auth()
        route = "/network/%s" % network_id
        count = 0
        while count < retry:
            try:
                return self.delete(route)
            except Exception as inst:
                d = json.loads(inst.response.content)
                if d.get('errorCode').startswith("NDEx_Concurrent_Modification"):
                    self.logger.debug("retry deleting network in 1 second(" + str(count) + ")")
                    count += 1
                    time.sleep(1)
                else:
                    raise inst
        raise Exception("Network is locked after " + str(retry) + " retry.")

    def get_provenance(self, network_id):
        """
        Gets the network provenance

        .. deprecated:: 3.3.2
            This method has been deprecated.

        :param network_id: Network id
        :type network_id: str
        :return: Provenance
        :rtype: dict
        """
        route = "/network/%s/provenance" % network_id
        return self.get(route)

    def set_provenance(self, network_id, provenance):
        """
        Sets the network provenance

        .. deprecated:: 3.3.2
            This method has been deprecated.

        :param network_id: Network id
        :type network_id: str
        :param provenance: Network provcenance
        :type provenance: dict
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :return: Result
        :rtype: dict
        """
        self._require_auth()
        route = "/network/%s/provenance" % network_id
        if isinstance(provenance, dict):
            put_json = json.dumps(provenance)
        else:
            put_json = provenance
        return self.put(route, put_json)

    def set_read_only(self, network_id, value):
        """
        Sets the read only flag to **value** on the network specified by
        **network_id**

        :param network_id: Network id
        :type network_id: str
        :param value: Must :py:const:`True` for read only, :py:const:`False` otherwise
        :type value: bool
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :raises NDExInvalidParameterError: If non bool is set in
                                           **valid** parameter
        :raises requests.exception.HTTPError: If there is some other error
        :return: empty string upon success
        :rtype: str
        """
        return self.set_network_system_properties(network_id,
                                                  {"readOnly": value})

    def set_network_properties(self, network_id, network_properties):
        """
        Updates properties of network

        Starting with version 2.5 of NDEx, any network properties
        not in the `network_properties` parameter are left unchanged.

        .. warning::

            ``name, description, version`` network attributes/properties cannot be updated by this method.
            Please use :py:func:`update_network_profile` to update these values.

        The format of `network_properties` should be a :py:func:`list` of :py:func:`dict`
        objects in this format:

        .. code-block::

            [{
                'subNetworkId': '',
                'predicateString': '',
                'dataType': '',
                'value': ''
            }]

        The ``predicateString`` field above is the network attribute/property name.

        The ``dataType`` field above must be one of the following
        `types <https://ndex2.readthedocs.io/en/latest/ndex2.html?highlight=list_of_string#supported-data-types>`__

        Regardless of ``dataType``, ``value`` should be converted to :py:func:`str` or :py:func:`list` of
        :py:func:`str`

        For more information please visit the underlying
        `REST call documentation <http://openapi.ndextools.org/#/Network/put_network__networkid__properties>`__

        Example to add two network properties (``foo``, ``bar``):

        .. code-block::

                [{
                'subNetworkId': '',
                'predicateString': 'foo',
                'dataType': 'list_of_integer',
                'value': ['1', '2', '3']
                },{
                'subNetworkId': '',
                'predicateString': 'bar',
                'dataType': 'string',
                'value': 'a value for bar as str'
                }]


        :param network_id: Network id
        :type network_id: str
        :param network_properties: List of NDEx property value pairs aka network
                                   properties to set on the network. This can
                                   also be a :py:func:`str` in JSON format
        :type network_properties: list or str
        :raises Exception: If `network_properties` is not a :py:func:`str` or
                           :py:func:`list`
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :raises requests.HTTPError: If there is an error with the request or
                                    if ``name, version, description`` is set
                                    in `network_properties` as a value to
                                    ``predicateString``
        :return: Empty string or ``1``
        :rtype: str or int
        """
        self._require_auth()
        route = "/network/%s/properties" % network_id
        if isinstance(network_properties, list):
            put_json = json.dumps(network_properties)
        elif isinstance(network_properties, str):
            put_json = network_properties
        else:
            raise Exception("network_properties must be a string or a list "
                            "of NdexPropertyValuePair objects")
        return self.put(route, put_json)

    def get_sample_network(self, network_id):
        """
        Gets the sample network

        :param network_id: Network id
        :type network_id: str
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :return: Sample network in CX format
        :rtype: list
        """
        route = "/network/%s/sample" % network_id
        return self.get(route)

    def set_network_sample(self, network_id, sample_cx_network_str):
        """

        :param network_id:
        :param sample_cx_network_str:
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :return:
        """
        self._require_auth()
        route = "/network/%s/sample" % network_id
    #    putJson = json.dumps(sample_cx_network_str)
        return self.put(route, sample_cx_network_str)

    def _validate_network_system_properties(self, network_properties,
                                            skipvalidation=False):
        """
        Verifies 'network_properties' passed in is a valid dict that
        can be set as network system properties. The dict should
        be of format:

        {'showcase': (boolean True or False),
         'visibility': (str set to 'PUBLIC' or 'PRIVATE'),
         'index_level': (str set to 'NONE', 'META', 'ALL'),
         'readOnly': (boolean True or False)}

        :param network_properties:
        :type network_properties: dict
        :raises NDExInvalidParameterError: If 'network_properties' is invalid
        :return: JSON string of 'network_properties'
        :rtype: str
        """

        if isinstance(network_properties, dict):
            net_props = network_properties
        elif isinstance(network_properties, str):
            try:
                net_props = json.loads(network_properties)
            except Exception as e:
                raise NDExInvalidParameterError('Error parsing json string: ' +
                                                str(network_properties) +
                                                ' : ' + str(e))
        else:
            raise NDExInvalidParameterError("network_properties must be "
                                            "a string or a dict")

        if skipvalidation is not None and skipvalidation is True:
            return json.dumps(net_props)

        if len(net_props.keys()) == 0:
            raise NDExInvalidParameterError('network_properties '
                                            'appears to be empty')

        for key in net_props.keys():
            if key not in Ndex2.VALID_NETWORK_SYSTEM_PROPERTIES:
                raise NDExInvalidParameterError(key + ' is not a valid network '
                                                      'system property')
            if key == 'readOnly' or key == 'showcase':
                if not isinstance(net_props[key], bool):
                    raise NDExInvalidParameterError(key + ' value must be a '
                                                          'bool set to True '
                                                          'or False')
            elif key == 'index_level':
                if not isinstance(net_props[key], str) \
                        or net_props[key] not in ['NONE', 'META', 'ALL']:
                    raise NDExInvalidParameterError(key + ' value must be a '
                                                          'string set to '
                                                          'NONE, META, or ALL')
            elif key == 'visibility':
                if not isinstance(net_props[key], str) \
                        or net_props[key] not in ['PUBLIC', 'PRIVATE']:
                    raise NDExInvalidParameterError(key + ' value must be a '
                                                          'string set to '
                                                          'PUBLIC or PRIVATE')
        return json.dumps(net_props)

    def set_network_system_properties(self, network_id, network_properties,
                                      skipvalidation=False):
        """
        Set network system properties on network with UUID specified by
        **network_id**

        The network properties should be a :py:func:`dict` or a json string of a :py:func:`dict`
        in this format:

        .. code-block:: python

            {'showcase': (boolean True or False),
             'visibility': (str 'PUBLIC' or 'PRIVATE'),
             'index_level': (str  'NONE', 'META', or 'ALL'),
             'readOnly': (boolean True or False)
            }

        .. note::

            Omit any values from :py:func:`dict` that you do NOT want changed

        Definition of **showcase** values:

            :py:const:`True` - means network will display in her home page for other users and :py:const:`False` hides the network for other users. where other users includes anonymous users

        Definition of **visibility** values:

            'PUBLIC' - means it can be found or read by anyone, including anonymous users

            'PRIVATE' - is the default, means that it can only be found or read by users according to their permissions

        Definition of **index_level** values:

            'NONE' - no index

            'META' - only index network attributes

            'ALL' - full index on the network

        Definition of **readOnly** values:

            :py:const:`True` - means network is only readonly, False is NOT readonly

        This method will validate **network_properties** matches above :py:func:`dict`
        unless **skipvalidation** is set to :py:const:`True` in which case the code
        only verifies the **network_properties** is valid JSON

        :param network_id: Network id
        :type network_id: str
        :param network_properties: Network properties as :py:func:`dict` or a JSON string
                                   of :py:func:`dict` adhering to structure above.
        :type network_properties: dict or str
        :param skipvalidation: If :py:const:`True`, only verify **network_properties**
                               can be parsed/converted to valid JSON
        :raises NDExUnsupportedCallError: If version of NDEx server is < 2
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :raises NDExInvalidParameterError: If invalid data is set in
                                           **network_properties** parameter
        :raises requests.exception.HTTPError: If there is some other error
        :return: empty string upon success
        :rtype: str
        """
        if self.version.startswith('1.'):
            raise NDExUnsupportedCallError('This call only works with NDEx 2+')

        self._require_auth()
        route = "/network/%s/systemproperty" % network_id

        # check that the properties are valid
        put_json = self._validate_network_system_properties(network_properties,
                                                            skipvalidation=
                                                            skipvalidation)
        return self.put(route, put_json)

    def update_network_profile(self, network_id, network_profile):
        """
        Updates the network profile
        Any profile attributes specified will be updated but attributes that are not specified will
        have no effect - omission of an attribute does not mean deletion of that attribute.
        The network profile attributes that can be updated by this method are: 'name', 'description' and 'version'.

        .. code-block:: python

            {
              "name": "string",
              "description": "string",
              "version": "string",
              "visibility": "string",
              "properties": [
                {
                  "subNetworkId": "",
                  "predicateString": "string",
                  "dataType": "string",
                  "value": "string"
                }
              ]
            }

        :param network_id: Network id
        :type network_id: str
        :param network_profile: Network profile
        :type network_profile: dict
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :return:
        :rtype:
        """

        self._require_auth()
        if isinstance(network_profile, dict):
            if network_profile.get("visibility") and self.version.startswith("2."):
                raise Exception("Ndex 2.x doesn't support setting visibility by this function. "
                                "Please use make_network_public/private function to set network visibility.")
            json_data = json.dumps(network_profile)
        elif isinstance(network_profile, str):
            json_data = network_profile
        else:
            raise Exception("network_profile must be a string or a dict")

        if self.version.startswith('1.'):
            route = "/network/%s/summary" % network_id
            return self.post(route, json_data)
        else:
            route = "/network/%s/profile" % network_id
            return self.put(route, json_data)

    def upload_file(self, filename):
        raise NDExError("This function is not supported in this release. Please use the save_new_network "
                        "function to create new networks in NDEx server.")

    def update_network_group_permission(self, groupid, networkid, permission):
        """
        Updated group permissions

        :param groupid: Group id
        :type groupid: str
        :param networkid: Network id
        :type networkid: str
        :param permission: Network permission
        :type permission: str
        :return: Result
        :rtype: dict
        """
        route = "/network/%s/permission?groupid=%s&permission=%s" % (networkid, groupid, permission)
        self.put(route)

    def update_network_user_permission(self, userid, networkid, permission):
        """
        Updated network user permission

        :param userid: User id
        :type userid: str
        :param networkid: Network id
        :type networkid: str
        :param permission: Network permission
        :type permission: str
        :return: Result
        :rtype: dict
        """
        route = "/network/%s/permission?userid=%s&permission=%s" % (networkid, userid, permission)
        self.put(route)

    def grant_networks_to_group(self, groupid, networkids, permission="READ"):
        """
        Set group permission for a set of networks

        :param groupid: Group id
        :type groupid: str
        :param networkids: List of network ids
        :type networkids: list
        :param permission: Network permission
        :type permission: str
        :return: Result
        :rtype: dict
        """
        for networkid in networkids:
            self.update_network_group_permission(groupid, networkid, permission)

    def get_id_for_user(self, username):
        """
        Gets NDEx user Id for user

        .. versionadded:: 3.4.0

        .. code-block:: python

            import ndex2.client
            my_ndex = ndex2.client.Ndex2()
            my_ndex.get_id_for_user('nci-pid')

        :param username: Name of user on NDEx. If ``None`` user set in
                         constructor of this client will be used.
        :type username: str
        :raises NDExError: If there was an error on the server.
        :raises NDExInvalidParameterError: If username is empty string or is
                                           of type other then str.
        :return: Id of user on NDEx server.
        :rtype: str
        """
        if username is None:
            username = self.username
            if username is None:
                raise NDExInvalidParameterError('None passed in this method and '
                                                'no user found via constructor '
                                                'of this client')
        if not isinstance(username, str):
            raise NDExInvalidParameterError('Username must be of type str')

        if username == '':
            raise NDExInvalidParameterError('Username cannot be empty str')

        try:
            user_json = self.get_user_by_username(username)
        except requests.HTTPError as he:
            self._convert_requests_http_error_to_ndex_error(he)
        except Exception as e:
            self._convert_exception_to_ndex_error(e)
        if 'externalId' not in user_json:
            raise NDExError('Unable to get user id for user: ' + str(username))
        return user_json['externalId']

    def get_user_by_username(self, username):
        """
        Gets user information from NDEx.

        Example user information:

        .. code-block:: python

            {'properties': {},
             'isIndividual': True,
             'userName': 'bsmith',
             'isVerified': True,
             'firstName': 'bob',
             'lastName': 'smith',
             'emailAddress': 'bob.smith@ndexbio.org',
             'diskQuota': 10000000000,
             'diskUsed': 3971183103,
             'externalId': 'f2c3a7ef-b0d9-4c61-bf31-4c9fcabe4173',
             'isDeleted': False,
             'modificationTime': 1554410147104,
             'creationTime': 1554410138498
            }

        :param username: User name
        :type username: str
        :return: User information as dict
        :rtype: dict
        """
        route = "/user?username=%s" % username
        return self.get(route)

    def get_user_by_id(self, user_id):
        """
        Gets user matching id from NDEx server.

        .. versionadded:: 3.4.0

        Result is a dict in format:

        .. code-block:: python

            {'properties': {},
             'isIndividual': True,
             'userName': 'bsmith',
             'isVerified': True,
             'firstName': 'bob',
             'lastName': 'smith',
             'emailAddress': 'bob.smith@ndexbio.org',
             'diskQuota': 10000000000,
             'diskUsed': 3971183103,
             'externalId': 'f2c3a7ef-b0d9-4c61-bf31-4c9fcabe4173',
             'isDeleted': False,
             'modificationTime': 1554410147104,
             'creationTime': 1554410138498
            }

        :param user_id: Id of user on NDEx server
        :type user_id: str
        :raises NDExError: If there was an error on the server
        :raises NDExInvalidParameterError: If user_id is not of
                                           type str or if empty str
        :return: user object. `externalId` is Id of user on NDEx server
        :rtype: dict
        """
        if user_id is None or not isinstance(user_id, str):
            raise NDExInvalidParameterError('user_id must be a str')

        if user_id == '':
            raise NDExInvalidParameterError('user_id cannot be an empty str')
        try:
            route = '/user/' + str(user_id)
            return self.get(route)
        except requests.HTTPError as he:
            self._convert_requests_http_error_to_ndex_error(he)
        except Exception as e:
            self._convert_exception_to_ndex_error(e)

    def get_network_summaries_for_user(self, username):
        """
        Wrapper that calls :func:`get_user_network_summaries`

        See :func:`get_user_network_summaries` for usage

        :param username: NDEx username
        :return: List of dict objects containing network summaries
        :rtype: list
        """
        return self.get_user_network_summaries(username)

    def get_user_network_summaries(self, username, offset=0, limit=1000):
        """
        Get a list of network summaries for networks owned by specified user.
        It returns not only the networks that the user owns but also the
        networks that are shared with them directly.
        As set via **limit** parameter only the first ``1,000`` ids are
        returned. The **offset** parameter combined with **limit**
        parameter provides pagination support.

        :param username: Username of the network owner
        :type username: str
        :param offset: Starting position of the network search
        :type offset: int
        :param limit: Number of summaries to return starting from `offset`
        :type limit: int
        :return: List of uuids
        :rtype: list
        """
        user = self.get_user_by_username(username)
        if self.version.startswith('1.'):
            route = "/user/%s/networksummary/asCX?offset=%s&limit=%s" % (user['externalId'], offset, limit)
        else:
            route = "/user/%s/networksummary?offset=%s&limit=%s" % (user['externalId'], offset, limit)

        network_summaries = self.get_stream(route)

        if network_summaries:
            return network_summaries.json()
        else:
            return None

    def get_network_ids_for_user(self, username, offset=0, limit=1000):
        """
        Get the network UUIDs owned by the user as well as any
        networks shared with the user. As set via **limit** parameter
        only the first ``1,000`` ids are returned. The **offset** parameter
        combined with **limit** provides pagination support.

        .. versionchanged:: 3.4.0
            **offset** and **limit** parameters added.

        :param username: NDEx username
        :type username: str
        :param offset: Starting position of the query. If set, **limit** parameter
                       must be set to a positive value.
        :type offset: int
        :param limit: Number of summaries to return starting from **offset**
                      If set to ``None`` or ``0`` all summaries will be
                      returned.
        :type limit: int
        :raises NDExInvalidParameterError: If **offset**/**limit** parameters
                                           are not of type int.
                                           If **offset** parameter
                                           is set to positive number and
                                           **limit** is ``0`` or
                                           negative.
        :return: List of uuids as str
        :rtype: list
        """
        if limit is None:
            limit = 0
        if offset is None:
            offset = 0

        if not isinstance(limit, int):
            raise NDExInvalidParameterError('Limit must be an int')

        if not isinstance(offset, int):
            raise NDExInvalidParameterError('Offset must be an int')

        if limit <= 0:
            if offset > 0:
                raise NDExInvalidParameterError('Limit must be set to a '
                                                'positive number '
                                                'to use offset')
        network_summaries = self.get_user_network_summaries(username,
                                                            offset=offset,
                                                            limit=limit)

        return self.network_summaries_to_ids(network_summaries)

    def grant_network_to_user_by_username(self, username, network_id, permission):
        """
        Grants permission to network for the given user name

        :param username: User name
        :type username: str
        :param network_id: Network id
        :type network_id: str
        :param permission: Network permission
        :type permission: str
        :return: Result
        :rtype: dict
        """
        user = self.get_user_by_username(username).json
        self.update_network_user_permission(user["externalid"], network_id, permission)

    def grant_networks_to_user(self, userid, networkids, permission="READ"):
        """
        Gives read permission to specified networks for the provided user

        :param userid: User id
        :type userid: str
        :param networkids: Network ids as str
        :type networkids: list
        :param permission: Network permissions
        :type permission: str (default is READ)
        :return: None
        :rtype: None
        """
        for networkid in networkids:
            self.update_network_user_permission(userid, networkid, permission)

    def update_status(self):
        """
        Updates the admin status, storing the status in the client
        object self.status

        :return: None
        """
        route = "/admin/status"
        self.status = self.get(route)

    def create_networkset(self, name, description):
        """
        Creates a new network set

        :param name: Network set name
        :type name: str
        :param description: Network set description
        :type description: str
        :return: URI of the newly created network set
        :rtype: str
        """
        route = '/networkset'
        return self.post(route, json.dumps({"name": name,
                                            "description": description}))

    def get_network_set(self, set_id):
        """
        Gets the network set information including the list of networks

        .. deprecated:: 3.2.0
            Use :func:`get_networkset` instead.

        :param set_id: network set id
        :type set_id: str
        :return: network set information
        :rtype: dict
        """
        return self.get_networkset(set_id)

    def get_networkset(self, set_id):
        """
        Gets the network set information including the list of networks

        :param set_id: network set id
        :type set_id: str
        :return: network set information
        :rtype: dict
        """
        route = '/networkset/%s' % set_id

        return self.get(route)

    def get_networksets_for_user_id(self, user_id, summary_only=True,
                                    showcase=False, offset=0,
                                    limit=0):
        """
        Gets a list of Network Set objects owned by the user
        identified by **user_id**

        .. versionadded:: 3.4.0

        Example when **summary_only** is ``True`` or if Network Set
        does not contain any networks:

        .. code-block:: python

            [
             {'name': 'test networkset',
              'description': ' ',
              'ownerId': '4f0a6356-ed4a-49df-bd81-098fee90b448',
              'showcased': False,
              'properties': {},
              'externalId': '956e31e8-f25c-471f-8596-2cae8348dcad',
              'isDeleted': False,
              'modificationTime': 1568844043868,
              'creationTime': 1568844043868
             }
            ]

        When **summary_only** is ``False`` and Network Set does
        contain networks there will be an additional property named
        ``networks``:

        .. code-block:: python

             'networks': ['face63b6-aba7-11eb-9e72-0ac135e8bacf',
                          'fae4d1e8-aba7-11eb-9e72-0ac135e8bacf']


        :param user_id: Id of user on NDEx. To get Id of user see
                        :py:func:`get_id_for_user`
        :type user_id: str
        :param summary_only: When ``True``, the server will not return the
                             list of network IDs in this Network Set
        :type summary_only: bool
        :param showcase: When ``True``, only showcased Network Sets are
                         returned
        :type showcase: bool
        :param offset: Index to first object to return. If ``0``/``None``
                       no offset will be applied. If this parameter is set
                       to a positive value then **limit** parameter must be
                       set to a positive value or this offset will be ignored.
        :type offset: int
        :param limit: Number of objects to retrieve. If ``0``, ``None``, or
                      negative all results will be returned.
        :type limit: int
        :raises NDExInvalidParameterError: If **user_id** parameter is not of
                                           type str.
                                           If **offset**/**limit** parameters
                                           are not ``None`` or of type int.
                                           If **offset** parameter
                                           is set to positive number and
                                           **limit** is ``0``, ``None``, or
                                           negative.
        :raises NDExError: If there is an error from server
        :return: list with dict objects containing Network Sets
        :rtype: list
        """
        if user_id is None or not isinstance(user_id, str):
            raise NDExInvalidParameterError('user_id must be of type str')

        params = {}
        if limit is not None:
            if not isinstance(limit, int):
                raise NDExInvalidParameterError('limit parameter must be of '
                                                'type int ' +
                                                str(type(limit)))
            params['limit'] = limit
        if offset is not None:
            if not isinstance(offset, int):
                raise NDExInvalidParameterError('offset parameter must be of '
                                                'type int ' +
                                                str(type(offset)))
            if limit is None or limit <= 0:
                if offset > 0:
                    raise NDExInvalidParameterError('limit (' + str(limit) +
                                                    ') parameter must be set '
                                                    'to positive value when '
                                                    'using offset parameter '
                                                    'set to (' +
                                                    str(offset) + ')')
            params['offset'] = offset
        if summary_only is not None:
            params['summary'] = summary_only
        if showcase is not None:
            params['showcase'] = showcase

        try:
            return self.get('/user/' + str(user_id) + '/networksets',
                            get_params=params)
        except requests.HTTPError as he:
            self._convert_requests_http_error_to_ndex_error(he)
        except Exception as e:
            self._convert_exception_to_ndex_error(e)

    def delete_networkset(self, networkset_id):
        """
        Deletes the network set, requires credentials

        :param networkset_id: networkset UUID id
        :type networkset_id: str
        :raises NDExInvalidParameterError: for invalid networkset id parameter
        :raises NDExUnauthorizedError: If no credentials or user is not authorized
        :raises NDExNotFoundError: If no networkset with id passed in found
        :raises NDExError: For any other error with contents of error in message
        :return: None upon success
        """
        if networkset_id is None:
            raise NDExInvalidParameterError('networkset id cannot be None')
        if not isinstance(networkset_id, str):
            raise NDExInvalidParameterError('networkset id must be a string')

        self._require_auth()
        route = '/networkset/%s' % networkset_id
        res = self.delete(route, raiseforstatus=False,
                          returnfullresponse=True)

        if res.status_code == 204 or res.status_code == 200:
            return None

        if res.status_code == 401:
            raise NDExUnauthorizedError('Not authorized')
        if res.status_code == 404:
            raise NDExNotFoundError('Network set with id: ' +
                                    str(networkset_id) + ' not found')

        msg = 'Unknown error server returned ' \
              'status code: ' + str(res.status_code)
        try:
            jsondata = res.json()
            msg += ' : ' + json.dumps(jsondata)
        except Exception:
             pass

        raise NDExError(msg)

    def add_networks_to_networkset(self, set_id, networks):
        """
        Add networks to a network set.  User must have visibility of all networks being added

        :param set_id: network set id
        :type set_id: str
        :param networks: networks (ids as str) that will be added to the set
        :type networks: list
        :return: None
        :rtype: None
        """

        route = '/networkset/%s/members' % set_id

        post_json = json.dumps(networks)
        return self.post(route, post_json)

    def delete_networks_from_networkset(self, set_id, networks, retry=5):
        """
        Removes network(s) from a network set.

        :param set_id: network set id
        :type set_id: str
        :param networks: networks (ids as str) that will be removed from the set
        :type networks: list
        :param retry: Number of times to retry
        :type retry: int
        :return: None
        :rtype: None
        """

        route = '/networkset/%s/members' % set_id
        post_json = json.dumps(networks)
        headers = self.s.headers
        headers['Content-Type'] = 'application/json;charset=UTF-8'
        headers['Accept'] = 'application/json'
        headers['User-Agent'] = userAgent + self.user_agent

        count = 0
        while count < retry:
            try:
                return self.delete(route, data=post_json)
            except Exception as inst:
                d = json.loads(inst.response.content)
                if d.get('errorCode').startswith("NDEx_Concurrent_Modification"):
                    self.logger.debug("retry deleting network in 1 second(" + str(count) + ")")
                    count += 1
                    time.sleep(1)
                else:
                    raise inst
        raise Exception("Network is locked after " + str(retry) + " retry.")


class DecimalEncoder(json.JSONEncoder):
    """
    Custom :py:class:`json.JSONEncoder` that handles
    :py:class:`numpy.integer`, :py:class:`decimal.Decimal`, and
    :py:class:`bytes` that can appear in CX data
    """

    def default(self, o):
        """
        Overrides default behavior by
        converting :py:class:`numpy.integer` to :py:class:`int`,
        :py:class:`decimal.Decimal` to :py:class:`float`, and
        :py:class:`bytes` to ascii decoded :py:class:`str` and
        defaults to :py:meth:`json.JSONEncoder` for all other
        object types for **o**

        :param o: object to convert
        :return: converted object **o**
        """
        if isinstance(o, decimal.Decimal):
            return float(o)
        elif isinstance(o, numpy.integer):
            return int(o)
        elif isinstance(o, bytes):
            bytes_string = o.decode('ascii')
            return bytes_string
        return super(DecimalEncoder, self).encode(o)