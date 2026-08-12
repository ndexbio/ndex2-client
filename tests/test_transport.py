#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ndex2.transport`."""

import os
import json
import unittest

import requests
import requests_mock

from ndex2.transport import HttpTransport
from ndex2.transport import V2
from ndex2.exceptions import NDExError
from ndex2.exceptions import NDExNotFoundError
from ndex2.exceptions import NDExUnauthorizedError
from ndex2.exceptions import raise_from_exception
from ndex2.exceptions import raise_from_requests_http_error

SKIP_REASON = 'NDEX2_TEST_SERVER environment variable detected, ' \
              'skipping for integration tests'

HOST = 'http://foo.com'
UUID = '11111111-1111-1111-1111-111111111111'
JSON_HEADERS = {'Content-Type': 'application/json'}


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestHttpTransportConstruction(unittest.TestCase):

    def test_host_required(self):
        self.assertRaises(NDExError, HttpTransport, None)

    def test_scheme_added_when_missing(self):
        self.assertEqual('http://foo.com', HttpTransport('foo.com').host)

    def test_scheme_preserved(self):
        self.assertEqual('https://foo.com',
                         HttpTransport('https://foo.com').host)

    def test_trailing_slash_stripped(self):
        self.assertEqual('http://foo.com/rest',
                         HttpTransport('http://foo.com/rest/').host)

    def test_servlet_context_path_preserved(self):
        t = HttpTransport('https://dev3.ndex.ucsd.edu/rest')
        self.assertEqual('https://dev3.ndex.ucsd.edu/rest/v3/files/count',
                         t.build_url('/files/count'))

    def test_defaults(self):
        t = HttpTransport(HOST)
        self.assertEqual(30, t.timeout)
        self.assertFalse(t.debug)
        self.assertFalse(t.is_authenticated)

    def test_user_agent_suffix_appended(self):
        t = HttpTransport(HOST, user_agent=' mytool/1.0')
        with requests_mock.mock() as mock:
            mock.get(HOST + '/v3/x', json={})
            t.get('/x')
            agent = mock.request_history[0].headers['User-Agent']
            self.assertTrue(agent.endswith(' mytool/1.0'))
            self.assertTrue(agent.startswith('ndex2-client'))

    def test_supplied_session_is_used(self):
        session = requests.session()
        self.assertIs(session, HttpTransport(HOST, session=session).session)


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestHttpTransportAuth(unittest.TestCase):

    def test_basic_auth(self):
        t = HttpTransport(HOST, username='bob', password='secret')
        self.assertEqual(('bob', 'secret'), t.session.auth)
        self.assertTrue(t.is_authenticated)

    def test_bearer_token(self):
        t = HttpTransport(HOST, bearer_token='tok')
        self.assertEqual('Bearer tok', t.session.headers['Authorization'])
        self.assertTrue(t.is_authenticated)

    def test_bearer_token_preferred_over_basic(self):
        t = HttpTransport(HOST, username='bob', password='secret',
                          bearer_token='tok')
        self.assertEqual('Bearer tok', t.session.headers['Authorization'])
        self.assertIsNone(t.session.auth)

    def test_username_without_password_is_not_authenticated(self):
        t = HttpTransport(HOST, username='bob')
        self.assertFalse(t.is_authenticated)
        self.assertIsNone(t.session.auth)

    def test_set_auth_switches_basic_to_bearer(self):
        t = HttpTransport(HOST, username='bob', password='secret')
        t.set_auth(bearer_token='tok')
        self.assertEqual('Bearer tok', t.session.headers['Authorization'])
        self.assertIsNone(t.session.auth)

    def test_set_auth_switches_bearer_to_basic(self):
        t = HttpTransport(HOST, bearer_token='tok')
        t.set_auth(username='bob', password='secret')
        self.assertEqual(('bob', 'secret'), t.session.auth)
        self.assertNotIn('Authorization', t.session.headers)

    def test_set_auth_with_no_arguments_clears(self):
        t = HttpTransport(HOST, bearer_token='tok')
        t.set_auth()
        self.assertFalse(t.is_authenticated)
        self.assertNotIn('Authorization', t.session.headers)
        self.assertIsNone(t.session.auth)

    def test_require_auth_raises_when_unauthenticated(self):
        self.assertRaises(NDExUnauthorizedError,
                          HttpTransport(HOST).require_auth)

    def test_require_auth_passes_when_authenticated(self):
        t = HttpTransport(HOST, username='bob', password='secret')
        self.assertIsNone(t.require_auth())


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestHttpTransportRequests(unittest.TestCase):

    def get_transport(self):
        return HttpTransport(HOST, username='bob', password='secret')

    def test_version_routing(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.get(HOST + '/v3/thing', json={})
            mock.get(HOST + '/v2/thing', json={})
            t.get('/thing')
            self.assertIn('/v3/thing', mock.request_history[0].url)
            t.get('/thing', version=V2)
            self.assertIn('/v2/thing', mock.request_history[1].url)

    def test_all_verbs(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            for verb in ('get', 'post', 'put', 'delete'):
                getattr(mock, verb)(HOST + '/v3/thing', json={'v': verb})
                self.assertEqual({'v': verb}, getattr(t, verb)('/thing'))

    def test_none_params_are_dropped(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.get(HOST + '/v3/thing', json={})
            t.get('/thing', params={'accesskey': None, 'limit': 5})
            qs = mock.request_history[0].qs
            self.assertNotIn('accesskey', qs)
            self.assertEqual(['5'], qs['limit'])

    def test_query_params_on_every_verb(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.put(HOST + '/v3/thing', status_code=204)
            mock.delete(HOST + '/v3/thing', status_code=204)
            t.put('/thing', params={'force': 'true'})
            self.assertEqual(['true'], mock.request_history[0].qs['force'])
            t.delete('/thing', params={'permanent': 'true'})
            self.assertEqual(['true'],
                             mock.request_history[1].qs['permanent'])

    def test_json_body_and_content_type(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.post(HOST + '/v3/thing', json={})
            t.post('/thing', json_body={'name': 'x'})
            req = mock.request_history[0]
            self.assertEqual({'name': 'x'}, json.loads(req.text))
            self.assertIn('application/json',
                          req.headers['Content-Type'])

    def test_no_content_type_without_body(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.get(HOST + '/v3/thing', json={})
            t.get('/thing')
            self.assertNotIn('Content-Type',
                             mock.request_history[0].headers)

    def test_extra_headers_merged(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.get(HOST + '/v3/thing', json={})
            t.get('/thing', extra_headers={'X-Custom': 'v'})
            self.assertEqual('v',
                             mock.request_history[0].headers['X-Custom'])

    def test_session_headers_not_mutated(self):
        """Per-request headers must not leak into the shared session."""
        t = self.get_transport()
        before = dict(t.session.headers)
        with requests_mock.mock() as mock:
            mock.post(HOST + '/v3/thing', json={})
            t.post('/thing', json_body={'a': 1},
                   extra_headers={'X-Custom': 'v'})
        self.assertEqual(before, dict(t.session.headers))

    def test_return_response(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.post(HOST + '/v3/thing', status_code=201, json={})
            res = t.post('/thing', return_response=True)
            self.assertEqual(201, res.status_code)

    def test_stream_returns_response(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.get(HOST + '/v3/thing', text='a\tb\n')
            res = t.get('/thing', stream=True)
            self.assertEqual('a\tb\n', res.text)

    def test_timeout_passed_through(self):
        t = HttpTransport(HOST, username='b', password='p', timeout=7)
        with requests_mock.mock() as mock:
            mock.get(HOST + '/v3/thing', json={})
            t.get('/thing')
            self.assertEqual(7, mock.request_history[0].timeout)


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestHttpTransportErrors(unittest.TestCase):

    def get_transport(self):
        return HttpTransport(HOST, username='bob', password='secret')

    def test_404(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.get(HOST + '/v3/thing', status_code=404, text='nope')
            self.assertRaises(NDExNotFoundError, t.get, '/thing')

    def test_401(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.get(HOST + '/v3/thing', status_code=401, text='denied')
            self.assertRaises(NDExUnauthorizedError, t.get, '/thing')

    def test_500(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.get(HOST + '/v3/thing', status_code=500, text='boom')
            self.assertRaises(NDExError, t.get, '/thing')

    def test_error_message_includes_status_and_body(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.get(HOST + '/v3/thing', status_code=500, text='kaboom')
            try:
                t.get('/thing')
                self.fail('expected NDExError')
            except NDExError as e:
                self.assertIn('500', str(e))
                self.assertIn('kaboom', str(e))

    def test_connection_error_becomes_ndex_error(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.get(HOST + '/v3/thing',
                     exc=requests.exceptions.ConnectTimeout)
            self.assertRaises(NDExError, t.get, '/thing')

    def test_501_becomes_ndex_error(self):
        """Removed server features report 501; it must surface clearly."""
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.get(HOST + '/v3/thing', status_code=501,
                     text='feature removed')
            try:
                t.get('/thing')
                self.fail('expected NDExError')
            except NDExError as e:
                self.assertIn('501', str(e))


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestHttpTransportParsing(unittest.TestCase):

    def get_transport(self):
        return HttpTransport(HOST, username='bob', password='secret')

    def test_204_returns_none(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.delete(HOST + '/v3/thing', status_code=204)
            self.assertIsNone(t.delete('/thing'))

    def test_empty_body_returns_none(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.get(HOST + '/v3/thing', text='')
            self.assertIsNone(t.get('/thing'))

    def test_json_content_type_parsed(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.get(HOST + '/v3/thing', json={'a': 1},
                     headers=JSON_HEADERS)
            self.assertEqual({'a': 1}, t.get('/thing'))

    def test_json_parsed_without_content_type(self):
        """A proxy that strips Content-Type must not yield a string."""
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.get(HOST + '/v3/thing', text='{"a": 1}',
                     headers={'Content-Type': 'text/plain'})
            self.assertEqual({'a': 1}, t.get('/thing'))

    def test_json_array_parsed_without_content_type(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.get(HOST + '/v3/thing', text='[1, 2]',
                     headers={'Content-Type': 'text/plain'})
            self.assertEqual([1, 2], t.get('/thing'))

    def test_bare_scalar_stays_text(self):
        """A text/plain body of digits must not become an int."""
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.get(HOST + '/v3/thing', text='123',
                     headers={'Content-Type': 'text/plain'})
            self.assertEqual('123', t.get('/thing'))

    def test_plain_text_returned_as_text(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.get(HOST + '/v3/thing', text='Online',
                     headers={'Content-Type': 'text/plain'})
            self.assertEqual('Online', t.get('/thing'))

    def test_malformed_json_falls_back_to_text(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.get(HOST + '/v3/thing', text='{not valid',
                     headers=JSON_HEADERS)
            self.assertEqual('{not valid', t.get('/thing'))


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestUuidFromCreated(unittest.TestCase):

    def get_transport(self):
        return HttpTransport(HOST, username='bob', password='secret')

    def test_uuid_from_body(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.post(HOST + '/v3/thing', status_code=201,
                      json={'uuid': UUID}, headers=JSON_HEADERS)
            res = t.post('/thing', return_response=True)
            self.assertEqual(UUID, t.uuid_from_created(res))

    def test_body_preferred_over_location(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.post(HOST + '/v3/thing', status_code=201,
                      json={'uuid': UUID},
                      headers={'Content-Type': 'application/json',
                               'Location': HOST + '/v3/thing/other'})
            res = t.post('/thing', return_response=True)
            self.assertEqual(UUID, t.uuid_from_created(res))

    def test_falls_back_to_location_header(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.post(HOST + '/v3/thing', status_code=201, text='',
                      headers={'Location': HOST + '/v3/thing/' + UUID})
            res = t.post('/thing', return_response=True)
            self.assertEqual(UUID, t.uuid_from_created(res))

    def test_location_trailing_slash_tolerated(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.post(HOST + '/v3/thing', status_code=201, text='',
                      headers={'Location': HOST + '/v3/thing/' + UUID + '/'})
            res = t.post('/thing', return_response=True)
            self.assertEqual(UUID, t.uuid_from_created(res))

    def test_falls_back_to_quoted_body(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.post(HOST + '/v3/thing', status_code=201,
                      text='"' + UUID + '"',
                      headers={'Content-Type': 'text/plain'})
            res = t.post('/thing', return_response=True)
            self.assertEqual(UUID, t.uuid_from_created(res))

    def test_raises_when_no_uuid_available(self):
        t = self.get_transport()
        with requests_mock.mock() as mock:
            mock.post(HOST + '/v3/thing', status_code=201, text='')
            res = t.post('/thing', return_response=True)
            self.assertRaises(NDExError, t.uuid_from_created, res)


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestSharedErrorConverters(unittest.TestCase):
    """The converters moved to ndex2.exceptions so client.py and the
    transport report server failures identically."""

    def make_http_error(self, status_code, text):
        response = requests.Response()
        response.status_code = status_code
        response._content = text.encode('utf-8')
        return requests.exceptions.HTTPError(response=response)

    def test_404(self):
        self.assertRaises(NDExNotFoundError,
                          raise_from_requests_http_error,
                          self.make_http_error(404, 'nope'))

    def test_401(self):
        self.assertRaises(NDExUnauthorizedError,
                          raise_from_requests_http_error,
                          self.make_http_error(401, 'denied'))

    def test_other_status(self):
        self.assertRaises(NDExError, raise_from_requests_http_error,
                          self.make_http_error(500, 'boom'))

    def test_none_http_error(self):
        self.assertRaises(NDExError, raise_from_requests_http_error, None)

    def test_exception_converter(self):
        try:
            raise_from_exception(ValueError('bad'))
            self.fail('expected NDExError')
        except NDExError as e:
            self.assertIn('ValueError', str(e))
            self.assertIn('bad', str(e))

    def test_none_exception(self):
        self.assertRaises(NDExError, raise_from_exception, None)

    def test_client_still_delegates(self):
        """Ndex2's private converters must keep their behaviour."""
        from ndex2.client import Ndex2
        client = Ndex2(skip_version_check=True)
        self.assertRaises(NDExNotFoundError,
                          client._convert_requests_http_error_to_ndex_error,
                          self.make_http_error(404, 'nope'))
        self.assertRaises(NDExError,
                          client._convert_exception_to_ndex_error,
                          ValueError('bad'))


if __name__ == '__main__':
    unittest.main()
