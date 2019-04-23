#!/usr/bin/env python

import requests
import json
import logging
from requests_toolbelt import MultipartEncoder
import io
import sys
import decimal
import numpy

from .version import __version__
from .exceptions import NDExInvalidCXError
from .exceptions import NDExUnauthorizedError
from .exceptions import NDExError
try:
    from urllib.parse import urljoin
except ImportError:
     from urlparse import urljoin

from requests import exceptions as req_except
import time

userAgent = 'NDEx2-Python/' + __version__

DEFAULT_SERVER = "http://public.ndexbio.org"


class Ndex2(object):
    """ A class to facilitate communication with an
        `NDEx server <http://ndexbio.org>`_.

        If host is not provided it will default to the
        `NDEx public server <http://ndexbio.org>`_.  UUID is required

    """
    USER_AGENT_KEY = 'User-Agent'

    def __init__(self, host=None, username=None, password=None,
                 update_status=False, debug=False, user_agent='',
                 timeout=30):
        """
        Creates a connection to a particular `NDEx server <http://ndexbio.org>`_.

        :param host: The URL of the server.
        :type host: string
        :param username: The username of the NDEx account to use. (Optional)
        :type username: string
        :param password: The account password. (Optional)
        :type password: string
        :param update_status: If set to True tells constructor to query
                              service for status
        :type update_status: bool
        :param user_agent: String to append to
                           `User-Agent <https://tools.ietf.org/html/rfc1945#page-46>`_
                           header sent with all requests to server
        :type user_agent: string
        :param timeout: The timeout in seconds value for requests to server. This value
                        is passed to Request calls `Click here for more information
                        <http://docs.python-requests.org/en/master/user/advanced/#timeouts>`_
        :type timeout: float or tuple(float, float)
        """
        self.debug = debug
        self.version = 1.3
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
            status_url = "/rest/admin/status"

            try:
                version_url = urljoin(host, status_url)

                response = requests.get(version_url,
                                        headers={Ndex2.USER_AGENT_KEY:
                                                 userAgent + self.user_agent})
                response.raise_for_status()
                data = response.json()

                prop = data.get('properties')
                if prop is not None:
                    pv = prop.get('ServerVersion')
                    if pv is not None:
                        if not pv.startswith('2.'):
                            raise Exception("This release only supports NDEx 2.x server.")
                        else:
                            self.version = pv
                            self.host = host + "/v2"
                    else:
                        self.logger.warning("Warning: This release doesn't fully "
                                            "support 1.3 version of NDEx")
                        self.version = "1.3"
                        self.host = host + "/rest"
                else:
                    self.logger.warning("Warning: No properties found. "
                                        "This release doesn't fully "
                                        "support 1.3 version of NDEx")
                    self.version = "1.3"
                    self.host = host + "/rest"

            except req_except.HTTPError as he:
                self.logger.warning("Can't determine server version. " + host +
                                    ' Server returned error -- ' + str(he) +
                                    ' will assume 1.3 version of NDEx which' +
                                    ' is not fully supported by this release')
                self.version = "1.3"
                self.host = host + "/rest"
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
        response.raise_for_status()
        if response.status_code == 204:
            return ""

        if returnjsonundertry is True:
            try:
                result = response.json()
            except ValueError:
                result = response.text
            return result

        if returnfullresponse is True:
            return response
        if response.headers['content-type'] == 'application/json':
            return response.json()
        else:
            return response.text

    def put(self, route, put_json=None):
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
        return self._return_response(response)

    def post(self, route, post_json):
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
        return self._return_response(response)

    def delete(self, route, data=None):
        url = self.host + route
        self.logger.debug("DELETE route: " + url)
        headers = self.s.headers
        headers[Ndex2.USER_AGENT_KEY] = userAgent + self.user_agent

        if data is not None:
            response = self.s.delete(url, headers=headers, data=data,
                                     timeout=self.timeout)
        else:
            response = self.s.delete(url, headers=headers,
                                     timeout=self.timeout)
        return self._return_response(response)

    def get(self, route, get_params=None):
        url = self.host + route
        self.logger.debug("GET route: " + url)
        headers = self.s.headers
        headers[Ndex2.USER_AGENT_KEY] = self._get_user_agent()
        response = self.s.get(url, params=get_params, headers=headers,
                              timeout=self.timeout)
        return self._return_response(response)

    # The stream refers to the Response, not the Request
    def get_stream(self, route, get_params=None):
        url = self.host + route
        self.logger.debug("GET stream route: " + url)
        headers = self.s.headers
        headers[Ndex2.USER_AGENT_KEY] = self._get_user_agent()
        response = self.s.get(url, params=get_params, stream=True,
                              headers=headers, timeout=self.timeout)
        return self._return_response(response,
                                     returnfullresponse=True)

    # The stream refers to the Response, not the Request
    def post_stream(self, route, post_json):
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
                                     returnfullresponse=True)

    # The Request is streamed, not the Response
    def put_multipart(self, route, fields):
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
                                     returnjsonundertry=True)

    # The Request is streamed, not the Response
    def post_multipart(self, route, fields, query_string=None):
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
                                     returnjsonundertry=True)

