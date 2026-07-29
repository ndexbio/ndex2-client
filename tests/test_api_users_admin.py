#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ndex2.api.users` and `ndex2.api.admin`."""

import os
import json
import unittest

import requests_mock

from ndex2.client import Ndex2
from ndex2.exceptions import NDExError
from ndex2.exceptions import NDExInvalidParameterError
from ndex2.exceptions import NDExNotFoundError
from ndex2.exceptions import NDExUnauthorizedError

SKIP_REASON = 'NDEX2_TEST_SERVER environment variable detected, ' \
              'skipping for integration tests'

HOST = 'http://foo.com'
V3 = HOST + '/v3'
USER_ID = '44444444-4444-4444-4444-444444444444'
FOLDER_ID = '11111111-1111-1111-1111-111111111111'
JSON_HEADERS = {'Content-Type': 'application/json'}


def client(authenticated=True):
    if authenticated:
        return Ndex2(host=HOST, username='bob', password='secret',
                     skip_version_check=True)
    return Ndex2(host=HOST, skip_version_check=True)


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestNamespaceWiring(unittest.TestCase):

    def test_all_four_namespaces_share_one_transport(self):
        c = client()
        transports = {id(c.files._http), id(c.networks._http),
                      id(c.users._http), id(c.admin._http), id(c._http)}
        self.assertEqual(1, len(transports))

    def test_method_counts(self):
        c = client()
        counts = {ns: len([m for m in dir(getattr(c, ns))
                           if not m.startswith('_')])
                  for ns in ('files', 'networks', 'users', 'admin')}
        self.assertEqual({'files': 26, 'networks': 11, 'users': 3,
                          'admin': 1}, counts)


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestUsers(unittest.TestCase):

    def test_get(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/users', json={'externalId': USER_ID},
                  headers=JSON_HEADERS)
            self.assertEqual(USER_ID, c.users.get('bob')['externalId'])
            self.assertEqual(['bob'], m.request_history[0].qs['username'])

    def test_get_invalid_username(self):
        c = client()
        for bad in (None, '   ', 5):
            self.assertRaises(NDExInvalidParameterError, c.users.get, bad)

    def test_get_not_found(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/users', status_code=404, text='nope')
            self.assertRaises(NDExNotFoundError, c.users.get, 'nobody')

    def test_home(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/users/' + USER_ID + '/home',
                  json=[{'uuid': FOLDER_ID, 'type': 'FOLDER'}],
                  headers=JSON_HEADERS)
            res = c.users.home(USER_ID)
            self.assertEqual('FOLDER', res[0]['type'])
            self.assertEqual(['update'], m.request_history[0].qs['format'])

    def test_home_compact_format(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/users/' + USER_ID + '/home', json=[],
                  headers=JSON_HEADERS)
            c.users.home(USER_ID, format='compact')
            self.assertEqual(['compact'], m.request_history[0].qs['format'])

    def test_home_empty_body_returns_list(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/users/' + USER_ID + '/home', status_code=204)
            self.assertEqual([], c.users.home(USER_ID))

    def test_home_rejects_none_user_id(self):
        self.assertRaises(NDExInvalidParameterError, client().users.home,
                          None)

    def test_home_allows_anonymous(self):
        """Anonymous callers see public items only, but may call."""
        c = client(authenticated=False)
        with requests_mock.mock() as m:
            m.get(V3 + '/users/' + USER_ID + '/home', json=[],
                  headers=JSON_HEADERS)
            self.assertEqual([], c.users.home(USER_ID))

    def test_signin_returns_user_and_sets_bearer_token(self):
        c = client(authenticated=False)
        with requests_mock.mock() as m:
            m.post(V3 + '/users/signin', json={'externalId': USER_ID},
                   headers=JSON_HEADERS)
            res = c.users.signin('tok')
            self.assertEqual(USER_ID, res['externalId'])
            self.assertEqual({'id_token': 'tok'},
                             json.loads(m.request_history[0].text))
        self.assertEqual('tok', c._http.bearer_token)
        self.assertEqual('Bearer tok',
                         c._http.session.headers['Authorization'])

    def test_signin_reauthenticates_the_whole_client(self):
        """The transport shares its session, so the flat methods change too."""
        c = client()
        self.assertEqual(('bob', 'secret'), c.s.auth)
        with requests_mock.mock() as m:
            m.post(V3 + '/users/signin', json={'externalId': USER_ID},
                   headers=JSON_HEADERS)
            c.users.signin('tok')
        self.assertIsNone(c.s.auth)
        self.assertEqual('Bearer tok', c.s.headers['Authorization'])

    def test_signin_reaches_every_namespace(self):
        c = client(authenticated=False)
        with requests_mock.mock() as m:
            m.post(V3 + '/users/signin', json={'externalId': USER_ID},
                   headers=JSON_HEADERS)
            c.users.signin('tok')
        for ns in ('files', 'networks', 'users', 'admin'):
            self.assertTrue(getattr(c, ns)._http.is_authenticated)

    def test_signin_invalid_token(self):
        c = client()
        self.assertRaises(NDExInvalidParameterError, c.users.signin, None)
        self.assertRaises(NDExInvalidParameterError, c.users.signin, '')

    def test_signin_rejected_leaves_credentials_alone(self):
        """A failed sign-in must not clear existing credentials."""
        c = client()
        with requests_mock.mock() as m:
            m.post(V3 + '/users/signin', status_code=401, text='denied')
            self.assertRaises(NDExUnauthorizedError, c.users.signin, 'bad')
        self.assertEqual(('bob', 'secret'), c.s.auth)
        self.assertIsNone(c._http.bearer_token)


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestAdmin(unittest.TestCase):

    def test_status(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/admin/status', json={'message': 'Online'},
                  headers=JSON_HEADERS)
            self.assertEqual('Online', c.admin.status()['message'])
            self.assertEqual(['full'], m.request_history[0].qs['format'])

    def test_status_allows_anonymous(self):
        c = client(authenticated=False)
        with requests_mock.mock() as m:
            m.get(V3 + '/admin/status', json={}, headers=JSON_HEADERS)
            self.assertEqual({}, c.admin.status())

    def test_status_on_non_v3_host_raises(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/admin/status', status_code=404, text='nope')
            self.assertRaises(NDExError, c.admin.status)

    def test_status_does_not_touch_flat_status_cache(self):
        """The flat update_status caches on self.status; this must not."""
        c = client()
        self.assertEqual({}, c.status)
        with requests_mock.mock() as m:
            m.get(V3 + '/admin/status', json={'message': 'Online'},
                  headers=JSON_HEADERS)
            c.admin.status()
        self.assertEqual({}, c.status)


if __name__ == '__main__':
    unittest.main()
