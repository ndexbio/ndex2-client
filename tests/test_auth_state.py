#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests that authentication state is read from one place.

The session is what actually carries credentials to the server. Anything
that decides whether a call is authenticated has to read the session; a
second copy of the credentials held elsewhere can disagree with it, and
the call is then refused client side even though the server would have
accepted it.

Two checks make that decision:

* :py:meth:`ndex2.transport.HttpTransport.is_authenticated`, used by the
  v3 namespaces.
* ``Ndex2._require_auth()``, used by twelve flat methods. It predates
  token support and originally tested ``self.s.auth`` alone, which a
  bearer token clears.

The NDEx server accepts both ``Basic`` and ``Bearer`` on v2 and v3 alike,
so refusing a bearer-authenticated call is always the client's error.
"""

import io
import os
import unittest

import requests_mock

from ndex2.client import Ndex2
from ndex2.transport import HttpTransport
from ndex2.exceptions import NDExUnauthorizedError

SKIP_REASON = 'NDEX2_TEST_SERVER environment variable detected, ' \
              'skipping for integration tests'

HOST = 'http://foo.com'
NETWORK_ID = '22222222-2222-2222-2222-222222222222'
FOLDER_ID = '11111111-1111-1111-1111-111111111111'
JSON_HEADERS = {'Content-Type': 'application/json'}

# flat methods that gate on _require_auth() before issuing a request
AUTH_GATED = ('save_cx_stream_as_new_network',
              'save_cx2_stream_as_new_network',
              'update_cx_network',
              'update_cx2_network',
              'get_task_by_id',
              'delete_network',
              'set_provenance',
              'set_network_properties',
              'set_network_sample',
              'set_network_system_properties',
              'update_network_profile',
              'delete_networkset')


def client(**kwargs):
    kwargs.setdefault('skip_version_check', True)
    return Ndex2(host=HOST, **kwargs)


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestRequireAuthAcceptsBearerToken(unittest.TestCase):
    """``_require_auth`` must accept a bearer token.

    Without this, signing in with a token disables twelve flat methods,
    including ``save_cx2_stream_as_new_network`` which carries the new
    ``folder_id`` argument.
    """

    def test_require_auth_passes_with_bearer_token_only(self):
        c = client()
        c._http.set_auth(bearer_token='TOKEN')
        self.assertIsNone(c.s.auth, 'a bearer token clears session.auth')
        self.assertIsNone(c._require_auth())

    def test_require_auth_passes_with_basic_auth(self):
        c = client(username='bob', password='secret')
        self.assertIsNone(c._require_auth())

    def test_require_auth_still_rejects_when_nothing_is_set(self):
        self.assertRaises(NDExUnauthorizedError, client()._require_auth)

    def test_every_gated_flat_method_exists(self):
        """Guards the list above against a rename."""
        c = client()
        for name in AUTH_GATED:
            self.assertTrue(hasattr(c, name), name)

    def test_gated_flat_method_reaches_server_after_signin(self):
        """The end to end case: sign in with a token, then use a flat
        method that gates on credentials."""
        c = client(username='bob', password='secret')
        with requests_mock.mock() as m:
            m.post(HOST + '/v3/users/signin', json={'externalId': 'u'},
                   headers=JSON_HEADERS)
            c.users.signin('TOKEN')
        with requests_mock.mock() as m:
            m.put(HOST + '/v2/network/' + NETWORK_ID + '/profile',
                  status_code=200, text='')
            c.update_network_profile(NETWORK_ID, {'name': 'renamed'})
            self.assertEqual(1, len(m.request_history),
                             'the request was never sent')
            self.assertEqual('Bearer TOKEN',
                             m.request_history[0].headers['Authorization'])

    def test_cx2_creation_still_works_after_signin(self):
        """save_cx2_stream_as_new_network is gated and carries folder_id."""
        c = client(username='bob', password='secret')
        with requests_mock.mock() as m:
            m.post(HOST + '/v3/users/signin', json={'externalId': 'u'},
                   headers=JSON_HEADERS)
            c.users.signin('TOKEN')
        with requests_mock.mock() as m:
            loc = HOST + '/v3/networks/' + NETWORK_ID
            m.post(HOST + '/v3/networks', status_code=201,
                   headers={'Location': loc})
            res = c.save_cx2_stream_as_new_network(
                io.BytesIO(b'[]'), folder_id=FOLDER_ID)
            self.assertEqual(loc, res)
            self.assertIn('folderId=' + FOLDER_ID,
                          m.request_history[0].url)


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestIsAuthenticatedReadsTheSession(unittest.TestCase):
    """``is_authenticated`` must reflect the session, not a copy."""

    def test_direct_session_auth_assignment_is_seen(self):
        """Assigning client.s.auth is how credentials were changed before
        set_auth existed. The namespaces must honour it."""
        c = client()
        self.assertFalse(c._http.is_authenticated)
        c.s.auth = ('bob', 'secret')
        self.assertTrue(c._http.is_authenticated)

    def test_direct_authorization_header_is_seen(self):
        c = client()
        c.s.headers['Authorization'] = 'Bearer TOKEN'
        self.assertTrue(c._http.is_authenticated)

    def test_namespace_call_works_after_direct_session_assignment(self):
        c = client()
        c.s.auth = ('bob', 'secret')
        with requests_mock.mock() as m:
            m.post(HOST + '/v3/files/folders/', status_code=201,
                   json={'uuid': FOLDER_ID}, headers=JSON_HEADERS)
            self.assertEqual(FOLDER_ID, c.files.create_folder('f'))

    def test_clearing_the_session_is_seen(self):
        c = client(username='bob', password='secret')
        self.assertTrue(c._http.is_authenticated)
        c.s.auth = None
        self.assertFalse(c._http.is_authenticated)

    def test_still_false_with_no_credentials(self):
        self.assertFalse(client()._http.is_authenticated)

    def test_standalone_transport_unaffected(self):
        t = HttpTransport(HOST)
        self.assertFalse(t.is_authenticated)
        t.set_auth(username='bob', password='secret')
        self.assertTrue(t.is_authenticated)
        t.set_auth(bearer_token='TOKEN')
        self.assertTrue(t.is_authenticated)
        t.set_auth()
        self.assertFalse(t.is_authenticated)


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestFlatAndNamespaceAgreeOnAuth(unittest.TestCase):
    """The two auth checks must never disagree, in either direction."""

    def scenarios(self):
        basic = client(username='bob', password='secret')

        bearer = client()
        bearer._http.set_auth(bearer_token='TOKEN')

        direct = client()
        direct.s.auth = ('bob', 'secret')

        header = client()
        header.s.headers['Authorization'] = 'Bearer TOKEN'

        return [('constructor basic', basic, True),
                ('transport bearer', bearer, True),
                ('direct s.auth', direct, True),
                ('direct header', header, True),
                ('nothing set', client(), False)]

    def test_both_checks_agree(self):
        for label, c, expected in self.scenarios():
            self.assertEqual(expected, c._http.is_authenticated,
                             '%s: transport disagrees' % label)
            if expected:
                self.assertIsNone(c._require_auth(),
                                  '%s: flat check refused' % label)
            else:
                self.assertRaises(NDExUnauthorizedError, c._require_auth)


if __name__ == '__main__':
    unittest.main()