# Network methods

    def save_new_network(self, cx, visibility=None):
        """
        Create a new network (cx) on the server

        :param cx: Network cx
        :type cx: list of dicts
        :param visibility: Sets the visibility (PUBLIC or PRIVATE)
        :type visibility: string
        :raises NDExInvalidCXError: For invalid CX data
        :return: Response data
        :rtype: string or dict
        """
        if cx is None:
            raise NDExInvalidCXError('CX is None')
        if not isinstance(cx, list):
            raise NDExInvalidCXError('CX is not a list')
        if len(cx) is 0:
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
        :type visibility: string
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :return: Response data
        :rtype: string or dict
        """

        indexed_fields = None
        #TODO add functionality for indexed_fields when it's supported by the server

        self._require_auth()
        query_string = None
        if indexed_fields:
            if visibility:
                query_string = 'indexedfields=' + ','.join(indexed_fields)
            else:
                query_string = 'visibility=' + str(visibility) + '&indexedfields=' + ','.join(indexed_fields)
        elif visibility:
                query_string = 'visibility=' + str(visibility)

        if self.version == "2.0":
            route = '/network'
        else:
            route = '/network/asCX'

        fields = {
            'CXNetworkStream': ('filename', cx_stream, 'application/octet-stream')
        }

        return self.post_multipart(route, fields, query_string=query_string)

    def update_cx_network(self, cx_stream, network_id):
        """
        Update the network specified by UUID network_id using the CX stream cx_stream.

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

        if self.version == "2.0":
            route = "/network/%s" % network_id
        else:
            route = '/network/asCX/%s' % network_id

        return self.put_multipart(route, fields)

    def get_network_as_cx_stream(self, network_id):
        """
        Get the existing network with UUID network_id from the NDEx connection as a CX stream.

        :param network_id: The UUID of the network.
        :type network_id: str
        :return: The response.
        :rtype: `response object <http://docs.python-requests.org/en/master/user/quickstart/#response-content>`_

        """

        if self.version == "2.0":
            route = "/network/%s" % network_id
        else:
            route = "/network/%s/asCX" % network_id

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

        if self.version == "2.0":
            route = "/network/%s/aspect/%s" % (network_id, aspect_name)
        else:
            route = "/network/%s/asCX" % network_id

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
        :param error_when_limit: Default value is true. If this value is true the server will stop streaming the network when it hits the edgeLimit, add success: false and error: "EdgeLimitExceeded" in the status aspect and close the CX stream. If this value is set to false the server will return a subnetwork with edge count up to edgeLimit. The status aspect will be a success, and a network attribute {"EdgeLimitExceeded": "true"} will be added to the returned network only if the server hits the edgeLimit..
        :type error_when_limit: boolean
        :return: The response.
        :rtype: `response object <http://docs.python-requests.org/en/master/user/quickstart/#response-content>`_

        """
        if self.version == "2.0":
            route = "/search/network/%s/query" % network_id
        else:
            route = "/network/%s/query" % network_id

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
        response = self.get_neighborhood_as_cx_stream(network_id, search_string, search_depth=search_depth,
                                                      edge_limit=edge_limit)

        if self.version == "2.0":
            # response_in_json = response.json()
            # data =  response_in_json["data"]
            # return data
            response_json = response.json()
            if isinstance(response_json, dict):
                return response_json.get('data')
            elif isinstance(response_json, list):
                return response_json
            else:
                return response_json
        else:
            raise Exception("get_neighborhood is not supported for versions prior to 2.0, "
                            "use get_neighborhood_as_cx_stream")

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
        if self.version == "2.0":
            route = "/search/network?start=%s&size=%s" % (start, size)
            if include_groups:
                post_data["includeGroups"] = True
        else:
            route = "/network/search/%s/%s" % (start, size)

        if account_name:
            post_data["accountName"] = account_name
        post_json = json.dumps(post_data)
        return self.post(route, post_json)

    def search_network_nodes(self, network_id, search_string='', limit=5):
        post_data = {"searchString": search_string}
        if self.version == "2.0":
            route = "/search/network/%s/nodes?limit=%s" % (network_id, limit)
        else:
            route = "/network/%s/nodes/%s" % (network_id, limit)

        post_json = json.dumps(post_data)
        return self.post(route, post_json)

    def find_networks(self, search_string="", account_name=None, skip_blocks=0, block_size=100):
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
        Gets information about a network.

        :param network_id: The UUID of the network.
        :type network_id: str
        :return: Summary
        :rtype: dict

        """
        if self.version == "2.0":
            route = "/network/%s/summary" % network_id
        else:
            route = "/network/%s" % network_id

        return self.get(route)

    def make_network_public(self, network_id):
        """
        Makes the network specified by the network_id public.

        :param network_id: The UUID of the network.
        :type network_id: str
        :return: The response.
        :rtype: `response object <http://docs.python-requests.org/en/master/user/quickstart/#response-content>`_

        """
        if self.version == "2.0":
            return self.set_network_system_properties(network_id, {'visibility': 'PUBLIC'})

        else:
            return self.update_network_profile(network_id, {'visibility': 'PUBLIC'})

    def _make_network_public_indexed(self, network_id):
        """
        Makes the network specified by the network_id public.

        :param network_id: The UUID of the network.
        :type network_id: str
        :return: The response.
        :rtype: `response object <http://docs.python-requests.org/en/master/user/quickstart/#response-content>`_

        """
        if self.version == "2.0":
            for i in range(0, 4):
                try:
                    return_message = self.set_network_system_properties(network_id, {'visibility': 'PUBLIC', 'index_level': 'ALL', 'showcase': True})
                except Exception as exc:
                    time.sleep(1)

            return return_message

        else:
            return self.update_network_profile(network_id, {'visibility': 'PUBLIC'})

    def make_network_private(self, network_id):
        """
        Makes the network specified by the network_id private.

        :param network_id: The UUID of the network.
        :type network_id: str
        :return: The response.
        :rtype: `response object <http://docs.python-requests.org/en/master/user/quickstart/#response-content>`_

        """
        if self.version == "2.0":
            return self.set_network_system_properties(network_id, {'visibility': 'PRIVATE'})

        else:
            return self.update_network_profile(network_id, {'visibility': 'PRIVATE'})

    def get_task_by_id(self, task_id):
        """
        Retrieves a task by id

        :param task_id: Task id
        :type task_id: string
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
        :type network_id: string
        :param retry: Number of times to retry if deleting fails
        :type retry: int
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :return: Error json if there is an error.  Blank
        :rtype: string
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

        .. warning::

           This method has been deprecated.

        ..

        :param network_id: Network id
        :type network_id: string
        :return: Provenance
        :rtype: dict
        """
        route = "/network/%s/provenance" % network_id
        return self.get(route)

    def set_provenance(self, network_id, provenance):
        """
        Sets the network provenance

        .. warning::

           This method has been deprecated.

        ..

        :param network_id: Network id
        :type network_id: string
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
        Sets the read only flag on the specified network

        :param network_id: Network id
        :type network_id: string
        :param value: Read only value
        :type value: bool
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :return: Result
        :rtype: dict
        """
        self._require_auth()
        return self.set_network_system_properties(network_id, {"readOnly": value})

    def set_network_properties(self, network_id, network_properties):
        """
        Sets network properties

        :param network_id: Network id
        :type network_id: string
        :param network_properties: List of NDEx property value pairs
        :type network_properties: list
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :return:
        :rtype:
        """
        self._require_auth()
        route = "/network/%s/properties" % network_id
        if isinstance(network_properties, list):
            put_json = json.dumps(network_properties)
        elif isinstance(network_properties, str):
            put_json = network_properties
        else:
            raise Exception("network_properties must be a string or a list of NdexPropertyValuePair objects")
        return self.put(route, put_json)

    def get_sample_network(self, network_id):
        """
        Gets the sample network

        :param network_id: Network id
        :type network_id: string
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

    def set_network_system_properties(self, network_id, network_properties):
        """
        Set network system properties

        :param network_id: Network id
        :type network_id: string
        :param network_properties: Network properties
        :type network_properties: dict of NDEx network property value pairs
        :raises NDExUnauthorizedError: If credentials are invalid or not set
        :return: Result
        :rtype: dict
        """
        self._require_auth()
        route = "/network/%s/systemproperty" % network_id
        if isinstance(network_properties, dict):
            put_json = json.dumps(network_properties)
        elif isinstance(network_properties, str):
            put_json = network_properties
        else:
            raise Exception("network_properties must be a string or a dict")
        return self.put(route, put_json)

    def update_network_profile(self, network_id, network_profile):
        """
        Updates the network profile
        Any profile attributes specified will be updated but attributes that are not specified will
        have no effect - omission of an attribute does not mean deletion of that attribute.
        The network profile attributes that can be updated by this method are: 'name', 'description' and 'version'.

        :param network_id: Network id
        :type network_id: string
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

        if self.version == "2.0":
            route = "/network/%s/profile" % network_id
            return self.put(route, json_data)
        else:
            route = "/network/%s/summary" % network_id
            return self.post(route, json_data)

    def upload_file(self, filename):
        raise NDExError("This function is not supported in this release. Please use the save_new_network "
                        "function to create new networks in NDEx server.")


    def update_network_group_permission(self, groupid, networkid, permission):
        """
        Updated group permissions

        :param groupid: Group id
        :type groupid: string
        :param networkid: Network id
        :type networkid: string
        :param permission: Network permission
        :type permission: string
        :return: Result
        :rtype: dict
        """
        route = "/network/%s/permission?groupid=%s&permission=%s" % (networkid, groupid, permission)
        self.put(route)

    def update_network_user_permission(self, userid, networkid, permission):
        """
        Updated network user permission

        :param userid: User id
        :type userid: string
        :param networkid: Network id
        :type networkid: string
        :param permission: Network permission
        :type permission: string
        :return: Result
        :rtype: dict
        """
        route = "/network/%s/permission?userid=%s&permission=%s" % (networkid, userid, permission)
        self.put(route)

    def grant_networks_to_group(self, groupid, networkids, permission="READ"):
        """
        Set group permission for a set of networks

        :param groupid: Group id
        :type groupid: string
        :param networkids: List of network ids
        :type networkids: list
        :param permission: Network permission
        :type permission: string
        :return: Result
        :rtype: dict
        """
        for networkid in networkids:
            self.update_network_group_permission(groupid, networkid, permission)

    def get_user_by_username(self, username):
        """
        Gets the user id by user name

        :param username: User name
        :type username: string
        :return: User id
        :rtype: string
        """
        route = "/user?username=%s" % username
        return self.get(route)

    def get_network_summaries_for_user(self, username):
        network_summaries = self.get_user_network_summaries(username)
        # self.search_networks("", username, size=1000)

        # if (network_summaries and network_summaries['networks']):
        #    network_summaries_list = network_summaries['networks']
        # else:
        #    network_summaries_list = []

        return network_summaries

    def get_user_network_summaries(self, username, offset=0, limit=1000):
        """
        Get a list of network summaries for networks owned by specified user.
        It returns not only the networks that the user owns but also the networks that are
        shared with them directly.

        :param username: the username of the network owner
        :type username: str
        :param offset: the starting position of the network search
        :type offset: int
        :param limit:
        :type limit:
        :return: list of uuids
        :rtype: list
        """

        route = ""
        user = self.get_user_by_username(username)#.json
        if self.version == "2.0":
            route = "/user/%s/networksummary?offset=%s&limit=%s" % (user['externalId'], offset, limit)
        else:
            route = "/user/%s/networksummary/asCX?offset=%s&limit=%s" % (user['externalId'], offset, limit)

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
        Get the network uuids owned by the user

        :param username: users NDEx username
        :type username: str
        :return: list of uuids
        """
        network_summaries_list = self.get_network_summaries_for_user(username)

        return self.network_summaries_to_ids(network_summaries_list)

    def grant_network_to_user_by_username(self, username, network_id, permission):
        """
        Grants permission to network for the given user name

        :param username: User name
        :type username: string
        :param network_id: Network id
        :type network_id: string
        :param permission: Network permission
        :type permission: string
        :return: Result
        :rtype: dict
        """
        user = self.get_user_by_username(username).json
        self.update_network_user_permission(user["externalid"], network_id, permission)

    def grant_networks_to_user(self, userid, networkids, permission="READ"):
        """
        Gives read permission to specified networks for the provided user

        :param userid: User id
        :type userid: string
        :param networkids: Network ids
        :type networkids: list of strings
        :param permission: Network permissions
        :type permission: string (default is READ)
        :return: none
        :rtype: none
        """
        for networkid in networkids:
            self.update_network_user_permission(userid, networkid, permission)

    def update_status(self):
        """
        Updates the admin status

        :return: None (however the status is stored in the client object self.status)
        :rtype:
        """
        route = "/admin/status"
        self.status = self.get(route)

    def create_networkset(self, name, description):
        """
        Creates a new network set

        :param name: Network set name
        :type name: string
        :param description: Network set description
        :type description: string
        :return: URI of the newly created network set
        :rtype: string
        """
        route = '/networkset'
        return self.post(route, json.dumps({"name": name, "description": description}))

    def get_network_set(self, set_id):
        """
        Gets the network set information including the list of networks

        :param set_id: network set id
        :type set_id: basestring
        :return: network set information
        :rtype: dict
        """
        route = '/networkset/%s' % set_id

        return self.get(route)

    def add_networks_to_networkset(self, set_id, networks):
        """
        Add networks to a network set.  User must have visibility of all networks being added

        :param set_id: network set id
        :type set_id: basestring
        :param networks: networks that will be added to the set
        :type networks: list of strings
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
        :type set_id: basestring
        :param networks: networks that will be removed from the set
        :type networks: list of strings
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
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        elif isinstance(o, numpy.integer):
            return int(o)
        elif isinstance(o, bytes):
            bytes_string = o.decode('ascii')
            return bytes_string
        return super(DecimalEncoder, self).encode(o)