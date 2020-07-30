#!/usr/bin/env python

import requests
import json
import logging
from requests_toolbelt import MultipartEncoder
import io
import decimal
import time
import numpy

from ndex2.version import __version__
from ndex2 import constants
from ndex2.exceptions import NDExInvalidCXError
from ndex2.exceptions import NDExUnauthorizedError
from ndex2.exceptions import NDExError
from ndex2.exceptions import NDExLockedError
from ndex2.exceptions import NDExServerError
from ndex2.exceptions import NDExInvalidParameterError
from ndex2.exceptions import NDExNotFoundError


class Ndex2(object):
    """ A class to facilitate communication with a
        `NDEx REST server <https://ndexbio.org>`_.

    """
    USER_AGENT_KEY = 'User-Agent'
    VALID_NETWORK_SYSTEM_PROPERTIES = ['showcase', 'visibility',
                                       'index_level', 'readOnly']
    USER_AGENT = constants.USERAGENT_PREFIX + __version__

    def __init__(self, host=None, username=None, password=None,
                 update_status=False, debug=False, user_agent='',
                 timeout=30):
        """

        Example creating anonymous connection:

        .. code-block:: python

            from ndex2 import client
            anon_ndex = client.Ndex2()


        Example creating connection with username and password:

        .. code-block:: python

            from ndex2 import client
            my_ndex = client.Ndex2(username='your account', password='your password')


        Example creating connection to alternate host with username and password:

        .. code-block:: python

            from ndex2 import client
            my_ndex = client.Ndex2(host='https://localhost/v2', username='your account',\
                          password='your password')
        .. note::

          If `host` parameter is set it must be the full URL to REST server.
          For production `NDEx REST server <https://ndexbio.org>`_ it is
          the value of: :py:data:`~ndex2.constants.DEFAULT_SERVER`

        :param host: The full URL of NDEx REST service endpoint. If set to `None` \
                     :py:data:`~ndex2.constants.DEFAULT_SERVER` is used.
        :type host: str
        :param username: The username of the NDEx account to use. (Optional)
        :type username: str
        :param password: The account password. (Optional)
        :type password: str
        :param update_status: This variable is deprecated and is ignored
        :type update_status: bool
        :param user_agent: String to append to
                           `User-Agent <https://tools.ietf.org/html/rfc1945#page-46>`_
                           header sent with all requests to server
        :type user_agent: str
        :param timeout: The timeout in seconds value for requests to server. This value
                        is passed to Request calls `Click here for more information
                        <http://docs.python-requests.org/en/master/user/advanced/#timeouts>`_
        :type timeout: float or tuple(float, float)
        """
        self.debug = debug
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
            self.host = constants.DEFAULT_SERVER
        else:
            self.host = host

        # create a session for this Ndex object
        self.s = requests.Session()
        if username and password:
            # add credentials to the session, if available
            self.s.auth = (username, password)

