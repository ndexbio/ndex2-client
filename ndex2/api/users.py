# -*- coding: utf-8 -*-

"""
The ``users`` namespace, reached as ``client.users``.

Served by ``/v3``. The v3 API looks users up by account name rather than
by UUID; the flat :py:meth:`~ndex2.client.Ndex2.get_user_by_id` remains
available for lookup by id.

.. versionadded:: 3.12.0
"""

from ndex2.api._validators import require_id
from ndex2.api._validators import require_str

USERS = '/users'


class UsersAPI(object):
    """
    User lookup, home directory listing and token sign-in.

    Not instantiated directly. Reached as ``client.users`` on
    :py:class:`~ndex2.client.Ndex2`.

    :param http: Shared transport, supplied by the client
    :type http: :py:class:`~ndex2.transport.HttpTransport`
    """

    def __init__(self, http):
        self._http = http

    def get(self, username):
        """
        Retrieves a user by account name.

        ``GET /v3/users?username=``

        :param username: Account name of the user
        :type username: str
        :raises NDExInvalidParameterError: For an invalid *username*
        :raises NDExNotFoundError: If no such user exists
        :return: User record, including ``externalId``
        :rtype: dict
        """
        require_str(username, 'username')
        return self._http.get(USERS, params={'username': username})

    def home(self, user_id, format='update'):
        """
        Lists the contents of a user's home directory.

        ``GET /v3/users/{userid}/home``

        This is the entry point for walking a user's folder tree: it
        returns the items that have no parent folder. Anonymous callers
        see only public items.

        :param user_id: UUID of the user
        :type user_id: str
        :param format: ``update`` for full item summaries, ``compact`` for
                       reduced ones
        :type format: str
        :raises NDExInvalidParameterError: For an invalid *user_id*
        :raises NDExNotFoundError: If no such user exists
        :return: File item summaries at the root of the user's home
        :rtype: list
        """
        require_id(user_id, 'user_id')
        result = self._http.get(USERS + '/' + str(user_id) + '/home',
                                params={'format': format})
        return [] if result is None else result

    def signin(self, id_token):
        """
        Signs in with an OAuth/Keycloak id token and returns the user.

        ``POST /v3/users/signin``

        On success the token is retained on the shared transport and sent
        as a bearer token on subsequent requests. Because the transport
        shares its session with the flat methods, this re-authenticates
        the whole client, replacing any username and password previously
        set.

        :param id_token: OAuth/Keycloak id token
        :type id_token: str
        :raises NDExInvalidParameterError: For an invalid *id_token*
        :raises NDExUnauthorizedError: If the token is rejected
        :return: User record for the signed-in account
        :rtype: dict
        """
        require_str(id_token, 'id_token')
        user = self._http.post(USERS + '/signin',
                               json_body={'id_token': id_token})
        self._http.set_auth(bearer_token=id_token)
        return user
