#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Client for the NDEx **v3** REST API.

The v3 API reorganizes user content around a *file system* model. Every
item a user owns is a **file item** with one of three types
(:py:class:`FileType`): ``NETWORK``, ``FOLDER`` or ``SHORTCUT``.
Folders nest arbitrarily and replace the flat *network set* concept from
v2; shortcuts let a single item appear in more than one folder.

.. versionadded:: 4.0.0

Example::

    from ndex2.client_v3 import Ndex3

    client = Ndex3(host='https://www.ndexbio.org',
                   username='bob', password='secret')

    folder_id = client.create_folder('My Pathways')
    client.move_networks_to_folder(folder_id, [network_id])
    for item in client.list_folder_items(folder_id):
        print(item['name'], item['type'])
"""

import json
import logging

import requests
from requests import exceptions as req_except

from ndex2.client import Ndex2
from ndex2.client import DecimalEncoder
from ndex2.client import DEFAULT_SERVER
from ndex2.exceptions import NDExError
from ndex2.exceptions import NDExInvalidParameterError
from ndex2.exceptions import NDExUnsupportedCallError

logger = logging.getLogger(__name__)


class FileType(object):
    """
    Valid values for the ``type`` of a v3 file item.
    """
    NETWORK = 'NETWORK'
    FOLDER = 'FOLDER'
    SHORTCUT = 'SHORTCUT'

    ALL = frozenset([NETWORK, FOLDER, SHORTCUT])


class Visibility(object):
    """
    Valid visibility values for v3 file items.
    """
    PUBLIC = 'PUBLIC'
    PRIVATE = 'PRIVATE'
    UNLISTED = 'UNLISTED'

    ALL = frozenset([PUBLIC, PRIVATE, UNLISTED])


class Permissions(object):
    """
    Valid permission values used when sharing file items.
    """
    READ = 'READ'
    WRITE = 'WRITE'
    ADMIN = 'ADMIN'
    MEMBER = 'MEMBER'

    ALL = frozenset([READ, WRITE, ADMIN, MEMBER])


class Ndex3(Ndex2):
    """
    A client for the NDEx **v3** REST API.

    This class subclasses :py:class:`~ndex2.client.Ndex2` to reuse its
    CX2 network I/O and error handling, but all requests issued by
    methods defined here are routed to ``/v3``. Network set and group
    calls inherited from :py:class:`~ndex2.client.Ndex2` are disabled and
    raise :py:class:`~ndex2.exceptions.NDExUnsupportedCallError`; the v3
    server exposes no equivalent endpoints. Use folders and
    :py:meth:`share_files` instead.

    Authentication accepts either a username/password pair (sent as HTTP
    Basic) or an OAuth/Keycloak id token (sent as ``Authorization:
    Bearer``). The v3 server accepts both.
    """

    V3_ENDPOINT = '/v3'

    FOLDERS_ROUTE = '/files/folders'
    SHORTCUTS_ROUTE = '/files/shortcuts'
    FILES_ROUTE = '/files'
    BATCH_ROUTE = '/batch'
    SEARCH_ROUTE = '/search'
    NETWORKS_ROUTE = '/networks'
    USERS_ROUTE = '/users'
    WORKSPACES_ROUTE = '/workspaces'

    def __init__(self, host=None, username=None, password=None,
                 bearer_token=None, debug=False, user_agent='',
                 timeout=30, skip_version_check=True):
        """
        Creates a connection to the v3 API of an NDEx server.

        :param host: URL of the server. Defaults to the NDEx public
                     server.
        :type host: str
        :param username: Username of the NDEx account to use
        :type username: str
        :param password: Password for *username*
        :type password: str
        :param bearer_token: OAuth/Keycloak id token. Sent as an
                             ``Authorization: Bearer`` header and takes
                             precedence over *username*/*password* when
                             both are supplied.
        :type bearer_token: str
        :param debug: If ``True`` log status codes and error bodies
        :type debug: bool
        :param user_agent: Appended to the ``User-Agent`` header of
                           every request
        :type user_agent: str
        :param timeout: Timeout in seconds passed to :py:mod:`requests`
        :type timeout: float or tuple(float, float)
        :param skip_version_check: If ``False`` the server is queried at
                                   ``/v3/admin/status`` and
                                   :py:class:`~ndex2.exceptions.NDExError`
                                   is raised if v3 is unavailable.
                                   Defaults to ``True``.
        :type skip_version_check: bool
        :raises NDExError: If *skip_version_check* is ``False`` and the
                           server does not respond to the v3 status
                           endpoint
        """
        self.debug = debug
        self.version = '3.0'
        self.version_endpoint = Ndex3.V3_ENDPOINT
        self.status = {}
        self.username = username
        self.password = password
        self.bearer_token = bearer_token
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

        if user_agent is None:
            self.user_agent = ''
        elif len(user_agent) > 0:
            self.user_agent = ' ' + user_agent
        else:
            self.user_agent = ''

        if host is None:
            host = DEFAULT_SERVER
        elif 'http' not in host:
            host = 'http://' + host
        self.host = host.rstrip('/')

        self.s = requests.session()
        if bearer_token is not None:
            self.s.headers['Authorization'] = 'Bearer ' + bearer_token
        elif username is not None and password is not None:
            self.s.auth = (username, password)

        if skip_version_check is not True:
            self.update_status()

    # ------------------------------------------------------------------
    # request plumbing
    # ------------------------------------------------------------------

    def _request(self, method, route, params=None, json_body=None,
                 extra_headers=None, stream=False, return_response=False):
        """
        Issues a request against the v3 endpoint and normalizes errors.

        Unlike the verb helpers on :py:class:`~ndex2.client.Ndex2` this
        method supports query parameters on every verb, does not mutate
        the shared session headers, and converts
        :py:class:`requests.HTTPError` into the
        :py:class:`~ndex2.exceptions.NDExError` hierarchy.

        :param method: HTTP verb, for example ``GET``
        :type method: str
        :param route: Path appended to ``<host>/v3``
        :type route: str
        :param params: Query parameters. ``None`` values are dropped.
        :type params: dict
        :param json_body: Object serialized to a JSON request body
        :param extra_headers: Headers merged over the defaults
        :type extra_headers: dict
        :param stream: If ``True`` the response is streamed and returned
                       unparsed
        :type stream: bool
        :param return_response: If ``True`` return the
                                :py:class:`requests.Response` instead of
                                a parsed body
        :type return_response: bool
        :raises NDExError: On any non 2xx response or transport failure
        :return: Parsed JSON, response text, ``None`` for empty bodies,
                 or the response object
        """
        url = self.host + self.version_endpoint + route
        headers = {Ndex2.USER_AGENT_KEY: self._get_user_agent(),
                   'Accept': 'application/json,text/plain',
                   'Connection': 'close'}
        if json_body is not None:
            headers['Content-Type'] = 'application/json;charset=UTF-8'
        if extra_headers is not None:
            headers.update(extra_headers)

        body = None
        if json_body is not None:
            body = json.dumps(json_body, cls=DecimalEncoder)

        if params is not None:
            params = {key: val for key, val in params.items()
                      if val is not None}

        self.logger.debug('%s %s params=%s', method, url, str(params))

        try:
            response = self.s.request(method, url, params=params, data=body,
                                      headers=headers, timeout=self.timeout,
                                      stream=stream)
            if self.debug is True:
                self.debug_response(response)
            response.raise_for_status()
        except req_except.HTTPError as he:
            self._convert_requests_http_error_to_ndex_error(he)
        except NDExError:
            raise
        except Exception as e:
            self._convert_exception_to_ndex_error(e)

        if stream is True or return_response is True:
            return response
        return self._parse_body(response)

    @staticmethod
    def _parse_body(response):
        """
        Converts a response into a Python object.

        :param response: Response to parse
        :type response: :py:class:`requests.Response`
        :return: ``None`` for empty bodies, parsed JSON when the content
                 type says JSON, otherwise the response text
        """
        if response.status_code == 204 or not response.content:
            return None
        content_type = (response.headers.get('Content-Type', '') or '').lower()
        text = response.text
        # Trust the declared content type, but also parse a body that is
        # plainly a JSON object or array. Some deployments and proxies drop
        # the Content-Type header, and silently handing back a string where
        # a dict is expected produces a confusing failure far from the
        # cause. Bare scalars are left as text so that a text/plain body of
        # "123" does not become an int.
        looks_like_json = text.lstrip()[:1] in ('{', '[')
        if 'application/json' in content_type or looks_like_json:
            try:
                return response.json()
            except ValueError:
                return text
        return text

    @staticmethod
    def _uuid_from_created(response):
        """
        Pulls the UUID of a newly created item out of a 201 response.

        The v3 create endpoints return an ``NdexObjectUpdateStatus``
        body containing a ``uuid`` field and also set a ``Location``
        header. The body is preferred and the header is the fallback.

        :param response: Response from a create call
        :type response: :py:class:`requests.Response`
        :raises NDExError: If no UUID can be recovered
        :return: UUID of the created item
        :rtype: str
        """
        body = Ndex3._parse_body(response)
        if isinstance(body, dict) and body.get('uuid') is not None:
            return str(body['uuid'])
        location = response.headers.get('Location')
        if location is not None and len(location) > 0:
            return location.rstrip('/').split('/')[-1]
        if isinstance(body, str) and len(body.strip()) > 0:
            return body.strip().strip('"')
        raise NDExError('Server did not return the UUID of the created '
                        'object')

    @staticmethod
    def _uuid_from_url(url):
        """
        Extracts the trailing UUID from a network URL.

        :param url: URL whose last path segment is a UUID
        :type url: str
        :return: The UUID
        :rtype: str
        """
        return str(url).rstrip('/').split('/')[-1]

    def _network_ref(self, response, return_url):
        """
        Returns either the UUID or the full URL of a created network.

        :param response: Response from a network create call
        :type response: :py:class:`requests.Response`
        :param return_url: If ``True`` return the full URL
        :type return_url: bool
        :raises NDExError: If neither form can be recovered
        :return: UUID, or full URL when *return_url* is ``True``
        :rtype: str
        """
        uuid_val = self._uuid_from_created(response)
        if return_url is not True:
            return uuid_val
        location = response.headers.get('Location')
        if location is not None and len(location) > 0:
            return location
        return (self.host + self.version_endpoint +
                Ndex3.NETWORKS_ROUTE + '/' + uuid_val)

    # ------------------------------------------------------------------
    # validation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _require_str(value, name):
        """
        Verifies *value* is a non empty string.

        :param value: Value to check
        :param name: Parameter name used in the error message
        :type name: str
        :raises NDExInvalidParameterError: If *value* is not a non empty
                                           string
        :return: *value* unchanged
        :rtype: str
        """
        if value is None:
            raise NDExInvalidParameterError(name + ' cannot be None')
        if not isinstance(value, str):
            raise NDExInvalidParameterError(name + ' must be a string')
        if len(value.strip()) == 0:
            raise NDExInvalidParameterError(name + ' cannot be empty')
        return value

    @staticmethod
    def _require_enum(value, valid, name, allow_none=True):
        """
        Verifies *value* is one of *valid*, case insensitively.

        :param value: Value to check
        :param valid: Permitted values
        :type valid: iterable of str
        :param name: Parameter name used in the error message
        :type name: str
        :param allow_none: If ``True`` a value of ``None`` is returned
                           as is
        :type allow_none: bool
        :raises NDExInvalidParameterError: If *value* is not permitted
        :return: Upper cased *value*, or ``None``
        :rtype: str
        """
        if value is None:
            if allow_none is True:
                return None
            raise NDExInvalidParameterError(name + ' cannot be None')
        if not isinstance(value, str):
            raise NDExInvalidParameterError(name + ' must be a string')
        upper = value.upper()
        if upper not in valid:
            raise NDExInvalidParameterError(
                name + ' must be one of ' + ', '.join(sorted(valid)) +
                ' but got ' + str(value))
        return upper

    @staticmethod
    def _require_id_list(values, name):
        """
        Normalizes a list of UUIDs to a list of strings.

        :param values: UUIDs
        :type values: list or str
        :param name: Parameter name used in the error message
        :type name: str
        :raises NDExInvalidParameterError: If *values* is empty or holds
                                           a non string entry
        :return: UUIDs as strings
        :rtype: list
        """
        if values is None:
            raise NDExInvalidParameterError(name + ' cannot be None')
        if isinstance(values, str):
            values = [values]
        try:
            id_list = [str(val) for val in values]
        except TypeError:
            raise NDExInvalidParameterError(name + ' must be a list of UUIDs')
        if len(id_list) == 0:
            raise NDExInvalidParameterError(name + ' cannot be empty')
        return id_list

    @staticmethod
    def _to_file_map(files, default_type=None):
        """
        Normalizes the many ways of naming file items into the
        ``{uuid: type}`` map the sharing and visibility endpoints want.

        Accepts a ``dict`` of UUID to :py:class:`FileType`, a list of
        ``(uuid, type)`` pairs, or a bare list of UUIDs when
        *default_type* is supplied.

        :param files: File items to normalize
        :type files: dict or list or str
        :param default_type: Type applied to entries that do not carry
                             one
        :type default_type: str
        :raises NDExInvalidParameterError: If *files* is empty, holds an
                                           unrecognized type, or omits a
                                           type with no *default_type*
                                           set
        :return: Map of UUID string to file type string
        :rtype: dict
        """
        default_type = Ndex3._require_enum(default_type, FileType.ALL,
                                           'default_type')
        if files is None:
            raise NDExInvalidParameterError('files cannot be None')

        if isinstance(files, str):
            files = [files]

        file_map = {}
        if isinstance(files, dict):
            pairs = files.items()
        else:
            pairs = []
            for entry in files:
                if isinstance(entry, str):
                    pairs.append((entry, default_type))
                elif isinstance(entry, (list, tuple)) and len(entry) == 2:
                    pairs.append((entry[0], entry[1]))
                else:
                    raise NDExInvalidParameterError(
                        'files entries must be UUID strings or '
                        '(uuid, type) pairs')

        for uuid_val, type_val in pairs:
            if type_val is None:
                type_val = default_type
            if type_val is None:
                raise NDExInvalidParameterError(
                    'No file type given for ' + str(uuid_val) +
                    ' and no default_type set')
            file_map[str(uuid_val)] = Ndex3._require_enum(str(type_val),
                                                          FileType.ALL,
                                                          'file type',
                                                          allow_none=False)
        if len(file_map) == 0:
            raise NDExInvalidParameterError('files cannot be empty')
        return file_map

    # ------------------------------------------------------------------
    # server status
    # ------------------------------------------------------------------

    def update_status(self):
        """
        Queries ``GET /v3/admin/status`` and caches the result on
        ``self.status``.

        :raises NDExError: If the server does not answer the v3 status
                           endpoint
        :return: Server status
        :rtype: dict
        """
        status = self._request('GET', '/admin/status',
                               params={'format': 'full'})
        if not isinstance(status, dict):
            raise NDExError('Server did not return a v3 status object; '
                            'this host may not support the v3 API')
        self.status = status
        return status

    # ------------------------------------------------------------------
    # folders
    # ------------------------------------------------------------------

    def create_folder(self, name, parent=None, description=None,
                      visibility=None):
        """
        Creates a folder.

        Corresponds to ``POST /v3/files/folders/``.

        :param name: Name of the new folder
        :type name: str
        :param parent: UUID of the parent folder. Omit to create the
                       folder at the top level of the user's home.
        :type parent: str
        :param description: Optional description
        :type description: str
        :param visibility: One of :py:class:`Visibility`. Defaults to
                           the server default of ``PRIVATE``.
        :type visibility: str
        :raises NDExInvalidParameterError: For invalid parameters
        :raises NDExUnauthorizedError: If not authenticated or lacking
                                       write access to *parent*
        :raises NDExError: For other server errors
        :return: UUID of the new folder
        :rtype: str
        """
        self._require_auth()
        self._require_str(name, 'name')
        body = {'name': name}
        if parent is not None:
            body['parent'] = str(parent)
        if description is not None:
            body['description'] = description
        vis = self._require_enum(visibility, Visibility.ALL, 'visibility')
        if vis is not None:
            body['visibility'] = vis
        response = self._request('POST', Ndex3.FOLDERS_ROUTE + '/',
                                 json_body=body, return_response=True)
        return self._uuid_from_created(response)

    def get_folder(self, folder_id, access_key=None):
        """
        Retrieves a folder.

        Corresponds to ``GET /v3/files/folders/{folderid}``.

        :param folder_id: UUID of the folder
        :type folder_id: str
        :param access_key: Access key granting read access to an
                           otherwise inaccessible folder
        :type access_key: str
        :raises NDExInvalidParameterError: For an invalid *folder_id*
        :raises NDExNotFoundError: If no such folder exists
        :raises NDExUnauthorizedError: If read access is denied
        :return: Folder with keys including ``externalId``, ``name``,
                 ``parent``, ``description``, ``owner``, ``owner_id``,
                 ``visibility``, ``creationTime`` and
                 ``modificationTime``
        :rtype: dict
        """
        self._require_str(folder_id, 'folder_id')
        return self._request('GET',
                             Ndex3.FOLDERS_ROUTE + '/' + str(folder_id),
                             params={'accesskey': access_key})

    def update_folder(self, folder_id, name=None, parent=None,
                      description=None, visibility=None):
        """
        Updates a folder.

        Corresponds to ``PUT /v3/files/folders/{folderid}``. Setting
        *parent* moves the folder.

        :param folder_id: UUID of the folder to update
        :type folder_id: str
        :param name: New name
        :type name: str
        :param parent: UUID of the new parent folder
        :type parent: str
        :param description: New description
        :type description: str
        :param visibility: One of :py:class:`Visibility`
        :type visibility: str
        :raises NDExInvalidParameterError: If no field to update is
                                           given, or a value is invalid
        :raises NDExNotFoundError: If no such folder exists
        :raises NDExUnauthorizedError: If write access is denied
        :return: ``None``
        """
        self._require_auth()
        self._require_str(folder_id, 'folder_id')
        body = {}
        if name is not None:
            body['name'] = self._require_str(name, 'name')
        if parent is not None:
            body['parent'] = str(parent)
        if description is not None:
            body['description'] = description
        vis = self._require_enum(visibility, Visibility.ALL, 'visibility')
        if vis is not None:
            body['visibility'] = vis
        if len(body) == 0:
            raise NDExInvalidParameterError('At least one of name, parent, '
                                            'description or visibility must '
                                            'be set')
        return self._request('PUT',
                             Ndex3.FOLDERS_ROUTE + '/' + str(folder_id),
                             json_body=body)

    def delete_folder(self, folder_id, force=False, permanent=False):
        """
        Deletes a folder.

        Corresponds to ``DELETE /v3/files/folders/{folderid}``. By
        default the folder is moved to the trash and the server refuses
        to delete a folder that still has children.

        :param folder_id: UUID of the folder
        :type folder_id: str
        :param force: If ``True`` delete the folder even when it still
                      contains items
        :type force: bool
        :param permanent: If ``True`` bypass the trash and delete
                          irrecoverably
        :type permanent: bool
        :raises NDExInvalidParameterError: For an invalid *folder_id*
        :raises NDExNotFoundError: If no such folder exists
        :raises NDExUnauthorizedError: If delete access is denied
        :return: ``None``
        """
        self._require_auth()
        self._require_str(folder_id, 'folder_id')
        return self._request('DELETE',
                             Ndex3.FOLDERS_ROUTE + '/' + str(folder_id),
                             params={'force': str(bool(force)).lower(),
                                     'permanent':
                                     str(bool(permanent)).lower()})

    def list_folder_items(self, folder_id, format='update', item_type=None,
                          access_key=None):
        """
        Lists the direct children of a folder.

        Corresponds to ``GET /v3/files/folders/{folderid}/list``.

        :param folder_id: UUID of the folder
        :type folder_id: str
        :param format: ``update`` for the full item summary or
                       ``compact`` for a reduced one
        :type format: str
        :param item_type: Restrict results to one
                          :py:class:`FileType`. Omit for all types.
        :type item_type: str
        :param access_key: Access key granting read access
        :type access_key: str
        :raises NDExInvalidParameterError: For invalid parameters
        :raises NDExNotFoundError: If no such folder exists
        :raises NDExUnauthorizedError: If read access is denied
        :return: File item summaries, each with keys including ``uuid``,
                 ``type``, ``name``, ``owner``, ``visibility``,
                 ``permission``, ``edges`` and ``modificationTime``
        :rtype: list
        """
        self._require_str(folder_id, 'folder_id')
        params = {'format': format,
                  'accesskey': access_key,
                  'type': self._require_enum(item_type, FileType.ALL,
                                             'item_type')}
        result = self._request('GET',
                               Ndex3.FOLDERS_ROUTE + '/' + str(folder_id) +
                               '/list', params=params)
        return [] if result is None else result

    def get_folder_child_count(self, folder_id, access_key=None):
        """
        Counts the direct children of a folder by type.

        Corresponds to ``GET /v3/files/folders/{folderid}/count``.

        :param folder_id: UUID of the folder
        :type folder_id: str
        :param access_key: Access key granting read access
        :type access_key: str
        :raises NDExNotFoundError: If no such folder exists
        :return: Counts keyed by ``network``, ``folder`` and
                 ``shortcut``
        :rtype: dict
        """
        self._require_str(folder_id, 'folder_id')
        return self._request('GET',
                             Ndex3.FOLDERS_ROUTE + '/' + str(folder_id) +
                             '/count',
                             params={'accesskey': access_key})

    def get_folder_access_key(self, folder_id):
        """
        Retrieves the access key of a shared folder.

        Corresponds to ``GET
        /v3/files/folders/{folderid}/accesskey``. Use
        :py:meth:`share_files` to create one.

        :param folder_id: UUID of the folder
        :type folder_id: str
        :raises NDExNotFoundError: If no such folder exists
        :raises NDExUnauthorizedError: If not the folder owner
        :return: Map containing the access key
        :rtype: dict
        """
        self._require_auth()
        self._require_str(folder_id, 'folder_id')
        return self._request('GET',
                             Ndex3.FOLDERS_ROUTE + '/' + str(folder_id) +
                             '/accesskey')

    def list_folders(self, limit=100):
        """
        Lists folders owned by the authenticated user.

        Corresponds to ``GET /v3/files/folders/``. The listing is flat
        and spans all nesting levels; use the ``parent`` field of each
        entry to rebuild the tree.

        :param limit: Maximum number of folders to return
        :type limit: int
        :raises NDExUnauthorizedError: If not authenticated
        :return: Folders owned by the user
        :rtype: list
        """
        self._require_auth()
        result = self._request('GET', Ndex3.FOLDERS_ROUTE + '/',
                               params={'limit': limit})
        return [] if result is None else result

    # ------------------------------------------------------------------
    # shortcuts
    # ------------------------------------------------------------------

    def create_shortcut(self, name, target, target_type, parent=None,
                        visibility=None):
        """
        Creates a shortcut pointing at another file item.

        Corresponds to ``POST /v3/files/shortcuts/``. A shortcut lets
        one network or folder appear in several folders without being
        copied.

        :param name: Name of the shortcut
        :type name: str
        :param target: UUID of the item the shortcut points at
        :type target: str
        :param target_type: Type of *target*, one of
                            :py:class:`FileType`
        :type target_type: str
        :param parent: UUID of the folder holding the shortcut. Omit for
                       the top level of the user's home.
        :type parent: str
        :param visibility: One of :py:class:`Visibility`
        :type visibility: str
        :raises NDExInvalidParameterError: For invalid parameters
        :raises NDExUnauthorizedError: If not authenticated or lacking
                                       access to *target*
        :return: UUID of the new shortcut
        :rtype: str
        """
        self._require_auth()
        self._require_str(name, 'name')
        self._require_str(str(target), 'target')
        body = {'name': name,
                'target': str(target),
                'targetType': self._require_enum(target_type, FileType.ALL,
                                                 'target_type',
                                                 allow_none=False)}
        if parent is not None:
            body['parent'] = str(parent)
        vis = self._require_enum(visibility, Visibility.ALL, 'visibility')
        if vis is not None:
            body['visibility'] = vis
        response = self._request('POST', Ndex3.SHORTCUTS_ROUTE + '/',
                                 json_body=body, return_response=True)
        return self._uuid_from_created(response)

    def get_shortcut(self, shortcut_id):
        """
        Retrieves a shortcut.

        Corresponds to ``GET /v3/files/shortcuts/{shortcutid}``.

        :param shortcut_id: UUID of the shortcut
        :type shortcut_id: str
        :raises NDExNotFoundError: If no such shortcut exists
        :raises NDExUnauthorizedError: If read access is denied
        :return: Shortcut with keys including ``externalId``, ``name``,
                 ``parent``, ``target``, ``targetType``, ``owner`` and
                 ``visibility``
        :rtype: dict
        """
        self._require_str(shortcut_id, 'shortcut_id')
        return self._request('GET',
                             Ndex3.SHORTCUTS_ROUTE + '/' + str(shortcut_id))

    def update_shortcut(self, shortcut_id, name=None, parent=None,
                        target=None, target_type=None, visibility=None):
        """
        Updates a shortcut.

        Corresponds to ``PUT /v3/files/shortcuts/{shortcutid}``.

        :param shortcut_id: UUID of the shortcut to update
        :type shortcut_id: str
        :param name: New name
        :type name: str
        :param parent: UUID of the new parent folder
        :type parent: str
        :param target: UUID of the new target
        :type target: str
        :param target_type: Type of *target*, one of
                            :py:class:`FileType`
        :type target_type: str
        :param visibility: One of :py:class:`Visibility`
        :type visibility: str
        :raises NDExInvalidParameterError: If no field to update is
                                           given, or a value is invalid
        :raises NDExNotFoundError: If no such shortcut exists
        :raises NDExUnauthorizedError: If write access is denied
        :return: ``None``
        """
        self._require_auth()
        self._require_str(shortcut_id, 'shortcut_id')
        body = {}
        if name is not None:
            body['name'] = self._require_str(name, 'name')
        if parent is not None:
            body['parent'] = str(parent)
        if target is not None:
            body['target'] = str(target)
        t_type = self._require_enum(target_type, FileType.ALL, 'target_type')
        if t_type is not None:
            body['targetType'] = t_type
        vis = self._require_enum(visibility, Visibility.ALL, 'visibility')
        if vis is not None:
            body['visibility'] = vis
        if len(body) == 0:
            raise NDExInvalidParameterError('At least one of name, parent, '
                                            'target, target_type or '
                                            'visibility must be set')
        return self._request('PUT',
                             Ndex3.SHORTCUTS_ROUTE + '/' + str(shortcut_id),
                             json_body=body)

    def delete_shortcut(self, shortcut_id):
        """
        Deletes a shortcut. The target is left untouched.

        Corresponds to ``DELETE /v3/files/shortcuts/{shortcutid}``.

        :param shortcut_id: UUID of the shortcut
        :type shortcut_id: str
        :raises NDExNotFoundError: If no such shortcut exists
        :raises NDExUnauthorizedError: If delete access is denied
        :return: ``None``
        """
        self._require_auth()
        self._require_str(shortcut_id, 'shortcut_id')
        return self._request('DELETE',
                             Ndex3.SHORTCUTS_ROUTE + '/' + str(shortcut_id))

    def list_shortcuts(self):
        """
        Lists shortcuts owned by the authenticated user.

        Corresponds to ``GET /v3/files/shortcuts/``.

        :raises NDExUnauthorizedError: If not authenticated
        :return: Shortcuts owned by the user
        :rtype: list
        """
        self._require_auth()
        result = self._request('GET', Ndex3.SHORTCUTS_ROUTE + '/')
        return [] if result is None else result

    # ------------------------------------------------------------------
    # files: counts, trash, copy
    # ------------------------------------------------------------------

    def get_file_count(self):
        """
        Counts all file items owned by the authenticated user, by type.

        Corresponds to ``GET /v3/files/count``.

        :raises NDExUnauthorizedError: If not authenticated
        :return: Counts keyed by ``network``, ``folder`` and
                 ``shortcut``
        :rtype: dict
        """
        self._require_auth()
        return self._request('GET', Ndex3.FILES_ROUTE + '/count')

    def list_trash(self):
        """
        Lists the authenticated user's trashed items.

        Corresponds to ``GET /v3/files/trash``.

        :raises NDExUnauthorizedError: If not authenticated
        :return: File item summaries for trashed items
        :rtype: list
        """
        self._require_auth()
        result = self._request('GET', Ndex3.FILES_ROUTE + '/trash')
        return [] if result is None else result

    def restore_from_trash(self, networks=None, folders=None,
                           shortcuts=None):
        """
        Restores items from the trash to their previous location.

        Corresponds to ``POST /v3/files/trash/restore``.

        :param networks: UUIDs of networks to restore
        :type networks: list
        :param folders: UUIDs of folders to restore
        :type folders: list
        :param shortcuts: UUIDs of shortcuts to restore
        :type shortcuts: list
        :raises NDExInvalidParameterError: If all three arguments are
                                           omitted
        :raises NDExUnauthorizedError: If not authenticated
        :return: ``None``
        """
        self._require_auth()
        body = {}
        if networks is not None:
            body['networks'] = self._require_id_list(networks, 'networks')
        if folders is not None:
            body['folders'] = self._require_id_list(folders, 'folders')
        if shortcuts is not None:
            body['shortcuts'] = self._require_id_list(shortcuts, 'shortcuts')
        if len(body) == 0:
            raise NDExInvalidParameterError('At least one of networks, '
                                            'folders or shortcuts must be '
                                            'set')
        return self._request('POST', Ndex3.FILES_ROUTE + '/trash/restore',
                             json_body=body)

    def clear_trash(self):
        """
        Permanently deletes everything in the authenticated user's
        trash. This cannot be undone.

        Corresponds to ``DELETE /v3/files/trash``.

        :raises NDExUnauthorizedError: If not authenticated
        :return: ``None``
        """
        self._require_auth()
        return self._request('DELETE', Ndex3.FILES_ROUTE + '/trash')

    def delete_trashed_item(self, item_id):
        """
        Permanently deletes a single trashed item.

        Corresponds to ``DELETE /v3/files/trash/{uuid}``.

        :param item_id: UUID of the trashed item
        :type item_id: str
        :raises NDExNotFoundError: If the item is not in the trash
        :raises NDExUnauthorizedError: If not the item owner
        :return: ``None``
        """
        self._require_auth()
        self._require_str(item_id, 'item_id')
        return self._request('DELETE',
                             Ndex3.FILES_ROUTE + '/trash/' + str(item_id))

    def copy_file(self, file_id, file_type, target_id, access_key=None):
        """
        Copies a network or shortcut into a folder.

        Corresponds to ``POST /v3/files/copy``.

        :param file_id: UUID of the item to copy
        :type file_id: str
        :param file_type: Type of the item, ``NETWORK`` or ``SHORTCUT``
        :type file_type: str
        :param target_id: UUID of the destination folder
        :type target_id: str
        :param access_key: Access key granting read access to *file_id*
        :type access_key: str
        :raises NDExInvalidParameterError: For invalid parameters
        :raises NDExUnauthorizedError: If access is denied to the source
                                       or destination
        :raises NDExError: If the copy fails, for example on exceeding
                           the disk quota
        :return: UUID of the new copy
        :rtype: str
        """
        self._require_auth()
        self._require_str(str(file_id), 'file_id')
        self._require_str(str(target_id), 'target_id')
        body = {'fileId': str(file_id),
                'type': self._require_enum(file_type, FileType.ALL,
                                           'file_type', allow_none=False),
                'targetId': str(target_id)}
        response = self._request('POST', Ndex3.FILES_ROUTE + '/copy',
                                 params={'accesskey': access_key},
                                 json_body=body, return_response=True)
        return self._uuid_from_created(response)

    # ------------------------------------------------------------------
    # files: sharing
    # ------------------------------------------------------------------

    def set_sharing_members(self, files, members, default_type=None):
        """
        Grants or changes per user permissions on file items.

        Corresponds to ``POST /v3/files/sharing/members``. This is the
        v3 replacement for the v2 group and user permission calls.

        :param files: Items to share. A ``{uuid: type}`` map, a list of
                      ``(uuid, type)`` pairs, or a list of UUIDs when
                      *default_type* is set.
        :type files: dict or list
        :param members: Map of user UUID to one of
                        :py:class:`Permissions`
        :type members: dict
        :param default_type: :py:class:`FileType` applied to entries in
                             *files* that do not carry one
        :type default_type: str
        :raises NDExInvalidParameterError: For invalid parameters
        :raises NDExUnauthorizedError: If not authorized to share an
                                       item
        :return: Server response describing the resulting permissions
        :rtype: dict
        """
        self._require_auth()
        if not isinstance(members, dict) or len(members) == 0:
            raise NDExInvalidParameterError('members must be a non empty '
                                            'dict of user UUID to '
                                            'permission')
        member_map = {}
        for user_id, permission in members.items():
            member_map[str(user_id)] = self._require_enum(
                str(permission), Permissions.ALL, 'permission',
                allow_none=False)
        body = {'files': self._to_file_map(files,
                                           default_type=default_type),
                'members': member_map}
        return self._request('POST', Ndex3.FILES_ROUTE + '/sharing/members',
                             json_body=body)

    def list_sharing_members(self, files, default_type=None):
        """
        Lists the users a set of file items is shared with.

        Corresponds to ``POST /v3/files/sharing/members/list``.

        :param files: Items to inspect, in any form accepted by
                      :py:meth:`set_sharing_members`
        :type files: dict or list
        :param default_type: :py:class:`FileType` applied to entries in
                             *files* that do not carry one
        :type default_type: str
        :raises NDExInvalidParameterError: For invalid parameters
        :raises NDExUnauthorizedError: If not authorized
        :return: Membership records for the requested items
        :rtype: list
        """
        self._require_auth()
        body = self._to_file_map(files, default_type=default_type)
        result = self._request('POST',
                               Ndex3.FILES_ROUTE + '/sharing/members/list',
                               json_body=body)
        return [] if result is None else result

    def share_files(self, files, default_type=None):
        """
        Generates public access keys for file items.

        Corresponds to ``POST /v3/files/sharing/share``. Anyone holding
        a returned key can read the item by passing it as the
        ``access_key`` argument of the read methods.

        :param files: Items to share, in any form accepted by
                      :py:meth:`set_sharing_members`
        :type files: dict or list
        :param default_type: :py:class:`FileType` applied to entries in
                             *files* that do not carry one
        :type default_type: str
        :raises NDExInvalidParameterError: For invalid parameters
        :raises NDExUnauthorizedError: If not the owner of an item
        :return: Map of item UUID to its new access key
        :rtype: dict
        """
        self._require_auth()
        body = {'files': self._to_file_map(files,
                                           default_type=default_type)}
        return self._request('POST', Ndex3.FILES_ROUTE + '/sharing/share',
                             json_body=body)

    def unshare_files(self, files, default_type=None):
        """
        Revokes the public access keys of file items.

        Corresponds to ``POST /v3/files/sharing/unshare``.

        :param files: Items to unshare, in any form accepted by
                      :py:meth:`set_sharing_members`
        :type files: dict or list
        :param default_type: :py:class:`FileType` applied to entries in
                             *files* that do not carry one
        :type default_type: str
        :raises NDExInvalidParameterError: For invalid parameters
        :raises NDExUnauthorizedError: If not the owner of an item
        :return: ``None``
        """
        self._require_auth()
        body = {'files': self._to_file_map(files,
                                           default_type=default_type)}
        return self._request('POST', Ndex3.FILES_ROUTE + '/sharing/unshare',
                             json_body=body)

    def transfer_network_ownership(self, networks, new_owner):
        """
        Transfers ownership of networks to another user.

        Corresponds to ``POST /v3/files/sharing/transfer``.

        :param networks: UUIDs of the networks to transfer
        :type networks: list
        :param new_owner: UUID of the user receiving ownership
        :type new_owner: str
        :raises NDExInvalidParameterError: For invalid parameters
        :raises NDExUnauthorizedError: If not the current owner
        :return: ``None``
        """
        self._require_auth()
        self._require_str(str(new_owner), 'new_owner')
        body = {'networks': self._require_id_list(networks, 'networks'),
                'new_owner': str(new_owner)}
        return self._request('POST', Ndex3.FILES_ROUTE + '/sharing/transfer',
                             json_body=body)

    def list_shared_files(self, limit=100):
        """
        Lists file items the authenticated user has shared.

        Corresponds to ``GET /v3/files/sharing/list``.

        :param limit: Maximum number of items to return
        :type limit: int
        :raises NDExUnauthorizedError: If not authenticated
        :return: File item summaries for shared items
        :rtype: list
        """
        self._require_auth()
        result = self._request('GET', Ndex3.FILES_ROUTE + '/sharing/list',
                               params={'limit': limit})
        return [] if result is None else result

    # ------------------------------------------------------------------
    # batch
    # ------------------------------------------------------------------

    def get_network_summaries(self, network_ids, access_key=None,
                              format='FULL'):
        """
        Retrieves summaries for many networks in one call.

        Corresponds to ``POST /v3/batch/networks/summary``.

        :param network_ids: UUIDs of the networks
        :type network_ids: list
        :param access_key: Access key granting read access
        :type access_key: str
        :param format: ``FULL`` or ``COMPACT``
        :type format: str
        :raises NDExInvalidParameterError: For invalid parameters
        :return: Network summaries
        :rtype: list
        """
        body = self._require_id_list(network_ids, 'network_ids')
        result = self._request('POST',
                               Ndex3.BATCH_ROUTE + '/networks/summary',
                               params={'accesskey': access_key,
                                       'format': format},
                               json_body=body)
        return [] if result is None else result

    def move_networks_to_folder(self, target_folder, networks):
        """
        Moves networks into a folder.

        Corresponds to ``POST /v3/batch/networks/move``. This is the v3
        replacement for adding networks to a network set.

        :param target_folder: UUID of the destination folder
        :type target_folder: str
        :param networks: UUIDs of the networks to move
        :type networks: list
        :raises NDExInvalidParameterError: For invalid parameters
        :raises NDExUnauthorizedError: If write access is denied to the
                                       folder or a network
        :return: ``None``
        """
        self._require_auth()
        self._require_str(str(target_folder), 'target_folder')
        body = {'targetFolder': str(target_folder),
                'networks': self._require_id_list(networks, 'networks')}
        return self._request('POST', Ndex3.BATCH_ROUTE + '/networks/move',
                             json_body=body)

    def set_file_visibility(self, visibility, files, default_type=None):
        """
        Sets the visibility of many file items in one call.

        Corresponds to ``POST /v3/batch/files/setvisibility``.

        :param visibility: One of :py:class:`Visibility`
        :type visibility: str
        :param files: Items to update, in any form accepted by
                      :py:meth:`set_sharing_members`
        :type files: dict or list
        :param default_type: :py:class:`FileType` applied to entries in
                             *files* that do not carry one
        :type default_type: str
        :raises NDExInvalidParameterError: For invalid parameters
        :raises NDExUnauthorizedError: If write access is denied
        :return: ``None``
        """
        self._require_auth()
        body = {'visibility': self._require_enum(visibility, Visibility.ALL,
                                                 'visibility',
                                                 allow_none=False),
                'files': self._to_file_map(files,
                                           default_type=default_type)}
        return self._request('POST',
                             Ndex3.BATCH_ROUTE + '/files/setvisibility',
                             json_body=body)

    # ------------------------------------------------------------------
    # search
    # ------------------------------------------------------------------

    def search_files(self, search_string='', account_name=None,
                     permission=None, file_type=None, visibility=None,
                     start=0, size=100):
        """
        Searches file items.

        Corresponds to ``POST /v3/search/files``. This replaces the v2
        network search and covers folders and shortcuts as well as
        networks.

        :param search_string: Query text. An empty string matches
                              everything.
        :type search_string: str
        :param account_name: Restrict results to items owned by this
                             account
        :type account_name: str
        :param permission: Restrict results to items on which the caller
                           holds this permission, one of
                           :py:class:`Permissions`
        :type permission: str
        :param file_type: Restrict results to one :py:class:`FileType`
        :type file_type: str
        :param visibility: ``PUBLIC`` or ``PRIVATE``. Defaults to
                           ``PUBLIC`` on the server. ``PRIVATE``
                           requires authentication. ``UNLISTED`` is
                           rejected by the server.
        :type visibility: str
        :param start: Zero based index of the first result
        :type start: int
        :param size: Maximum number of results
        :type size: int
        :raises NDExInvalidParameterError: For invalid parameters,
                                           including a *visibility* of
                                           ``UNLISTED``
        :raises NDExUnauthorizedError: For a ``PRIVATE`` search without
                                       credentials
        :return: Results with keys ``numFound``, ``start`` and ``files``
        :rtype: dict
        """
        vis = self._require_enum(visibility, Visibility.ALL, 'visibility')
        if vis == Visibility.UNLISTED:
            raise NDExInvalidParameterError('visibility of UNLISTED is not a '
                                            'valid search mode; use PUBLIC '
                                            'or PRIVATE')
        if vis == Visibility.PRIVATE:
            self._require_auth()

        body = {'searchString': search_string if search_string is not None
                else ''}
        if account_name is not None:
            body['accountName'] = account_name
        perm = self._require_enum(permission, Permissions.ALL, 'permission')
        if perm is not None:
            body['permission'] = perm
        f_type = self._require_enum(file_type, FileType.ALL, 'file_type')
        if f_type is not None:
            body['type'] = f_type

        return self._request('POST', Ndex3.SEARCH_ROUTE + '/files',
                             params={'visibility': vis,
                                     'start': start,
                                     'size': size},
                             json_body=body)

    # ------------------------------------------------------------------
    # networks
    # ------------------------------------------------------------------

    def get_network_summary(self, network_id, access_key=None,
                            format='FULL'):
        """
        Retrieves the summary of a network.

        Corresponds to ``GET /v3/networks/{networkid}/summary``. The v3
        summary adds a ``folderId`` field naming the folder holding the
        network.

        :param network_id: UUID of the network
        :type network_id: str
        :param access_key: Access key granting read access
        :type access_key: str
        :param format: ``FULL`` or ``COMPACT``
        :type format: str
        :raises NDExNotFoundError: If no such network exists
        :raises NDExUnauthorizedError: If read access is denied
        :return: Network summary
        :rtype: dict
        """
        self._require_str(network_id, 'network_id')
        return self._request('GET',
                             Ndex3.NETWORKS_ROUTE + '/' + str(network_id) +
                             '/summary',
                             params={'accesskey': access_key,
                                     'format': format})

    def save_new_cx2_network_in_folder(self, cx, visibility=None,
                                       folder_id=None, indexed_fields=None,
                                       return_url=False):
        """
        Creates a network from a CX2 object, optionally placing it
        directly into a folder.

        Corresponds to ``POST /v3/networks``. Unlike
        :py:meth:`~ndex2.client.Ndex2.save_new_cx2_network` this accepts
        a *folder_id*, saving a follow up call to
        :py:meth:`move_networks_to_folder`.

        :param cx: CX2 network as a list of aspect dicts
        :type cx: list
        :param visibility: ``PUBLIC`` or ``PRIVATE``. Defaults to the
                           server default of ``PRIVATE``.
        :type visibility: str
        :param folder_id: UUID of the folder to create the network in
        :type folder_id: str
        :param indexed_fields: Additional fields to index. Not yet
                               implemented server side.
        :type indexed_fields: list
        :param return_url: If ``True`` return the full URL of the new
                           network rather than its UUID. Defaults to
                           ``False``; note this is the opposite of
                           :py:meth:`~ndex2.client.Ndex2.save_new_cx2_network`
                           on :py:class:`~ndex2.client.Ndex2`, which always
                           returns a URL.
        :type return_url: bool
        :raises NDExInvalidParameterError: If *cx* is not a list
        :raises NDExUnauthorizedError: If not authenticated
        :return: UUID of the new network, or its full URL when
                 *return_url* is ``True``
        :rtype: str
        """
        self._require_auth()
        if not isinstance(cx, list):
            raise NDExInvalidParameterError('cx must be a list of aspects')
        params = {'visibility': self._require_enum(visibility,
                                                   Visibility.ALL,
                                                   'visibility')}
        if folder_id is not None:
            params['folderId'] = str(folder_id)
        if indexed_fields is not None:
            params['indexedfields'] = ','.join(indexed_fields)
        response = self._request('POST', Ndex3.NETWORKS_ROUTE,
                                 params=params, json_body=cx,
                                 return_response=True)
        return self._network_ref(response, return_url)

    def delete_network(self, network_id, permanent=False):
        """
        Deletes a network.

        Corresponds to ``DELETE /v3/networks/{networkid}``. By default
        the network is moved to the trash and can be restored with
        :py:meth:`restore_from_trash`.

        :param network_id: UUID of the network
        :type network_id: str
        :param permanent: If ``True`` bypass the trash and delete
                          irrecoverably
        :type permanent: bool
        :raises NDExNotFoundError: If no such network exists
        :raises NDExUnauthorizedError: If delete access is denied
        :return: ``None``
        """
        self._require_auth()
        self._require_str(network_id, 'network_id')
        return self._request('DELETE',
                             Ndex3.NETWORKS_ROUTE + '/' + str(network_id),
                             params={'permanent':
                                     str(bool(permanent)).lower()})

    def get_network_aspects(self, network_id, access_key=None):
        """
        Lists the CX2 aspect metadata of a network.

        Corresponds to ``GET /v3/networks/{networkid}/aspects``.

        :param network_id: UUID of the network
        :type network_id: str
        :param access_key: Access key granting read access
        :type access_key: str
        :raises NDExNotFoundError: If no such network exists
        :return: Aspect metadata entries
        :rtype: list
        """
        self._require_str(network_id, 'network_id')
        result = self._request('GET',
                               Ndex3.NETWORKS_ROUTE + '/' + str(network_id) +
                               '/aspects',
                               params={'accesskey': access_key})
        return [] if result is None else result

    def export_network_as_tsv(self, network_id, type='node',
                              include_header=True, list_delimiter=',',
                              node_key='id', access_key=None):
        """
        Exports a network as tab separated text.

        Corresponds to ``GET /v3/networks/{networkid}/export``.

        :param network_id: UUID of the network
        :type network_id: str
        :param type: ``node`` or ``edge``
        :type type: str
        :param include_header: If ``True`` emit a header row
        :type include_header: bool
        :param list_delimiter: Separator used inside list valued
                               attributes
        :type list_delimiter: str
        :param node_key: Node attribute used to identify nodes in edge
                         rows
        :type node_key: str
        :param access_key: Access key granting read access
        :type access_key: str
        :raises NDExNotFoundError: If no such network exists
        :return: Streamed response whose body is the TSV text
        :rtype: :py:class:`requests.Response`
        """
        self._require_str(network_id, 'network_id')
        return self._request('GET',
                             Ndex3.NETWORKS_ROUTE + '/' + str(network_id) +
                             '/export',
                             params={'accesskey': access_key,
                                     'type': type,
                                     'header':
                                         str(bool(include_header)).lower(),
                                     'listdelimiter': list_delimiter,
                                     'nodekey': node_key},
                             stream=True)

    def mint_doi(self, network_id, key, email):
        """
        Requests a DOI for a network.

        Corresponds to ``GET /v3/networks/{networkid}/DOI``.

        :param network_id: UUID of the network
        :type network_id: str
        :param key: Encrypted key issued by the server authorizing the
                    request
        :type key: str
        :param email: Email address of the submitter
        :type email: str
        :raises NDExInvalidParameterError: For invalid parameters
        :raises NDExUnauthorizedError: If the key is not valid for the
                                       network
        :return: Server response describing the request
        :rtype: str
        """
        self._require_str(network_id, 'network_id')
        self._require_str(key, 'key')
        self._require_str(email, 'email')
        return self._request('GET',
                             Ndex3.NETWORKS_ROUTE + '/' + str(network_id) +
                             '/DOI',
                             params={'key': key, 'email': email})

    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------

    def get_user_by_username(self, username):
        """
        Retrieves a user by account name.

        Corresponds to ``GET /v3/users?username=``.

        :param username: Account name of the user
        :type username: str
        :raises NDExInvalidParameterError: For an invalid *username*
        :raises NDExNotFoundError: If no such user exists
        :return: User record
        :rtype: dict
        """
        self._require_str(username, 'username')
        return self._request('GET', Ndex3.USERS_ROUTE,
                             params={'username': username})

    def get_user_home(self, user_id, format='update'):
        """
        Lists the contents of a user's home directory.

        Corresponds to ``GET /v3/users/{userid}/home``. This is the
        entry point for walking a user's folder tree: it returns the
        items that have no parent folder. Anonymous callers see only
        public items.

        :param user_id: UUID of the user
        :type user_id: str
        :param format: ``update`` for full item summaries or ``compact``
                       for reduced ones
        :type format: str
        :raises NDExInvalidParameterError: For an invalid *user_id*
        :raises NDExNotFoundError: If no such user exists
        :return: File item summaries at the root of the user's home
        :rtype: list
        """
        self._require_str(str(user_id), 'user_id')
        result = self._request('GET',
                               Ndex3.USERS_ROUTE + '/' + str(user_id) +
                               '/home',
                               params={'format': format})
        return [] if result is None else result

    def get_workspaces_for_user(self, user_id):
        """
        Lists the Cytoscape Web workspaces of a user.

        Corresponds to ``GET /v3/users/{userid}/workspaces``.

        :param user_id: UUID of the user
        :type user_id: str
        :raises NDExUnauthorizedError: If not authorized to view the
                                       user's workspaces
        :return: Workspaces
        :rtype: list
        """
        self._require_str(str(user_id), 'user_id')
        result = self._request('GET',
                               Ndex3.USERS_ROUTE + '/' + str(user_id) +
                               '/workspaces')
        return [] if result is None else result

    def signin(self, id_token):
        """
        Signs in with an OAuth/Keycloak id token and returns the
        matching user.

        Corresponds to ``POST /v3/users/signin``. On success the token
        is retained on this client and sent as a bearer token on
        subsequent requests.

        :param id_token: OAuth/Keycloak id token
        :type id_token: str
        :raises NDExInvalidParameterError: For an invalid *id_token*
        :raises NDExUnauthorizedError: If the token is rejected
        :return: User record for the signed in account
        :rtype: dict
        """
        self._require_str(id_token, 'id_token')
        user = self._request('POST', Ndex3.USERS_ROUTE + '/signin',
                             json_body={'id_token': id_token})
        self.bearer_token = id_token
        self.s.headers['Authorization'] = 'Bearer ' + id_token
        self.s.auth = None
        return user

    # ------------------------------------------------------------------
    # workspaces
    # ------------------------------------------------------------------

    def create_workspace(self, name, options=None, network_ids=None):
        """
        Creates a Cytoscape Web workspace.

        Corresponds to ``POST /v3/workspaces``.

        :param name: Name of the workspace
        :type name: str
        :param options: Free form workspace options
        :type options: dict
        :param network_ids: UUIDs of networks in the workspace
        :type network_ids: list
        :raises NDExInvalidParameterError: For invalid parameters
        :raises NDExUnauthorizedError: If not authenticated
        :return: UUID of the new workspace
        :rtype: str
        """
        self._require_auth()
        self._require_str(name, 'name')
        body = {'name': name}
        if options is not None:
            body['options'] = options
        if network_ids is not None:
            body['networkIDs'] = self._require_id_list(network_ids,
                                                       'network_ids')
        response = self._request('POST', Ndex3.WORKSPACES_ROUTE,
                                 json_body=body, return_response=True)
        return self._uuid_from_created(response)

    def get_workspace(self, workspace_id):
        """
        Retrieves a workspace.

        Corresponds to ``GET /v3/workspaces/{workspaceid}``.

        :param workspace_id: UUID of the workspace
        :type workspace_id: str
        :raises NDExNotFoundError: If no such workspace exists
        :raises NDExUnauthorizedError: If read access is denied
        :return: Workspace with keys including ``name``, ``options`` and
                 ``networkIDs``
        :rtype: dict
        """
        self._require_str(workspace_id, 'workspace_id')
        return self._request('GET',
                             Ndex3.WORKSPACES_ROUTE + '/' +
                             str(workspace_id))

    def update_workspace(self, workspace_id, name=None, options=None,
                         network_ids=None):
        """
        Replaces the contents of a workspace.

        Corresponds to ``PUT /v3/workspaces/{workspaceid}``. To change
        only the name or only the network list use
        :py:meth:`rename_workspace` or
        :py:meth:`update_workspace_networks`.

        :param workspace_id: UUID of the workspace
        :type workspace_id: str
        :param name: New name
        :type name: str
        :param options: New options
        :type options: dict
        :param network_ids: New list of network UUIDs
        :type network_ids: list
        :raises NDExInvalidParameterError: If no field to update is
                                           given
        :raises NDExNotFoundError: If no such workspace exists
        :raises NDExUnauthorizedError: If write access is denied
        :return: Update status containing ``uuid`` and
                 ``modificationTime``
        :rtype: dict
        """
        self._require_auth()
        self._require_str(workspace_id, 'workspace_id')
        body = {}
        if name is not None:
            body['name'] = self._require_str(name, 'name')
        if options is not None:
            body['options'] = options
        if network_ids is not None:
            body['networkIDs'] = self._require_id_list(network_ids,
                                                       'network_ids')
        if len(body) == 0:
            raise NDExInvalidParameterError('At least one of name, options '
                                            'or network_ids must be set')
        return self._request('PUT',
                             Ndex3.WORKSPACES_ROUTE + '/' +
                             str(workspace_id), json_body=body)

    def rename_workspace(self, workspace_id, name):
        """
        Renames a workspace.

        Corresponds to ``PUT /v3/workspaces/{workspaceid}/name``.

        :param workspace_id: UUID of the workspace
        :type workspace_id: str
        :param name: New name
        :type name: str
        :raises NDExInvalidParameterError: For invalid parameters
        :raises NDExNotFoundError: If no such workspace exists
        :raises NDExUnauthorizedError: If write access is denied
        :return: ``None``
        """
        self._require_auth()
        self._require_str(workspace_id, 'workspace_id')
        self._require_str(name, 'name')
        return self._request('PUT',
                             Ndex3.WORKSPACES_ROUTE + '/' +
                             str(workspace_id) + '/name',
                             json_body={'name': name})

    def update_workspace_networks(self, workspace_id, network_ids):
        """
        Replaces the network list of a workspace.

        Corresponds to ``PUT
        /v3/workspaces/{workspaceid}/networkids``.

        :param workspace_id: UUID of the workspace
        :type workspace_id: str
        :param network_ids: UUIDs of the networks
        :type network_ids: list
        :raises NDExInvalidParameterError: For invalid parameters
        :raises NDExNotFoundError: If no such workspace exists
        :raises NDExUnauthorizedError: If write access is denied
        :return: ``None``
        """
        self._require_auth()
        self._require_str(workspace_id, 'workspace_id')
        return self._request('PUT',
                             Ndex3.WORKSPACES_ROUTE + '/' +
                             str(workspace_id) + '/networkids',
                             json_body=self._require_id_list(network_ids,
                                                             'network_ids'))

    def delete_workspace(self, workspace_id):
        """
        Deletes a workspace. Networks in the workspace are untouched.

        Corresponds to ``DELETE /v3/workspaces/{workspaceid}``.

        :param workspace_id: UUID of the workspace
        :type workspace_id: str
        :raises NDExNotFoundError: If no such workspace exists
        :raises NDExUnauthorizedError: If delete access is denied
        :return: ``None``
        """
        self._require_auth()
        self._require_str(workspace_id, 'workspace_id')
        return self._request('DELETE',
                             Ndex3.WORKSPACES_ROUTE + '/' +
                             str(workspace_id))

    # ------------------------------------------------------------------
    # v3 network queries
    #
    # The v2 routes /v2/search/network/{id}/... were renamed to
    # /v3/search/networks/{id}/... and now return CX2 rather than CX.
    # ------------------------------------------------------------------

    def query_network_as_cx2_stream(self, network_id, search_string,
                                    search_depth=1, edge_limit=2500,
                                    error_when_limit=True, direct_only=False,
                                    node_ids=None, aspects=None,
                                    access_key=None, save=False,
                                    preserve_coordinates=False):
        """
        Runs a neighborhood query and returns the result as CX2.

        Corresponds to ``POST /v3/search/networks/{networkId}/query``.
        This replaces
        :py:meth:`~ndex2.client.Ndex2.get_neighborhood_as_cx_stream`,
        which targeted the v2 route and returned CX.

        :param network_id: UUID of the network to query
        :type network_id: str
        :param search_string: Query terms identifying the starting nodes
        :type search_string: str
        :param search_depth: Number of hops to traverse
        :type search_depth: int
        :param edge_limit: Maximum edges to return. ``0`` means no limit.
        :type edge_limit: int
        :param error_when_limit: If ``True`` the server raises an error
                                 rather than truncating when
                                 *edge_limit* is exceeded
        :type error_when_limit: bool
        :param direct_only: If ``True`` return only directly connected
                            neighbors
        :type direct_only: bool
        :param node_ids: Start from these node ids instead of running
                         *search_string*
        :type node_ids: list
        :param aspects: Restrict the result to these CX2 aspects
        :type aspects: list
        :param access_key: Access key granting read access
        :type access_key: str
        :param save: If ``True`` save the result as a new network
        :type save: bool
        :param preserve_coordinates: If ``True`` keep node coordinates
                                     from the source network
        :type preserve_coordinates: bool
        :raises NDExInvalidParameterError: For invalid parameters
        :raises NDExNotFoundError: If no such network exists
        :return: Streamed response whose body is the CX2 result
        :rtype: :py:class:`requests.Response`
        """
        self._require_str(network_id, 'network_id')
        body = {'searchString': search_string,
                'searchDepth': search_depth,
                'edgeLimit': edge_limit,
                'errorWhenLimitIsOver': bool(error_when_limit),
                'directOnly': bool(direct_only)}
        if node_ids is not None:
            body['nodeIds'] = list(node_ids)
        if aspects is not None:
            body['aspects'] = list(aspects)
        return self._request('POST',
                             Ndex3.SEARCH_ROUTE + '/networks/' +
                             str(network_id) + '/query',
                             params={'accesskey': access_key,
                                     'save': str(bool(save)).lower(),
                                     'preserveCoordinates':
                                     str(bool(preserve_coordinates)).lower()},
                             json_body=body, stream=True)

    def interconnect_query_as_cx2_stream(self, network_id, search_string,
                                         search_depth=1, edge_limit=2500,
                                         error_when_limit=True,
                                         direct_only=False, node_ids=None,
                                         aspects=None, access_key=None,
                                         save=False,
                                         preserve_coordinates=False):
        """
        Runs an interconnect query and returns the result as CX2.

        Corresponds to ``POST
        /v3/search/networks/{networkId}/interconnectquery``. This
        replaces
        :py:meth:`~ndex2.client.Ndex2.get_interconnectquery_as_cx_stream`.

        Arguments match :py:meth:`query_network_as_cx2_stream`.

        :param network_id: UUID of the network to query
        :type network_id: str
        :param search_string: Query terms identifying the nodes to
                              interconnect
        :type search_string: str
        :param search_depth: Number of hops to traverse
        :type search_depth: int
        :param edge_limit: Maximum edges to return
        :type edge_limit: int
        :param error_when_limit: If ``True`` error rather than truncate
        :type error_when_limit: bool
        :param direct_only: If ``True`` return only direct connections
        :type direct_only: bool
        :param node_ids: Start from these node ids
        :type node_ids: list
        :param aspects: Restrict the result to these CX2 aspects
        :type aspects: list
        :param access_key: Access key granting read access
        :type access_key: str
        :param save: If ``True`` save the result as a new network
        :type save: bool
        :param preserve_coordinates: If ``True`` keep node coordinates
        :type preserve_coordinates: bool
        :raises NDExInvalidParameterError: For invalid parameters
        :raises NDExNotFoundError: If no such network exists
        :return: Streamed response whose body is the CX2 result
        :rtype: :py:class:`requests.Response`
        """
        self._require_str(network_id, 'network_id')
        body = {'searchString': search_string,
                'searchDepth': search_depth,
                'edgeLimit': edge_limit,
                'errorWhenLimitIsOver': bool(error_when_limit),
                'directOnly': bool(direct_only)}
        if node_ids is not None:
            body['nodeIds'] = list(node_ids)
        if aspects is not None:
            body['aspects'] = list(aspects)
        return self._request('POST',
                             Ndex3.SEARCH_ROUTE + '/networks/' +
                             str(network_id) + '/interconnectquery',
                             params={'accesskey': access_key,
                                     'save': str(bool(save)).lower(),
                                     'preserveCoordinates':
                                     str(bool(preserve_coordinates)).lower()},
                             json_body=body, stream=True)

    def get_node_attributes(self, network_id, node_ids=None,
                            attribute_names=None, access_key=None):
        """
        Retrieves selected node attributes from a network.

        Corresponds to ``POST /v3/search/networks/{networkId}/nodes``.
        This replaces
        :py:meth:`~ndex2.client.Ndex2.search_network_nodes`, which
        targeted the v2 route.

        :param network_id: UUID of the network
        :type network_id: str
        :param node_ids: Restrict the result to these node ids. Omit for
                         all nodes.
        :type node_ids: list
        :param attribute_names: Restrict the result to these attribute
                                names. Omit for all attributes.
        :type attribute_names: list
        :param access_key: Access key granting read access
        :type access_key: str
        :raises NDExInvalidParameterError: For invalid parameters
        :raises NDExNotFoundError: If no such network exists
        :return: Streamed response whose body holds the node attributes
        :rtype: :py:class:`requests.Response`
        """
        self._require_str(network_id, 'network_id')
        body = {}
        if node_ids is not None:
            body['ids'] = list(node_ids)
        if attribute_names is not None:
            body['attributeNames'] = list(attribute_names)
        return self._request('POST',
                             Ndex3.SEARCH_ROUTE + '/networks/' +
                             str(network_id) + '/nodes',
                             params={'accesskey': access_key},
                             json_body=body, stream=True)

    def save_new_cx2_network(self, cx, visibility=None, return_url=False):
        """
        Creates a network from a CX2 object.

        Overrides :py:meth:`~ndex2.client.Ndex2.save_new_cx2_network` so
        that the return value is consistent with the rest of this class.
        The inherited version always returns the full URL of the new
        network; this returns its UUID unless *return_url* is ``True``.

        :param cx: CX2 network as a list of aspect dicts
        :type cx: list
        :param visibility: ``PUBLIC`` or ``PRIVATE``
        :type visibility: str
        :param return_url: If ``True`` return the full URL rather than
                           the UUID
        :type return_url: bool
        :raises NDExInvalidParameterError: If *cx* is not a list
        :raises NDExUnauthorizedError: If not authenticated
        :return: UUID of the new network, or its full URL when
                 *return_url* is ``True``
        :rtype: str
        """
        return self.save_new_cx2_network_in_folder(cx, visibility=visibility,
                                                   return_url=return_url)

    def save_cx2_stream_as_new_network(self, cx_stream, visibility=None,
                                       return_url=False):
        """
        Creates a network from a CX2 byte stream.

        Overrides
        :py:meth:`~ndex2.client.Ndex2.save_cx2_stream_as_new_network` to
        return a UUID by default, matching the rest of this class. The
        upload itself is unchanged and still streams as multipart, which
        is the reason to prefer this over
        :py:meth:`save_new_cx2_network` for large networks.

        :param cx_stream: File-like object holding CX2 bytes
        :param visibility: ``PUBLIC`` or ``PRIVATE``
        :type visibility: str
        :param return_url: If ``True`` return the full URL rather than
                           the UUID
        :type return_url: bool
        :raises NDExUnauthorizedError: If not authenticated
        :raises NDExError: If the server does not report the location of
                           the new network
        :return: UUID of the new network, or its full URL when
                 *return_url* is ``True``
        :rtype: str
        """
        url = super(Ndex3, self).save_cx2_stream_as_new_network(
            cx_stream, visibility=visibility)
        if return_url is True:
            return url
        return self._uuid_from_url(url)

    # ------------------------------------------------------------------
    # v2 methods remapped onto v3 endpoints
    # ------------------------------------------------------------------

    def make_network_public(self, network_id):
        """
        Sets the visibility of a network to ``PUBLIC``.

        Reimplemented on top of ``POST
        /v3/batch/files/setvisibility``. The v2 implementation used
        ``/network/{id}/systemproperty``, which does not exist in v3.

        :param network_id: UUID of the network
        :type network_id: str
        :raises NDExInvalidParameterError: For an invalid *network_id*
        :raises NDExUnauthorizedError: If write access is denied
        :return: ``None``
        """
        self._require_str(network_id, 'network_id')
        return self.set_file_visibility(Visibility.PUBLIC, [str(network_id)],
                                        default_type=FileType.NETWORK)

    def make_network_private(self, network_id):
        """
        Sets the visibility of a network to ``PRIVATE``.

        Reimplemented on top of ``POST
        /v3/batch/files/setvisibility``.

        :param network_id: UUID of the network
        :type network_id: str
        :raises NDExInvalidParameterError: For an invalid *network_id*
        :raises NDExUnauthorizedError: If write access is denied
        :return: ``None``
        """
        self._require_str(network_id, 'network_id')
        return self.set_file_visibility(Visibility.PRIVATE, [str(network_id)],
                                        default_type=FileType.NETWORK)

    def update_network_user_permission(self, userid, networkid, permission):
        """
        Grants a user a permission on a network.

        Reimplemented on top of ``POST /v3/files/sharing/members``. The
        v2 implementation used ``/network/{id}/permission``, which does
        not exist in v3.

        :param userid: UUID of the user
        :type userid: str
        :param networkid: UUID of the network
        :type networkid: str
        :param permission: One of :py:class:`Permissions`
        :type permission: str
        :raises NDExInvalidParameterError: For invalid parameters
        :raises NDExUnauthorizedError: If not authorized to share
        :return: Server response describing the resulting permissions
        :rtype: dict
        """
        self._require_str(str(networkid), 'networkid')
        self._require_str(str(userid), 'userid')
        return self.set_sharing_members({str(networkid): FileType.NETWORK},
                                        {str(userid): permission})

    def grant_networks_to_user(self, userid, networkids, permission='READ'):
        """
        Grants a user the same permission on several networks.

        Reimplemented on top of ``POST /v3/files/sharing/members``.
        Unlike the v2 version, which issued one request per network,
        this sends a single batched request.

        :param userid: UUID of the user
        :type userid: str
        :param networkids: UUIDs of the networks
        :type networkids: list
        :param permission: One of :py:class:`Permissions`
        :type permission: str
        :raises NDExInvalidParameterError: For invalid parameters
        :raises NDExUnauthorizedError: If not authorized to share
        :return: Server response describing the resulting permissions
        :rtype: dict
        """
        self._require_str(str(userid), 'userid')
        return self.set_sharing_members(
            self._require_id_list(networkids, 'networkids'),
            {str(userid): permission}, default_type=FileType.NETWORK)

    def grant_network_to_user_by_username(self, username, network_id,
                                          permission):
        """
        Grants a permission on a network to a user named by account
        name.

        Looks the user up with :py:meth:`get_user_by_username` and then
        calls :py:meth:`update_network_user_permission`.

        :param username: Account name of the user
        :type username: str
        :param network_id: UUID of the network
        :type network_id: str
        :param permission: One of :py:class:`Permissions`
        :type permission: str
        :raises NDExInvalidParameterError: For invalid parameters
        :raises NDExNotFoundError: If no such user exists
        :raises NDExUnauthorizedError: If not authorized to share
        :return: Server response describing the resulting permissions
        :rtype: dict
        """
        user = self.get_user_by_username(username)
        if not isinstance(user, dict) or user.get('externalId') is None:
            raise NDExError('Server did not return an externalId for user ' +
                            str(username))
        return self.update_network_user_permission(user['externalId'],
                                                   network_id, permission)

    # ------------------------------------------------------------------
    # removed in v3
    # ------------------------------------------------------------------

    @staticmethod
    def _removed(name, replacement):
        """
        Raises the error used by every removed v2 method.

        :param name: Name of the removed method
        :type name: str
        :param replacement: Guidance naming the v3 equivalent
        :type replacement: str
        :raises NDExUnsupportedCallError: always
        """
        raise NDExUnsupportedCallError(
            name + ' is not supported by the NDEx v3 API. ' + replacement)

    def create_networkset(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('create_networkset', 'Use create_folder instead.')

    def get_networkset(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('get_networkset', 'Use get_folder and '
                                         'list_folder_items instead.')

    def get_network_set(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('get_network_set', 'Use get_folder and '
                                          'list_folder_items instead.')

    def get_networksets_for_user_id(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('get_networksets_for_user_id',
                       'Use list_folders, or get_user_home to walk the '
                       'folder tree from its root.')

    def delete_networkset(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('delete_networkset', 'Use delete_folder instead.')

    def add_networks_to_networkset(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('add_networks_to_networkset',
                       'Use move_networks_to_folder, or create_shortcut to '
                       'list a network in more than one folder.')

    def delete_networks_from_networkset(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('delete_networks_from_networkset',
                       'Use move_networks_to_folder to move the networks '
                       'elsewhere, or delete_shortcut.')

    def update_network_group_permission(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('update_network_group_permission',
                       'Groups were removed in v3. Use set_sharing_members '
                       'to grant per user permissions.')

    def grant_networks_to_group(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('grant_networks_to_group',
                       'Groups were removed in v3. Use set_sharing_members '
                       'to grant per user permissions.')

    def search_networks(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('search_networks', 'Use search_files instead.')

    def find_networks(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('find_networks', 'Use search_files instead.')

    def get_neighborhood_as_cx_stream(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('get_neighborhood_as_cx_stream',
                       'The v2 route /search/network/{id}/query became '
                       '/v3/search/networks/{id}/query and returns CX2. Use '
                       'query_network_as_cx2_stream instead.')

    def get_neighborhood(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('get_neighborhood',
                       'v3 serves CX2 only, so the result cannot be parsed '
                       'into a NiceCXNetwork. Use query_network_as_cx2_stream '
                       'instead.')

    def get_interconnectquery_as_cx_stream(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('get_interconnectquery_as_cx_stream',
                       'The v2 route became '
                       '/v3/search/networks/{id}/interconnectquery and '
                       'returns CX2. Use interconnect_query_as_cx2_stream '
                       'instead.')

    def get_interconnectquery(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('get_interconnectquery',
                       'v3 serves CX2 only, so the result cannot be parsed '
                       'into a NiceCXNetwork. Use '
                       'interconnect_query_as_cx2_stream instead.')

    def search_network_nodes(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('search_network_nodes',
                       'The v2 route became /v3/search/networks/{id}/nodes. '
                       'Use get_node_attributes instead.')

    def get_network_as_cx_stream(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('get_network_as_cx_stream',
                       'v3 serves CX2 only. Use get_network_as_cx2_stream '
                       'instead.')

    def get_network_aspect_as_cx_stream(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('get_network_aspect_as_cx_stream',
                       'v3 serves CX2 only. Use '
                       'get_network_aspect_as_cx2_stream instead.')

    def save_cx_stream_as_new_network(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('save_cx_stream_as_new_network',
                       'v3 accepts CX2 only. Use '
                       'save_cx2_stream_as_new_network, or '
                       'save_new_cx2_network_in_folder to place the network '
                       'in a folder.')

    def save_new_network(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('save_new_network',
                       'v3 accepts CX2 only. Use save_new_cx2_network, or '
                       'save_new_cx2_network_in_folder to place the network '
                       'in a folder.')

    def update_cx_network(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('update_cx_network',
                       'v3 accepts CX2 only. Use update_cx2_network instead. ')

    def get_provenance(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('get_provenance',
                       'The provenance aspect was dropped in v3 and has no '
                       'replacement endpoint.')

    def set_provenance(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('set_provenance',
                       'The provenance aspect was dropped in v3 and has no '
                       'replacement endpoint.')

    def get_sample_network(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('get_sample_network',
                       'v3 exposes no sample network endpoint. The summary '
                       'returned by get_network_summary reports hasSample but '
                       'the sample itself cannot be fetched.')

    def set_network_sample(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('set_network_sample',
                       'v3 exposes no sample network endpoint. ')

    def get_task_by_id(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('get_task_by_id',
                       'v3 exposes no task service; there is no /v3/task '
                       'endpoint.')

    def set_read_only(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('set_read_only',
                       'v3 exposes no system property endpoint. Read-only '
                       'status is reported by get_network_summary but cannot '
                       'be set through the v3 API.')

    def set_network_system_properties(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('set_network_system_properties',
                       'v3 exposes no system property endpoint. For '
                       'visibility use set_file_visibility, '
                       'make_network_public or make_network_private; '
                       'showcase, index_level and readOnly have no v3 '
                       'equivalent.')

    def set_network_properties(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('set_network_properties',
                       'v3 updates a network by replacing its CX2 content. '
                       'Use update_cx2_network instead.')

    def update_network_profile(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('update_network_profile',
                       'v3 has no profile endpoint; a network is updated by '
                       'replacing its CX2 content. Use update_cx2_network '
                       'instead.')

    def get_user_by_id(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('get_user_by_id',
                       'v3 looks users up by account name. Use '
                       'get_user_by_username, or get_user_home if you only '
                       'need the user content listing.')

    def get_user_network_summaries(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('get_user_network_summaries',
                       'Use get_user_home to list the root of a user home '
                       'directory, list_folder_items to walk into folders, or '
                       'search_files with account_name set.')

    def get_network_summaries_for_user(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('get_network_summaries_for_user',
                       'Use get_user_home, or search_files with account_name '
                       'set.')

    def get_network_ids_for_user(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('get_network_ids_for_user',
                       'Use get_user_home or search_files with account_name '
                       'set, then read the uuid field of each returned item.')

    def search_networks_by_property_filter(self, *args, **kwargs):
        """
        Not supported in v3.

        :raises NDExUnsupportedCallError: always
        """
        Ndex3._removed('search_networks_by_property_filter',
                       'Use search_files instead.')