# Base methods for making requests to this NDEx

    def close(self):
        """
        Closes session associated with this object

        .. versionadded:: 4.0.0
        :return:
        """
        if self.s is not None:
            self.s.close()

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
        return Ndex2.USER_AGENT + self.user_agent

    def _return_response(self, response,
                         raiseforstatus=True,
                         returnfullresponse=False,
                         returnjsonundertry=False):
        """
        Given a response from service request
        this method returns response.json() if the
        headers content-type is application/json otherwise
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
        if response.headers['content-type'] == 'application/json':
            return response.json()
        else:
            return response.text

    def put(self, route, put_json=None,
            raiseforstatus=True,
            returnfullresponse=False,
            returnjsonundertry=False):
        url = self.host + route
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
        return self._return_response(response, raiseforstatus=raiseforstatus,
                                     returnfullresponse=returnfullresponse,
                                     returnjsonundertry=returnjsonundertry)

    def post(self, route, post_json,
             raiseforstatus=True,
             returnfullresponse=False,
             returnjsonundertry=False):
        url = self.host + route
        self.logger.debug("POST route: " + url)
        self.logger.debug("POST json: " + post_json)
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json,text/plain',
                   'Cache-Control': 'no-cache',
                   Ndex2.USER_AGENT_KEY: self._get_user_agent(),
                   }
        response = self.s.post(url, data=post_json, headers=headers,
                               timeout=self.timeout)
        return self._return_response(response,
                                     raiseforstatus=raiseforstatus,
                                     returnfullresponse=returnfullresponse,
                                     returnjsonundertry=returnjsonundertry)

    def delete(self, route, data=None,
               raiseforstatus=True,
               returnfullresponse=False,
               returnjsonundertry=False):
        url = self.host + route
        self.logger.debug("DELETE route: " + url)
        headers = self.s.headers
        headers[Ndex2.USER_AGENT_KEY] = self._get_user_agent()
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

    def get(self, route, get_params=None,
            raiseforstatus=True,
            returnfullresponse=False,
            returnjsonundertry=False):
        url = self.host + route
        self.logger.debug("GET route: " + url)
        headers = self.s.headers
        headers[Ndex2.USER_AGENT_KEY] = self._get_user_agent()
        headers['Connection'] = 'close'
        response = self.s.get(url, params=get_params, headers=headers,
                              timeout=self.timeout)
        return self._return_response(response,
                                     raiseforstatus=raiseforstatus,
                                     returnfullresponse=returnfullresponse,
                                     returnjsonundertry=returnjsonundertry)

    # The stream refers to the Response, not the Request
    def get_stream(self, route, get_params=None,
                   raiseforstatus=True,
                   returnfullresponse=True,
                   returnjsonundertry=False):
        url = self.host + route
        self.logger.debug("GET stream route: " + url)
        headers = self.s.headers
        headers[Ndex2.USER_AGENT_KEY] = self._get_user_agent()
        response = self.s.get(url, params=get_params, stream=True,
                              headers=headers, timeout=self.timeout)
        return self._return_response(response,
                                     raiseforstatus=raiseforstatus,
                                     returnfullresponse=returnfullresponse,
                                     returnjsonundertry=returnjsonundertry)

    # The stream refers to the Response, not the Request
    def post_stream(self, route, post_json,
                    raiseforstatus=True,
                    returnfullresponse=True,
                    returnjsonundertry=False):
        url = self.host + route
        self.logger.debug("POST stream route: " + url)
        headers = self.s.headers

        headers['Content-Type'] = 'application/json'
        headers['Accept'] = 'application/json'
        headers[Ndex2.USER_AGENT_KEY] = self._get_user_agent()
        headers['Connection'] = 'close'
        response = self.s.post(url, data=post_json, headers=headers,
                               stream=True, timeout=self.timeout)
        return self._return_response(response,
                                     raiseforstatus=raiseforstatus,
                                     returnfullresponse=returnfullresponse,
                                     returnjsonundertry=returnjsonundertry)

    # The Request is streamed, not the Response
    def put_multipart(self, route, fields,
                      raiseforstatus=True,
                      returnfullresponse=False,
                      returnjsonundertry=True):
        url = self.host + route
        multipart_data = MultipartEncoder(fields=fields)
        self.logger.debug("PUT route: " + url)

        headers = {'Content-Type': multipart_data.content_type,
                   'Accept': 'application/json',
                   Ndex2.USER_AGENT_KEY: self._get_user_agent(),
                   'Connection': 'close'
                   }
        response = requests.put(url, data=multipart_data, headers=headers, auth=(self.username, self.password))
        return self._return_response(response,
                                     raiseforstatus=raiseforstatus,
                                     returnfullresponse=returnfullresponse,
                                     returnjsonundertry=returnjsonundertry)

    # The Request is streamed, not the Response
    def post_multipart(self, route, fields, query_string=None,
                       raiseforstatus=True,
                       returnfullresponse=False,
                       returnjsonundertry=True):
        if query_string:
            url = self.host + route + '?' + query_string
        else:
            url = self.host + route
        multipart_data = MultipartEncoder(fields=fields)
        self.logger.debug("POST route: " + url)
        headers = {'Content-Type': multipart_data.content_type,
                   Ndex2.USER_AGENT_KEY: self._get_user_agent(),
                   'Connection': 'close'
                   }
        response = requests.post(url, data=multipart_data, headers=headers, auth=(self.username, self.password))
        return self._return_response(response,
                                     raiseforstatus=raiseforstatus,
                                     returnfullresponse=returnfullresponse,
                                     returnjsonundertry=returnjsonundertry)

# Network methods

    def save_new_network(self, cx, visibility=None):
        """
        Create a new network on the server with CX passed in via
        *cx* parameter that is a :func:`list` of :func:`dict`

        Click here for information about
        `CX format <https://home.ndexbio.org/data-model/>`_

        .. note::

           For very large networks (millions of edges) it will be more efficient
           to use :func:`save_cx_stream_as_new_network`

        :param cx: Network in `CX format <https://home.ndexbio.org/data-model/>`_
        :type cx: list of dicts
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
        if len(cx) is 0:
            raise NDExInvalidCXError('CX appears to be empty')

        if cx[-1] is not None:
            if cx[-1].get('status') is None:
                cx.append({"status": [{"error": "", "success": True}]})
            else:
                if len(cx[-1].get('status')) < 1:
                    cx[-1].get('status').append({"error": "", "success": True})

            stream = io.BytesIO(json.dumps(cx, cls=DecimalEncoder).encode('utf-8'))

        return self.save_cx_stream_as_new_network(stream, visibility=visibility)

    def save_cx_stream_as_new_network(self, cx_stream, visibility=None):
        """
        Create a new network from a CX stream that should be in JSON
        following the `CX format <https://home.ndexbio.org/data-model/>`_

        :param cx_stream:  IO stream of cx
        :type cx_stream: stream like BytesIO
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

        route = '/network'

        fields = {
            'CXNetworkStream': ('filename', cx_stream, 'application/octet-stream')
        }

        return self.post_multipart(route, fields, query_string=query_string)

    def update_cx_network(self, cx_stream, network_id):
        """
        Update the network specified by UUID network_id
        using the CX stream *cx_stream*

        :param cx_stream: The network stream.
        :param network_id: The UUID of the network.
        :type network_id: str
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :raises requests.exception.HTTPError: If there is some other error like
                                              network is too large or insufficient
                                              permission
        :return: The response.
        :rtype: `response object <http://docs.python-requests.org/en/master/user/quickstart/#response-content>`_

        """
        self._require_auth()
        fields = {
            'CXNetworkStream': ('filename', cx_stream, 'application/octet-stream')
        }

        route = "/network/%s" % network_id

        return self.put_multipart(route, fields)

    def get_network_as_cx_stream(self, network_id):
        """
        Get the existing network with UUID `network_id`
        from the NDEx connection as a CX stream.
        This is performed as a monolithic operation, so it is typically
        advisable for applications to first use the
        :py:func:`get_network_summary` method to check the node and
        edge counts for a network before retrieving the network.

        To download CX to a file:

        .. code-block:: python

           from ndex2 import client

           anon_ndex = client.Ndex2()
           client_resp = anon_ndex.get_network_as_cx_stream('<UUID OF NETWORK>')
           with open('/tmp/REPLACE_WITH_DESIRED_FILE_NAME', 'wb') as f:
           for chunk in client_resp.iter_content(chunk_size=8096):
               if chunk:  # filter out keep-alive new chunks
                   f.write(chunk)
                   f.flush()

        :param network_id: The UUID of the network.
        :type network_id: str
        :return: The response.
        :rtype: `response object <http://docs.python-requests.org/en/master/user/quickstart/#response-content>`_

        """
        route = "/network/%s" % network_id

        return self.get_stream(route)

    def get_network_aspect_as_cx_stream(self, network_id, aspect_name):
        """
        Get the specified aspect of the existing network with UUID network_id from the NDEx connection as a CX stream.

        :param network_id: The UUID of the network.
        :param aspect_name: The aspect NAME.
        :type network_id: str
        :return: The response.
        :rtype: `response object <http://docs.python-requests.org/en/master/user/quickstart/#response-content>`_

        """
        route = "/network/%s/aspect/%s" % (network_id, aspect_name)

        return self.get_stream(route)

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
        :param error_when_limit: Default value is true. If this value is True, the server
                                 will stop streaming the network when it hits the edgeLimit,
                                 and add `success: false and error: "EdgeLimitExceeded"`
                                 in the status aspect and close the CX stream.
                                 If this value is set to False the server will
                                 return a subnetwork with edge count up to edgeLimit.
                                 The status aspect will be a success, and a network
                                 attribute `{"EdgeLimitExceeded": "true"}` will be added to
                                 the returned network only if the server hits the edgeLimit.
        :type error_when_limit: boolean
        :return: The response.
        :rtype: `response object <http://docs.python-requests.org/en/master/user/quickstart/#response-content>`_

        """
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
        response = self.\
            get_neighborhood_as_cx_stream(network_id,
                                          search_string,
                                          search_depth=search_depth,
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
        :type error_when_limit: boolean
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
        :type error_when_limit: boolean
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

    def search_networks(self, search_string="", account_name=None, start=0,
                        size=100, include_groups=False):
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
        :param include_groups: If True enables this method to return
                               networks where the user has group
                               permission to access
        :type include_groups: bool
        :return: The response.
        :rtype: `response object <http://docs.python-requests.org/en/master/user/quickstart/#response-content>`_

        """
        post_data = {"searchString": search_string}

        route = "/search/network?start=%s&size=%s" % (start, size)
        if include_groups:
            post_data["includeGroups"] = True

        if account_name:
            post_data["accountName"] = account_name
        post_json = json.dumps(post_data)
        return self.post(route, post_json)

    def search_network_nodes(self, network_id,
                             search_string='', limit=5):
        """
        This does not appear to be in public REST API for
        NDEx 2.4+. Slating for removal, pending feedback
        from Jing

        .. deprecated:: 4.0.0


        :param network_id:
        :param search_string:
        :param limit:
        :return:
        """
        post_data = {"searchString": search_string}

        route = "/search/network/%s/nodes?limit=%s" % (network_id, limit)

        post_json = json.dumps(post_data)
        return self.post(route, post_json)

    def find_networks(self, search_string="", account_name=None, skip_blocks=0, block_size=100):
        """

        .. deprecated:: 2.0.1
        Use :func:`search_networks` instead.

        :param search_string:
        :param account_name:
        :param skip_blocks:
        :param block_size:
        :return:
        """
        self.logger.warning("find_networks is deprecated, please use search_networks")
        return self.search_networks(search_string, account_name, skip_blocks, block_size)

    def network_summaries_to_ids(self, network_summaries):
        """
        Internal method used by get_network_ids_for_user to
        extract a list of network ids from a list of
        summary objects

        :param network_summaries:
        :return:
        """
        network_ids = []
        for network in network_summaries:
            network_ids.append(network['externalId'])
        return network_ids

    def get_network_summary(self, network_id):
        """
        Gets information about a network.

        :param network_id: The UUID of the network.
        :type network_id: str
        :return: Summary
        :rtype: dict

        """
        route = "/network/%s/summary" % network_id

        return self.get(route)

    def make_network_public(self, network_id):
        """
        Makes the network specified by the **network_id** public.

        .. deprecated:: 4.0.0
        Use :py:func:`set_network_system_properties`

        :param network_id: The UUID of the network.
        :type network_id: str
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :raises requests.exception.HTTPError: If there is some other error
        :return: empty string upon success
        :rtype: str
        """
        return self.set_network_system_properties(network_id, {'visibility': 'PUBLIC'})

    def _make_network_public_indexed(self, network_id):
        """
        Makes the network specified by the **network_id** public.

        .. deprecated:: 4.0.0
        Use :py:func:`set_network_system_properties`

        :param network_id: The UUID of the network.
        :type network_id: str
        :raises NDExUnsupportedCallError: If version of NDEx server is < 2
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :raises requests.exception.HTTPError: If there is some other error
        :return: empty string upon success
        :rtype: str
        """
        return self.set_network_system_properties(network_id,
                                                  {'visibility': 'PUBLIC',
                                                   'index_level': 'ALL',
                                                   'showcase': True})

    def make_network_private(self, network_id):
        """
        Makes the network specified by the **network_id** private.

        .. deprecated:: 4.0.0
        Use :py:func:`set_network_system_properties`

        :param network_id: The UUID of the network.
        :type network_id: str
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :raises requests.exception.HTTPError: If there is some other error
        :return: empty string upon success
        :rtype: str

        """
        return self.set_network_system_properties(network_id,
                                                  {'visibility': 'PRIVATE'})

    def get_task_by_id(self, task_id):
        """
        Retrieves a task by id

        .. code-block:: json-object

           {
               "startTime": "2020-02-14T20:31:10.412Z",
               "finishTime": "2020-02-14T20:31:10.412Z",
               "ownerProperties": {
                 "newTask": true
               },
               "taskOwnerId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
               "taskType": "string",
               "progress": 0,
               "resource": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
               "attributes": {
                 "name": "string",
                 "downloadFileName": "string",
                 "downloadFileExtension": "string"
               },
               "format": "string",
               "description": "string",
               "status": "string",
               "message": "string",
               "priority": "string",
               "externalId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
               "isDeleted": true,
               "modificationTime": "2020-02-14T20:31:10.412Z",
               "creationTime": "2020-02-14T20:31:10.412Z"
             }

        :param task_id: Task id
        :type task_id: str
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :return: Task
        :rtype: dict
        """
        self._require_auth()
        route = "/task/%s" % task_id
        return self.get(route)

    def _delete_with_lock_check(self, route=None, data=None):
        """
        Internal call that raises the proper exceptions
        for all the cases when invoking delete on a
        network, networkset, or members of a networkset

        :param route:
        :type route: str
        :return: True if delete succeeded, False if object was locked
        """
        try:
            resp = self.delete(route, data=data,
                               raiseforstatus=False,
                               returnjsonundertry=False,
                               returnfullresponse=True)

            if resp.status_code == 204:
                return True
            if resp.status_code == 401:
                raise NDExUnauthorizedError('Server returned'
                                            'unauthorized error')
            if resp.status_code == 404:
                raise NDExNotFoundError('Server returned not '
                                        'found error')
            if resp.status_code == 500:
                ecode = 'unknown'
                d = None
                try:
                    d = json.loads(resp.content)
                    ecode = d.get('errorCode')
                except Exception as e:
                    self.logger.error('Caught exception trying '
                                      'to get '
                                      'erorcode from server error: ' +
                                      str(e))
                if ecode.startswith('NDEx_Concurrent_'
                                    'Modification'):
                    return False
                else:
                    msg = 'Unknown server error'
                    try:
                        msg = d.get('message')
                    except Exception as e:
                        self.logger.error('Caught exception trying '
                                          'to get '
                                          'message from server error: ' +
                                          str(e))
                    raise NDExServerError(msg)

            raise NDExError('Unknown status code received: ' +
                            str(resp.status_code))
        except requests.RequestException as re:
            raise NDExError('Exception from requests call: ' + str(re))

    def delete_network(self, network_id, retry=5,
                       retry_wait=1):
        """
        Deletes the specified network from the server which
        must be owned by the authenticated user

        .. warning::

           There is no undo operation

        :param network_id: Network id
        :type network_id: str
        :param retry: Number of times to retry if deleting fails
        :type retry: int
        :param retry_wait: Time to wait in seconds between retries
        :type retry_wait: int
        :raises NDExUnauthorizedError: If server returns 401 status code which
                                       means credentials are invalid or not set
        :raises NDExNotFoundError: If server returns 404 status code
        :raises NDExServerError: If server returns 500 status code with message
                                 set to message content returned from server
        :raises NDExLockedError: If network is still locked after all retries
        :raises NDExError: If server return an unexpected status code or
                           there was a communication error with
                           server
        :return: None
        """
        if retry_wait is None:
            retry_wait = 1

        self._require_auth()
        route = "/network/%s" % network_id
        count = 0
        while count < retry:
            res = self._delete_with_lock_check(route=route)
            if res is True:
                return

            self.logger.debug('retry deleting network in ' +
                              str(retry_wait) + ' second(s) (' +
                              str(count) + ')')
            count += 1
            time.sleep(retry_wait)

        raise NDExLockedError("Network is locked after " +
                              str(retry) + " retry(s)")

    def get_provenance(self, network_id):
        """
        Gets the network provenance.

        .. warning::

           This method has been deprecated and will be removed at some
           point since the REST service now treats this as an opaque aspect.

        ..

        .. deprecated:: 2.0.1

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

        .. warning::

           This method has been deprecated and will be removed at some
           point since the REST service now treats this as an opaque aspect.

        ..

        .. deprecated:: 2.0.1

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
        Sets network properties

        This method will **NOT** work for ``name, version, description``
        To change those parameters use :py:func:`~update_network_profile`

        Expected format of `network_properties`
        (:py:func:`list` of :py:func:`dict`) parameter:

        .. code-block:: json-object

           [
            {
             'subNetworkId': '',
             'predicateString': '',
             'dataType': '',
             'value': ''
            }
           ]

        Definitions:

        ``subNetworkId`` - Optional identifier of the subnetwork to which \
                           the property applies

        ``predicateString`` - Name of the attribute.

        ``dataType`` - Data type of this property. Has to be one of the CX supported \
                       types. If unset, string is assumed.

        ``value`` - String representation of the property value.

        .. note::
           Many networks in NDEx have no subnetworks
           and in those cases the ``subNetworkId`` attribute of every
           NdexPropertyValuePair should not be set. Some networks,
           including some saved from Cytoscape have one subnetwork.
           In those cases, every NdexPropertyValuePair should have
           the ``subNetworkId`` attribute set to the id of that subNetwork.
           Other networks originating in Cytoscape Desktop correspond
           to Cytoscape "collections" and may have multiple
           subnetworks. Each subnetwork may have NdexPropertyValuePairs
           associated with it and these will be visible in the
           Cytoscape network viewer. The collection itself may
           have NdexPropertyValuePairs associated with it and
           these are not visible in the Cytoscape network viewer
           but may be set or read by specific Cytoscape Apps. In
           these cases, we strongly recommend that you edit these
           network attributes in Cytoscape rather than via this API
           unless you are very familiar with the Cytoscape data model.

        :param network_id: Network id
        :type network_id: str
        :param network_properties: List of NDEx property value pairs
        :type network_properties: list
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :raises NDExError: If network_properties is not a
                           :py:func:`list` or :py:func:`str`
        :raises requests.exceptions.HTTPError: If there is some server side error
        :return: None
        """
        self._require_auth()
        route = "/network/%s/properties" % network_id
        if isinstance(network_properties, list):
            put_json = json.dumps(network_properties)
        elif isinstance(network_properties, str):
            put_json = network_properties
        else:
            raise NDExError('network_properties must be a string or a list '
                            'of NdexPropertyValuePair objects')

        self.put(route, put_json)

    def get_sample_network(self, network_id):
        """
        Gets the sample network

        :param network_id: Network id
        :type network_id: str
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :return: Sample network
        :rtype: list of dicts in cx format
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

        .. code-block:: json-object

            {'showcase': (boolean True or False),
             'visibility': (str 'PUBLIC' or 'PRIVATE'),
             'index_level': (str  'NONE', 'META', or 'ALL'),
             'readOnly': (boolean True or False)}

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

        Any profile attributes specified will be updated but attributes \
        that are not specified will have no effect - omission of an attribute \
        does not mean deletion of that attribute.
        The network profile attributes that can be updated by this method \
        are: ``name``, ``description`` and ``version``.

        .. note::

           This method will raise a :py:class:`~ndex2.exceptions.NDExError` \
           if network is NOT fully validated on the server.
           To check if the network has been validated \
           call :py:func:`~ndex2.client.Ndex2.get_network_summary`

        The `network_profile` parameter should be a :py:func:`dict` in this
        format:

        .. code-block:: json-object

           {
            'name': '',
            'description': '',
            'version': ''
           }

        :param network_id: Network id
        :type network_id: str
        :param network_profile: Network profile
        :type network_profile: dict
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :raises NDExInvalidParameterError: If `visibility` is set in
                                           `network_profile` parameter or
                                           if `network_profile` parameter is
                                           not a :py:func:`str` or :py:func:`dict`
        :raises NDExError: If there was a server side error with update of \
                           network profile like if the network is not validated \
                           on server. See note above.
        :return: None
        """

        self._require_auth()
        if isinstance(network_profile, dict):
            if network_profile.get("visibility"):
                raise NDExInvalidParameterError("Ndex 2.x doesn't support "
                                                "setting visibility by "
                                                "this function. "
                                                "Please use "
                                                "make_network_public/private "
                                                "function to set network "
                                                "visibility.")
            json_data = json.dumps(network_profile)
        elif isinstance(network_profile, str):
            json_data = network_profile
        else:
            raise NDExInvalidParameterError("network_profile must be a "
                                            "string or a dict")

        route = "/network/%s/profile" % network_id
        self.put(route, json_data)
        return None

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

    def get_user_by_username(self, username):
        """
        Gets user information as a :py:func:`dict` example format:

        .. code-block:: json-object

            {
             'properties': {},
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

        If the user account has not been verified by the user yet, the
        returned object will contain no user UUID and the *isVerified* field
        will be ``False``.

        :param username: User name
        :type username: str
        :raises requests.exception.HTTPError: If there is some other error
        :return: user information as dict
        :rtype: dict
        """
        route = "/user?username=%s" % username
        return self.get(route)

    def get_user_network_summaries(self, username):
        """
        This method invokes :py:func:`get_network_summaries_for_user` with
        default `offset` and `limit`

        .. deprecated:: 4.0.0
        Use :func:`get_network_summaries_for_user` instead.

        :param username: the username of the network owner
        :type username: str
        :return: list of network summaries
        :rtype: list
        """
        network_summaries = self.get_network_summaries_for_user(username)
        return network_summaries

    def get_network_summaries_for_user(self, username, offset=0, limit=1000):
        """
        Get a list of network summaries for networks owned by specified user.
        It returns not only the networks that the user owns but also the networks that are
        shared with them directly.

        Example result:

        .. code-block:: json-object

           [
              {
                "ownerUUID": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "isReadOnly": false,
                "subnetworkIds": [
                  "3fa85f64-5717-4562-b3fc-2c963f66afa6"
                ],
                "errorMessage": "string",
                "isValid": true,
                "warnings": [
                  "string"
                ],
                "isShowcase": false,
                "doi": "string",
                "isCertified": false,
                "visibility": "PUBLIC",
                "indexed": true,
                "completed": true,
                "edgeCount": 0,
                "nodeCount": 0,
                "version": "string",
                "uri": "string",
                "owner": "string",
                "name": "string",
                "properties": [
                  {
                    "subNetworkId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "predicateString": "string",
                    "dataType": "string",
                    "value": "string"
                  }
                ],
                "description": "string",
                "externalId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "isDeleted": false,
                "modificationTime": "2020-02-14T21:59:24.648Z",
                "creationTime": "2020-02-14T21:59:24.648Z"
              }
           ]

        :param username: the username of the network owner
        :type username: str
        :param offset: the starting position of the network search
        :type offset: int
        :param limit:
        :type limit:
        :return: :py:func:`list` of network summaries as :py:func:`dict`
        :rtype: list
        """
        user = self.get_user_by_username(username)#.json

        route = "/user/%s/networksummary?offset=%s&limit=%s" % (user['externalId'], offset, limit)

        network_summaries = self.get_stream(route)

        # uuids = None
        # if network_summaries:
        #    uuids = [d.get('externalId') for d in network_summaries.json()]
        if network_summaries:
            return network_summaries.json()
        else:
            return None

    def get_network_ids_for_user(self, username):
        """
        Get the network uuids owned by the user as a :py:func:`list`

        .. note::

          This method only returns the first 1000 ids. To
          get more results see :py:func:`get_user_network_summaries`

        :param username: users NDEx username
        :type username: str
        :return: list of uuids
        :rtype: list
        """
        network_summaries_list = self.get_network_summaries_for_user(username)

        return self.network_summaries_to_ids(network_summaries_list)

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
        :param networkids: list of network ids as strings
        :type networkids: list
        :param permission: Network permissions
        :type permission: str
        :return: none
        :rtype: none
        """
        for networkid in networkids:
            self.update_network_user_permission(userid, networkid, permission)

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
        :type set_id: basestring
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

    def delete_networkset(self, networkset_id):
        """
        Deletes the network set, requires credentials

        :param networkset_id: networkset UUID id
        :type networkset_id: str
        :raises NDExInvalidParameterError: for invalid networkset id parameter
        :raises NDExUnauthorizedError: If no credentials or user is not authorized
        :raises NDExNotFoundError: If no networkset with id passed in found
        :raises NDExError: For any other error with contents of error in message
        :return: None
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
        :param networks: networks that will be added to the set
        :type networks: list
        :return: None
        :rtype: None
        """

        route = '/networkset/%s/members' % set_id

        post_json = json.dumps(networks)
        return self.post(route, post_json)

    def delete_networks_from_networkset(self, set_id, networks,
                                        retry=5, retry_wait=1):
        """
        Removes network(s) from a network set.

        :param set_id: network set id
        :type set_id: basestring
        :param networks: networks that will be removed from the set
        :type networks: list of strings
        :param retry: Number of times to retry
        :type retry: int
        :param retry_wait: Time to wait in seconds between retries
        :type retry_wait: int
        :raises NDExUnauthorizedError: If server returns 401 status code which
                                       means credentials are invalid or not set
        :raises NDExNotFoundError: If server returns 404 status code
        :raises NDExServerError: If server returns 500 status code with message
                                 set to message content returned from server
        :raises NDExLockedError: If network(s) are still locked after all
                                 retries
        :raises NDExError: If server return an unexpected status code or
                           there was a communication error with
                           server
        :return: None
        """

        route = '/networkset/%s/members' % set_id
        post_json = json.dumps(networks)
        headers = self.s.headers
        headers['Content-Type'] = 'application/json;charset=UTF-8'
        headers['Accept'] = 'application/json'
        headers['User-Agent'] = self._get_user_agent()

        if retry_wait is None:
            retry_wait = 1

        count = 0
        while count < retry:
            res = self._delete_with_lock_check(route=route,
                                               data=post_json)
            if res is True:
                return

            self.logger.debug('retry deleting network(s) from networkset '
                              'in ' + str(retry_wait) + ' second(s) (' +
                              str(count) + ')')
            count += 1
            time.sleep(retry_wait)

        raise NDExLockedError("Network(s) are locked after " +
                              str(retry) + " retry(s)")


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        elif isinstance(o, numpy.integer):
            return int(o)
        elif isinstance(o, bytes):
            bytes_string = o.decode('ascii')
            return bytes_string
        return super(DecimalEncoder, self).encode(o)