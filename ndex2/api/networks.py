# -*- coding: utf-8 -*-

"""
The ``networks`` namespace, reached as ``client.networks``.

Network operations served by ``/v3``. Creation is deliberately absent:
:py:meth:`~ndex2.client.Ndex2.save_new_cx2_network` and
:py:meth:`~ndex2.client.Ndex2.save_cx2_stream_as_new_network` already
target ``/v3`` and accept a ``folder_id``, so duplicating them here would
give two creation paths for no benefit.

Several methods here overlap a flat method on
:py:class:`~ndex2.client.Ndex2` where the v3 endpoint offers more than its
v2 counterpart. Both remain available; each docstring notes what the v3
version adds.

.. versionadded:: 3.12.0
"""

from ndex2.api._validators import require_id
from ndex2.api._validators import require_id_list
from ndex2.api._validators import require_str

NETWORKS = '/networks'
BATCH_NETWORKS = '/batch/networks'
SEARCH_NETWORKS = '/search/networks'
SHARING_TRANSFER = '/files/sharing/transfer'


class NetworksAPI(object):
    """
    Network summaries, aspects, queries, export and ownership.

    Not instantiated directly. Reached as ``client.networks`` on
    :py:class:`~ndex2.client.Ndex2`.

    .. versionadded:: 3.12.0

    :param http: Shared transport, supplied by the client
    :type http: :py:class:`~ndex2.transport.HttpTransport`
    """

    def __init__(self, http):
        self._http = http

    # ------------------------------------------------------------------
    # summaries and aspects
    # ------------------------------------------------------------------

    def get_summary(self, network_id, access_key=None, format='FULL'):
        """
        Retrieves the summary of a network.

        ``GET /v3/networks/{networkid}/summary``

        The summary includes a ``folderId`` field naming the folder holding
        the network. Field names and types follow the v3
        ``NetworkSummaryV3`` model, which differs in places from what the
        flat :py:meth:`~ndex2.client.Ndex2.get_network_summary` returns.

        .. versionadded:: 3.12.0

        :param network_id: UUID of the network
        :type network_id: str
        :param access_key: Access key granting read access
        :type access_key: str
        :param format: ``FULL`` or ``COMPACT``
        :type format: str
        :raises NDExInvalidParameterError: For an invalid *network_id*
        :raises NDExNotFoundError: If no such network exists
        :raises NDExUnauthorizedError: If read access is denied
        :return: Network summary, including ``folderId``
        :rtype: dict
        """
        require_str(network_id, 'network_id')
        return self._http.get(NETWORKS + '/' + str(network_id) + '/summary',
                              params={'accesskey': access_key,
                                      'format': format})

    def get_summaries(self, network_ids, access_key=None, format='FULL'):
        """
        Retrieves summaries for many networks in one request.

        ``POST /v3/batch/networks/summary``

        .. versionadded:: 3.12.0

        :param network_ids: UUIDs of the networks
        :type network_ids: list or str
        :param access_key: Access key granting read access
        :type access_key: str
        :param format: ``FULL`` or ``COMPACT``
        :type format: str
        :raises NDExInvalidParameterError: If *network_ids* is empty
        :raises NDExUnauthorizedError: If read access is denied
        :return: Network summaries
        :rtype: list
        """
        body = require_id_list(network_ids, 'network_ids')
        result = self._http.post(BATCH_NETWORKS + '/summary',
                                 params={'accesskey': access_key,
                                         'format': format},
                                 json_body=body)
        return [] if result is None else result

    def list_aspects(self, network_id, access_key=None):
        """
        Lists the CX2 aspect metadata of a network.

        ``GET /v3/networks/{networkid}/aspects``

        .. versionadded:: 3.12.0

        :param network_id: UUID of the network
        :type network_id: str
        :param access_key: Access key granting read access
        :type access_key: str
        :raises NDExNotFoundError: If no such network exists
        :return: Aspect metadata entries
        :rtype: list
        """
        require_str(network_id, 'network_id')
        result = self._http.get(NETWORKS + '/' + str(network_id) + '/aspects',
                                params={'accesskey': access_key})
        return [] if result is None else result

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------

    def delete(self, network_id, permanent=False):
        """
        Deletes a network.

        ``DELETE /v3/networks/{networkid}``

        Unlike the flat :py:meth:`~ndex2.client.Ndex2.delete_network`, this
        moves the network to the trash by default, from where
        ``client.files.restore()`` can recover it. Pass *permanent* to
        match the flat method's behaviour.

        .. versionadded:: 3.12.0

        :param network_id: UUID of the network
        :type network_id: str
        :param permanent: If ``True``, bypass the trash and delete
                          irrecoverably
        :type permanent: bool
        :raises NDExNotFoundError: If no such network exists
        :raises NDExUnauthorizedError: If delete access is denied
        :return: ``None``
        """
        self._http.require_auth()
        require_str(network_id, 'network_id')
        return self._http.delete(
            NETWORKS + '/' + str(network_id),
            params={'permanent': str(bool(permanent)).lower()})

    def move_to_folder(self, folder_id, network_ids):
        """
        Moves networks into a folder.

        ``POST /v3/batch/networks/move``

        A network lives in exactly one folder, so this moves rather than
        adds. To have a network appear in more than one place, use
        ``client.files.create_shortcut()``.

        .. versionadded:: 3.12.0

        :param folder_id: UUID of the destination folder
        :type folder_id: str
        :param network_ids: UUIDs of the networks to move
        :type network_ids: list or str
        :raises NDExInvalidParameterError: For invalid arguments
        :raises NDExUnauthorizedError: If write access to the folder or a
                                       network is denied
        :return: ``None``
        """
        self._http.require_auth()
        require_id(folder_id, 'folder_id')
        body = {'targetFolder': str(folder_id),
                'networks': require_id_list(network_ids, 'network_ids')}
        return self._http.post(BATCH_NETWORKS + '/move', json_body=body)

    def transfer_ownership(self, network_ids, new_owner):
        """
        Transfers ownership of networks to another user.

        ``POST /v3/files/sharing/transfer``

        .. versionadded:: 3.12.0

        :param network_ids: UUIDs of the networks to transfer
        :type network_ids: list or str
        :param new_owner: UUID of the user receiving ownership
        :type new_owner: str
        :raises NDExInvalidParameterError: For invalid arguments
        :raises NDExUnauthorizedError: If the caller is not the owner
        :return: ``None``
        """
        self._http.require_auth()
        require_id(new_owner, 'new_owner')
        body = {'networks': require_id_list(network_ids, 'network_ids'),
                'new_owner': str(new_owner)}
        return self._http.post(SHARING_TRANSFER, json_body=body)

    # ------------------------------------------------------------------
    # export and DOI
    # ------------------------------------------------------------------

    def export_as_tsv(self, network_id, type='node', include_header=True,
                      list_delimiter=',', node_key='id', access_key=None):
        """
        Exports a network as tab separated text.

        ``GET /v3/networks/{networkid}/export``

        The response is streamed, so the body is available as
        ``.text`` or ``.content`` on the returned object rather than being
        parsed.

        .. versionadded:: 3.12.0

        :param network_id: UUID of the network
        :type network_id: str
        :param type: ``node`` or ``edge``
        :type type: str
        :param include_header: If ``True``, emit a header row
        :type include_header: bool
        :param list_delimiter: Separator used inside list-valued
                               attributes
        :type list_delimiter: str
        :param node_key: Node attribute identifying nodes in edge rows
        :type node_key: str
        :param access_key: Access key granting read access
        :type access_key: str
        :raises NDExNotFoundError: If no such network exists
        :return: Streamed response whose body is the TSV text
        :rtype: :py:class:`requests.Response`
        """
        require_str(network_id, 'network_id')
        return self._http.get(
            NETWORKS + '/' + str(network_id) + '/export',
            params={'accesskey': access_key,
                    'type': type,
                    'header': str(bool(include_header)).lower(),
                    'listdelimiter': list_delimiter,
                    'nodekey': node_key},
            stream=True)

    def mint_doi(self, network_id, key, email):
        """
        Requests a DOI for a network.

        ``GET /v3/networks/{networkid}/DOI``

        .. versionadded:: 3.12.0

        :param network_id: UUID of the network
        :type network_id: str
        :param key: Encrypted key issued by the server authorizing the
                    request
        :type key: str
        :param email: Email address of the submitter
        :type email: str
        :raises NDExInvalidParameterError: For invalid arguments
        :raises NDExUnauthorizedError: If the key is not valid for the
                                       network
        :return: Server response describing the request
        :rtype: str
        """
        require_str(network_id, 'network_id')
        require_str(key, 'key')
        require_str(email, 'email')
        return self._http.get(NETWORKS + '/' + str(network_id) + '/DOI',
                              params={'key': key, 'email': email})

    # ------------------------------------------------------------------
    # queries
    #
    # The v2 routes /v2/search/network/{id}/... were renamed to
    # /v3/search/networks/{id}/... and now return CX2 rather than CX. The
    # flat CX methods on Ndex2 still target the v2 routes, so both remain
    # usable side by side.
    # ------------------------------------------------------------------

    def _query(self, network_id, route, search_string, search_depth,
               edge_limit, error_when_limit, direct_only, node_ids, aspects,
               access_key, save, preserve_coordinates):
        """
        Builds and sends a path query.

        Shared by :py:meth:`query` and :py:meth:`interconnect_query`, which
        differ only in *route*. Every argument other than *route* is
        documented on those two methods and passed through unchanged.

        :param network_id: UUID of the network to query
        :type network_id: str
        :param route: Query route appended below the network id, either
                      ``/query`` or ``/interconnectquery``
        :type route: str
        :return: Streamed response whose body is the CX2 result
        :rtype: :py:class:`requests.Response`
        """
        require_str(network_id, 'network_id')
        body = {'searchString': search_string,
                'searchDepth': search_depth,
                'edgeLimit': edge_limit,
                'errorWhenLimitIsOver': bool(error_when_limit),
                'directOnly': bool(direct_only)}
        if node_ids is not None:
            body['nodeIds'] = list(node_ids)
        if aspects is not None:
            body['aspects'] = list(aspects)
        return self._http.post(
            SEARCH_NETWORKS + '/' + str(network_id) + route,
            params={'accesskey': access_key,
                    'save': str(bool(save)).lower(),
                    'preserveCoordinates':
                        str(bool(preserve_coordinates)).lower()},
            json_body=body, stream=True)

    def query(self, network_id, search_string, search_depth=1,
              edge_limit=2500, error_when_limit=True, direct_only=False,
              node_ids=None, aspects=None, access_key=None, save=False,
              preserve_coordinates=False):
        """
        Runs a neighborhood query and returns the result as CX2.

        ``POST /v3/search/networks/{networkid}/query``

        The CX equivalent is the flat
        :py:meth:`~ndex2.client.Ndex2.get_neighborhood_as_cx_stream`, which
        targets the v2 route.

        .. versionadded:: 3.12.0

        :param network_id: UUID of the network to query
        :type network_id: str
        :param search_string: Query terms identifying the starting nodes
        :type search_string: str
        :param search_depth: Number of hops to traverse
        :type search_depth: int
        :param edge_limit: Maximum edges to return. ``0`` means no limit.
        :type edge_limit: int
        :param error_when_limit: If ``True``, the server raises an error
                                 rather than truncating when *edge_limit*
                                 is exceeded
        :type error_when_limit: bool
        :param direct_only: If ``True``, return only directly connected
                            neighbors
        :type direct_only: bool
        :param node_ids: Start from these node ids instead of running
                         *search_string*
        :type node_ids: list
        :param aspects: Restrict the result to these CX2 aspects
        :type aspects: list
        :param access_key: Access key granting read access
        :type access_key: str
        :param save: If ``True``, save the result as a new network
        :type save: bool
        :param preserve_coordinates: If ``True``, keep node coordinates
                                     from the source network
        :type preserve_coordinates: bool
        :raises NDExInvalidParameterError: For invalid arguments
        :raises NDExNotFoundError: If no such network exists
        :return: Streamed response whose body is the CX2 result
        :rtype: :py:class:`requests.Response`
        """
        return self._query(network_id, '/query', search_string, search_depth,
                           edge_limit, error_when_limit, direct_only,
                           node_ids, aspects, access_key, save,
                           preserve_coordinates)

    def interconnect_query(self, network_id, search_string, search_depth=1,
                           edge_limit=2500, error_when_limit=True,
                           direct_only=False, node_ids=None, aspects=None,
                           access_key=None, save=False,
                           preserve_coordinates=False):
        """
        Runs an interconnect query and returns the result as CX2.

        ``POST /v3/search/networks/{networkid}/interconnectquery``

        Arguments match :py:meth:`query`. The CX equivalent is the flat
        :py:meth:`~ndex2.client.Ndex2.get_interconnectquery_as_cx_stream`.

        .. versionadded:: 3.12.0

        :param network_id: UUID of the network to query
        :type network_id: str
        :param search_string: Query terms identifying the nodes to
                              interconnect
        :type search_string: str
        :param search_depth: Number of hops to traverse
        :type search_depth: int
        :param edge_limit: Maximum edges to return
        :type edge_limit: int
        :param error_when_limit: If ``True``, error rather than truncate
        :type error_when_limit: bool
        :param direct_only: If ``True``, return only direct connections
        :type direct_only: bool
        :param node_ids: Start from these node ids
        :type node_ids: list
        :param aspects: Restrict the result to these CX2 aspects
        :type aspects: list
        :param access_key: Access key granting read access
        :type access_key: str
        :param save: If ``True``, save the result as a new network
        :type save: bool
        :param preserve_coordinates: If ``True``, keep node coordinates
        :type preserve_coordinates: bool
        :raises NDExInvalidParameterError: For invalid arguments
        :raises NDExNotFoundError: If no such network exists
        :return: Streamed response whose body is the CX2 result
        :rtype: :py:class:`requests.Response`
        """
        return self._query(network_id, '/interconnectquery', search_string,
                           search_depth, edge_limit, error_when_limit,
                           direct_only, node_ids, aspects, access_key, save,
                           preserve_coordinates)

    def get_node_attributes(self, network_id, node_ids=None,
                            attribute_names=None, access_key=None):
        """
        Retrieves selected node attributes from a network.

        ``POST /v3/search/networks/{networkid}/nodes``

        Replaces the flat
        ``Ndex2.search_network_nodes()``, which targets
        the v2 route.

        .. versionadded:: 3.12.0

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
        :raises NDExInvalidParameterError: For an invalid *network_id*
        :raises NDExNotFoundError: If no such network exists
        :return: Streamed response whose body holds the node attributes
        :rtype: :py:class:`requests.Response`
        """
        require_str(network_id, 'network_id')
        body = {}
        if node_ids is not None:
            body['ids'] = list(node_ids)
        if attribute_names is not None:
            body['attributeNames'] = list(attribute_names)
        return self._http.post(
            SEARCH_NETWORKS + '/' + str(network_id) + '/nodes',
            params={'accesskey': access_key}, json_body=body, stream=True)
