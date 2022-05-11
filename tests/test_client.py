#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ndex2.client` package."""

import os
import sys
import io
import decimal
import unittest
import numpy as np
import json

import requests_mock
from unittest.mock import MagicMock
from requests.exceptions import HTTPError
from ndex2 import client
from ndex2.client import Ndex2
from ndex2.client import DecimalEncoder
from ndex2 import __version__
from ndex2.exceptions import NDExInvalidCXError
from ndex2.exceptions import NDExNotFoundError
from ndex2.exceptions import NDExUnauthorizedError
from ndex2.exceptions import NDExInvalidParameterError
from ndex2.exceptions import NDExUnsupportedCallError
from ndex2.exceptions import NDExError

SKIP_REASON = 'NDEX2_TEST_USER environment variable detected, ' \
              'skipping for integration tests'


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestClient(unittest.TestCase):

    def get_rest_admin_status_dict(self, version='2.1'):
        return {"networkCount": 1321,
                "userCount": 12,
                "groupCount": 0,
                "message": "Online",
                "properties": {"ServerVersion": version,
                               "ServerResultLimit": "10000"}}

    def get_rest_admin_v1_empty_dict(self):
        return {}

    def get_rest_admin_status_url(self):
        return client.DEFAULT_SERVER + '/rest/admin/status'

    def setUp(self):
        """Set up test fixtures, if any."""
        pass

    def tearDown(self):
        """Tear down test fixtures, if any."""
        pass

    def test_decimalencoder(self):
        dec = DecimalEncoder()

        if sys.version_info.major >= 3:
            # test bytes is returned as string
            res = dec.default(bytes('hello', 'utf-8'))
            self.assertTrue(isinstance(res, str))

        # test decimal.Decimal is float
        res = dec.default(decimal.Decimal(5))
        self.assertTrue(isinstance(res, float))

        # test numpy.int64 is int
        res = dec.default(np.int64(12))
        self.assertTrue(isinstance(res, int))

        # test regular old int which throws TypeError
        try:
            res = dec.default(np.int32(1))
            self.assertEqual(res, int(1))
        except TypeError:
            pass

    def test_ndex2_constructor_with_localhost(self):

        # this is invasive, but there isn't really a good way
        # to test the constructor
        # try with nothing set
        ndex = Ndex2(host='localhost')
        self.assertEqual(ndex.debug, False)
        self.assertEqual(ndex.version, '1.3')
        self.assertEqual(ndex.status, {})
        self.assertEqual(ndex.username, None)
        self.assertEqual(ndex.password, None)
        self.assertEqual(ndex.user_agent, '')
        self.assertEqual(ndex.host, 'http://localhost:8080/ndexbio-rest')
        self.assertTrue(ndex.s is not None)
        self.assertTrue(ndex.timeout, 30)
        ndex.set_request_timeout(10)
        self.assertTrue(ndex.timeout, 30)

        # try with user, pass and user_agent set oh and host
        # with extra text prepended to localhost
        ndex = Ndex2(host='xxxlocalhost', username='bob',
                     password='smith', user_agent='yo', debug=True,
                     timeout=1)
        self.assertEqual(ndex.debug, True)
        self.assertEqual(ndex.version, '1.3')
        self.assertEqual(ndex.status, {})
        self.assertEqual(ndex.username, 'bob')
        self.assertEqual(ndex.password, 'smith')
        self.assertEqual(ndex.user_agent, ' yo')
        self.assertEqual(ndex.version_endpoint, '/rest')
        self.assertEqual(ndex.host, 'http://localhost:8080/ndexbio-rest')
        self.assertTrue(ndex.s is not None)
        self.assertTrue(ndex.timeout, 1)

        # try with user_agent set to None Issue #34
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            ndex = Ndex2(user_agent=None)
            self.assertEqual(ndex.user_agent, '')

    def test_ndex2_constructor_that_raises_httperror(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  text='uhoh',
                  reason='some error',
                  status_code=404)
            ndex = Ndex2()
            self.assertEqual(ndex.debug, False)
            self.assertEqual(ndex.version, '1.3')
            self.assertEqual(ndex.status, {})
            self.assertEqual(ndex.username, None)
            self.assertEqual(ndex.password, None)
            self.assertEqual(ndex.user_agent, '')
            self.assertEqual(ndex.version_endpoint, '/rest')
            self.assertEqual(ndex.host, client.DEFAULT_SERVER)
            self.assertTrue(ndex.s is not None)

    def test_ndex2_constructor_with_defaulthost_serverversionnone(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json={"networkCount": 1321,
                        "userCount": 12,
                        "groupCount": 0,
                        "message": "Online",
                        "properties": {"ServerVersion": None}})
            ndex = Ndex2()
            self.assertEqual(ndex.debug, False)
            self.assertEqual(ndex.version, '1.3')
            self.assertEqual(ndex.status, {})
            self.assertEqual(ndex.username, None)
            self.assertEqual(ndex.password, None)
            self.assertEqual(ndex.user_agent, '')
            self.assertEqual(ndex.version_endpoint, '/rest')
            self.assertEqual(ndex.host, client.DEFAULT_SERVER)
            self.assertTrue(ndex.s is not None)

    def test_ndex2_constructor_with_defaulthost_properties_is_none(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json={"networkCount": 1321,
                        "userCount": 12,
                        "groupCount": 0,
                        "message": "Online"})
            ndex = Ndex2()
            self.assertEqual(ndex.debug, False)
            self.assertEqual(ndex.version, '1.3')
            self.assertEqual(ndex.status, {})
            self.assertEqual(ndex.username, None)
            self.assertEqual(ndex.password, None)
            self.assertEqual(ndex.user_agent, '')
            self.assertEqual(ndex.version_endpoint, '/rest')
            self.assertEqual(ndex.host, client.DEFAULT_SERVER)
            self.assertTrue(ndex.s is not None)

    def test_ndex2_constructor_with_defaulthost_thatisversionone(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json={"networkCount": 1321,
                        "userCount": 12,
                        "groupCount": 0,
                        "message": "Online",
                        "properties": {"ServerVersion": "1.1",
                                       "ServerResultLimit": "10000"}})
            try:
                Ndex2()
                self.fail('Expected exception')
            except Exception as e:
                self.assertEqual(str(e),
                                 'This release only supports NDEx 2.x server.')

    def test_ndex2_constructor_with_defaulthost_thatisversiontwo(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            ndex = Ndex2()
            self.assertEqual(ndex.debug, False)
            self.assertEqual(ndex.version, '2.1')
            self.assertEqual(ndex.status, {})
            self.assertEqual(ndex.username, None)
            self.assertEqual(ndex.password, None)
            self.assertEqual(ndex.user_agent, '')
            self.assertEqual(ndex.version_endpoint, '/v2')
            self.assertEqual(ndex.host, client.DEFAULT_SERVER)
            self.assertTrue(ndex.s is not None)

    def test_ndex2_constructor_with_skip_check_version_true(self):
        ndex = Ndex2(skip_version_check=True)
        self.assertEqual(ndex.debug, False)
        self.assertEqual(ndex.version, '2.0')
        self.assertEqual(ndex.status, {})
        self.assertEqual(ndex.username, None)
        self.assertEqual(ndex.password, None)
        self.assertEqual(ndex.user_agent, '')
        self.assertEqual(ndex.version_endpoint, '/v2')
        self.assertEqual(ndex.host, client.DEFAULT_SERVER)
        self.assertTrue(ndex.s is not None)

    def test_ndex2_require_auth(self):
        ndex = Ndex2(host='localhost')
        try:
            ndex._require_auth()
            self.fail('Expected exception')
        except Exception as e:
            self.assertEqual(str(e),
                             'This method requires user authentication')

    def test_ndex2_get_user_agent(self):
        ndex = Ndex2(host='localhost')
        # try with default
        res = ndex._get_user_agent()
        self.assertEqual(res, 'NDEx2-Python/' + __version__)

        ndex = Ndex2(host='localhost', user_agent='hi')
        # try with user_agent set
        res = ndex._get_user_agent()
        self.assertEqual(res, 'NDEx2-Python/' + __version__ + ' hi')

    def test_convert_exception_to_ndex_error(self):
        # try passing none
        ndex = Ndex2(host='localhost')
        try:
            ndex._convert_exception_to_ndex_error(None)
        except NDExError as ne:
            self.assertEqual('Caught unknown error', str(ne))

        # try passing in a ValueError
        try:
            ndex._convert_exception_to_ndex_error(ValueError('hi'))
        except NDExError as ne:
            self.assertEqual('Caught ValueError: hi', str(ne))

    def test_convert_requests_http_error_to_ndex_error(self):
        # try passing none
        ndex = Ndex2(host='localhost')
        try:
            ndex._convert_requests_http_error_to_ndex_error(None)
        except NDExError as ne:
            self.assertEqual('Caught unknown server error', str(ne))

        error = MagicMock()
        error.response = MagicMock()
        error.response.status_code = 404
        error.response.text = 'hi'

        # try passing in a mock HTTPError
        try:
            ndex._convert_requests_http_error_to_ndex_error(error)
            self.fail('Expected NDExNotFoundError')
        except NDExNotFoundError as ne:
            self.assertEqual('Caught 404 from server: hi', str(ne))

        # try passing in a 500 error
        error.response.status_code = 500
        try:
            ndex._convert_requests_http_error_to_ndex_error(error)
            self.fail('Expected NDExError')
        except NDExError as ne:
            self.assertEqual('Caught 500 from server: hi', str(ne))

    def test_ndex2_put_no_json_empty_resp_code_204(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.put(client.DEFAULT_SERVER + '/v2/hi', status_code=204)
            ndex = Ndex2()
            res = ndex.put('/hi')
            self.assertEqual(res, '')

    def test_ndex2_put_no_json_empty_code_200(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.put(client.DEFAULT_SERVER + '/v2/hi',
                  status_code=200,
                  text='hehe',
                  request_headers={'Content-Type': 'application/'
                                                   'json;charset=UTF-8',
                                   'Accept': 'application/json',
                                   'User-Agent': client.userAgent},
                  headers={'Content-Type': 'application/foo'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.put('/hi')
            self.assertEqual(res, 'hehe')

    def test_ndex2_put_returns_code_401(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.put(client.DEFAULT_SERVER + '/v2/hi',
                  status_code=401,
                  text='hehe',
                  request_headers={'Content-Type': 'application/'
                                                   'json;charset=UTF-8',
                                   'Accept': 'application/json',
                                   'User-Agent': client.userAgent},
                  headers={'Content-Type': 'application/foo'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            try:
                ndex.put('/hi')
                self.fail('Expected HTTPError')
            except HTTPError as he:
                self.assertEqual(he.response.status_code, 401)
                self.assertEqual(he.response.text, 'hehe')

    def test_ndex2_put_returns_code_500(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.put(client.DEFAULT_SERVER + '/v2/hi',
                  status_code=500,
                  text='hehe',
                  request_headers={'Content-Type': 'application/'
                                                   'json;charset=UTF-8',
                                   'Accept': 'application/json',
                                   'User-Agent': client.userAgent},
                  headers={'Content-Type': 'application/foo'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            try:
                ndex.put('/hi')
                self.fail('Expected HTTPError')
            except HTTPError as he:
                self.assertEqual(he.response.status_code, 500)
                self.assertEqual(he.response.text, 'hehe')

    def test_ndex2_put_with_json_and_json_resp(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.put(client.DEFAULT_SERVER + '/v2/hi',
                  status_code=200,
                  json={'hi': 'bye'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.put('/hi', put_json='{"x": "y"}')
            self.assertEqual(res, {'hi': 'bye'})

    def test_ndex2_post_with_json_and_json_resp(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.post(client.DEFAULT_SERVER + '/v2/hi',
                   status_code=200,
                   json={'hi': 'bye'},
                   headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.post('/hi', post_json='{"x": "y"}')
            self.assertEqual(res, {'hi': 'bye'})

    def test_ndex2_delete_with_json_and_json_resp(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.delete(client.DEFAULT_SERVER + '/v2/hi',
                     status_code=200,
                     json={'hi': 'bye'},
                     headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.delete('/hi', data='{"x": "y"}')
            self.assertEqual(res, {'hi': 'bye'})

    def test_ndex2_delete_no_data(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.delete(client.DEFAULT_SERVER + '/v2/hi',
                     status_code=200,
                     json={'hi': 'bye'},
                     headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.delete('/hi')
            self.assertEqual(res, {'hi': 'bye'})

    def test_ndex2_get_with_json_and_json_resp(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.get(client.DEFAULT_SERVER + '/v2/hi?x=y',
                  status_code=200,
                  json={'hi': 'bye'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.get('/hi', get_params={"x": "y"})
            self.assertEqual(res, {'hi': 'bye'})

    def test_ndex2_get_stream_withparams(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.get(client.DEFAULT_SERVER + '/v2/hi?x=y',
                  status_code=200,
                  json={'hi': 'bye'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.get_stream('/hi', get_params={"x": "y"})
            self.assertEqual(res.json(), {'hi': 'bye'})
            self.assertEqual(res.status_code, 200)

    def test_ndex2_post_stream_withparams(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.post(client.DEFAULT_SERVER + '/v2/hi',
                   status_code=200,
                   json={'hi': 'bye'},
                   request_headers={'Connection': 'close'},
                   headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.post_stream('/hi', post_json={"x": "y"})
            self.assertEqual(res.json(), {'hi': 'bye'})
            self.assertEqual(res.status_code, 200)

    def test_ndex2_put_multipart(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.put(client.DEFAULT_SERVER + '/v2/hi',
                  request_headers={'Connection': 'close'},
                  status_code=200)
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.put_multipart('/hi', fields={"x": "y"})
            self.assertEqual(res, '')

    def test_ndex2_post_multipart(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.post(client.DEFAULT_SERVER + '/v2/hi',
                   request_headers={'Connection': 'close'},
                   status_code=200)
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.post_multipart('/hi', fields={"x": "y"})
            self.assertEqual(res, '')

    def test_ndex2_post_multipart_with_querystring(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.post(client.DEFAULT_SERVER + '/v2/hi?yo=1',
                   request_headers={'Connection': 'close'},
                   status_code=200)
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.post_multipart('/hi', {"x": "y"}, query_string='yo=1')
            self.assertEqual(res, '')

    def test_get_id_for_user_invalid_param(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                 json=self.get_rest_admin_status_dict())
            ndex = Ndex2()
            # try where None passed in and client was
            # also constructed with anonymous connection so
            # no username
            try:
                ndex.get_id_for_user(None)
                self.fail('Expected NDExInvalidParameterError')
            except NDExInvalidParameterError as ne:
                self.assertTrue('None passed in this method' in str(ne))

            # try where username is not of type str
            try:
                ndex.get_id_for_user(44)
                self.fail('Expected NDExInvalidParameterError')
            except NDExInvalidParameterError as ne:
                self.assertEqual('Username must be of type str', str(ne))

            # try where username is empty str
            try:
                ndex.get_id_for_user('')
                self.fail('Expected NDExInvalidParameterError')
            except NDExInvalidParameterError as ne:
                self.assertEqual('Username cannot be empty str', str(ne))

    def test_get_user_by_username(self):
        with requests_mock.mock() as m:
            resurl = client.DEFAULT_SERVER + '/v2/user?username=bob'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.get(resurl, json={'userName': 'bob'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            res = ndex.get_user_by_username('bob')
            self.assertEqual('bob', res['userName'])

    def test_get_id_for_user_success(self):
        with requests_mock.mock() as m:
            resurl = client.DEFAULT_SERVER + '/v2/user?username=bob'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.get(resurl, json={'externalId': '12345'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            self.assertEqual('12345', ndex.get_id_for_user('bob'))

    def test_get_id_for_user_httperror(self):
        with requests_mock.mock() as m:
            resurl = client.DEFAULT_SERVER + '/v2/user?username=bob'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.get(resurl,
                  status_code=404,
                  text='error',
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            try:
                ndex.get_id_for_user('bob')
                self.fail('Expected NDExNotFoundError')
            except NDExNotFoundError as ne:
                self.assertEqual('Caught 404 from server: error',
                                 str(ne))

    def test_get_id_for_user_exception(self):
        with requests_mock.mock() as m:
            resurl = client.DEFAULT_SERVER + '/v2/user?username=bob'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.get(resurl,
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            try:
                ndex.get_id_for_user('bob')
                self.fail('Expected NDExError')
            except NDExError as ne:
                self.assertTrue('Caught JSONDecodeError:' in str(ne))

    def test_get_id_for_user_no_external_id(self):
        with requests_mock.mock() as m:
            resurl = client.DEFAULT_SERVER + '/v2/user?username=bob'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.get(resurl,
                  json={'uhoh': 'missing'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            try:
                ndex.get_id_for_user('bob')
                self.fail('Expected NDExError')
            except NDExError as ne:
                self.assertTrue('Unable to get user id for user: bob',
                                str(ne))

    def test_get_user_by_id_invalid_user_id(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            ndex = Ndex2()
            # try passing None
            try:
                ndex.get_user_by_id(None)
                self.fail('Expect NDExInvalidParameterError')
            except NDExInvalidParameterError as ne:
                self.assertEqual('user_id must be a str', str(ne))

            # try passing empty string
            try:
                ndex.get_user_by_id('')
                self.fail('Expect NDExInvalidParameterError')
            except NDExInvalidParameterError as ne:
                self.assertEqual('user_id cannot be an empty str', str(ne))

    def test_get_user_by_id_success(self):
        with requests_mock.mock() as m:

            resurl = client.DEFAULT_SERVER + '/v2/user/foo'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.get(resurl,
                  json={'userName': 'foo'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            res = ndex.get_user_by_id('foo')
            self.assertEqual('foo', res['userName'])

    def test_get_user_by_id_404_error(self):
        with requests_mock.mock() as m:

            resurl = client.DEFAULT_SERVER + '/v2/user/foo'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.get(resurl,
                  text='some error', status_code=404)
            ndex = Ndex2()
            try:
                res = ndex.get_user_by_id('foo')
                self.fail('Expected NDExNotFoundError: ' + str(res))
            except NDExNotFoundError as ne:
                self.assertEqual('Caught 404 from server: some error',
                                 str(ne))

    def test_get_user_by_id_500_error(self):
        with requests_mock.mock() as m:

            resurl = client.DEFAULT_SERVER + '/v2/user/foo'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.get(resurl,
                  text='error', status_code=500)
            ndex = Ndex2()
            try:
                res = ndex.get_user_by_id('foo')
                self.fail('Expected NDExNotFoundError: ' + str(res))
            except NDExError as ne:
                self.assertEqual('Caught 500 from server: error',
                                 str(ne))

    def test_get_user_by_id_random_exception(self):
        with requests_mock.mock() as m:

            resurl = client.DEFAULT_SERVER + '/v2/user/foo'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.get(resurl,
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            try:
                res = ndex.get_user_by_id('foo')
                self.fail('Expected NDExError: ' + str(res))
            except NDExError as ne:
                self.assertTrue('Caught JSONDecodeError' in str(ne))

    def test_get_networksets_for_user_invalid_userid(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            ndex = Ndex2()

            # try where user id is None
            try:
                ndex.get_networksets_for_user_id(None)
                self.fail('Expected NDExInvalidParameterError')
            except NDExInvalidParameterError as ne:
                self.assertEqual('user_id must be of type str',
                                 str(ne))

            # try where user id is not of type str
            try:
                ndex.get_networksets_for_user_id(4)
                self.fail('Expected NDExInvalidParameterError')
            except NDExInvalidParameterError as ne:
                self.assertEqual('user_id must be of type str',
                                 str(ne))

    def test_get_networksets_for_user_invalid_limit(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            ndex = Ndex2()

            # try where limit is not int or str
            try:
                ndex.get_networksets_for_user_id('foo', limit=3.5)
                self.fail('Expected NDExInvalidParameterError')
            except NDExInvalidParameterError as ne:
                self.assertTrue('limit parameter must be of type '
                                'int ' in str(ne))

    def test_get_networksets_for_user_invalid_offset_type(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            ndex = Ndex2()

            # try where limit is not int or str
            try:
                ndex.get_networksets_for_user_id('foo', offset=3.5)
                self.fail('Expected NDExInvalidParameterError')
            except NDExInvalidParameterError as ne:
                self.assertTrue('offset parameter must be of type '
                                'int ' in str(ne))

    def test_get_networksets_for_user_invalid_offset(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            ndex = Ndex2()

            # try where limit is not int or str
            try:
                ndex.get_networksets_for_user_id('foo', offset=5)
                self.fail('Expected NDExInvalidParameterError')
            except NDExInvalidParameterError as ne:
                self.assertTrue('limit (0) parameter must be set to '
                                'positive ' in str(ne))

    def test_get_networksets_for_user_success(self):
        with requests_mock.mock() as m:
            resurl = client.DEFAULT_SERVER + '/v2/user/foo/networksets'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.get(resurl, json={'hi': 'there'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2()

            res = ndex.get_networksets_for_user_id('foo',
                                                   summary_only=False,
                                                   showcase=True)
            self.assertEqual('there', res['hi'])

    def test_get_networksets_for_user_httperror(self):
        with requests_mock.mock() as m:
            resurl = client.DEFAULT_SERVER + '/v2/user/foo/networksets'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.get(resurl, status_code=404)
            ndex = Ndex2()

            try:
                ndex.get_networksets_for_user_id('foo')
            except NDExNotFoundError as ne:
                self.assertEqual('Caught 404 from server: ', str(ne))

    def test_get_networksets_for_user_exception(self):
        with requests_mock.mock() as m:
            resurl = client.DEFAULT_SERVER + '/v2/user/foo/networksets'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.get(resurl,
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2()

            try:
                ndex.get_networksets_for_user_id('foo')
            except NDExError as ne:
                self.assertTrue('Caught JSONDecodeError: ' in str(ne))

    def test_save_new_network_none_as_cx(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            ndex = Ndex2()
            try:
                ndex.save_new_network(None)
                self.fail('expected NDExInvalidCXError')
            except NDExInvalidCXError as ice:
                self.assertEqual(str(ice), 'CX is None')

    def test_save_new_network_invalid_as_cx(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            ndex = Ndex2()
            try:
                ndex.save_new_network('hi')
                self.fail('expected NDExInvalidCXError')
            except NDExInvalidCXError as ice:
                self.assertEqual(str(ice), 'CX is not a list')

    def test_save_new_network_empty_cx(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            ndex = Ndex2()
            try:
                ndex.save_new_network([])
                self.fail('expected NDExInvalidCXError')
            except NDExInvalidCXError as ice:
                self.assertEqual(str(ice), 'CX appears to be empty')

    def test_save_new_network_cx_with_no_status(self):
        with requests_mock.mock() as m:
            resurl = client.DEFAULT_SERVER + '/v2/network/asdf'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.post(client.DEFAULT_SERVER + '/v2/network',
                   request_headers={'Connection': 'close'},
                   status_code=1,
                   text=resurl)
            ndex = Ndex2(username='bob', password='warnerbrandis')
            res = ndex.save_new_network([{'foo': '123'}])
            self.assertEqual(res, resurl)
            decode_txt = m.last_request.text.read().decode('UTF-8')
            self.assertTrue('Content-Disposition: form-data; '
                            'name="CXNetworkStream"; '
                            'filename="filename"' in decode_txt)
            self.assertTrue('Content-Type: application/'
                            'octet-stream' in decode_txt)
            self.assertTrue('{"foo": "123"}' in decode_txt)
            self.assertTrue('{"status": [{"' in decode_txt)
            self.assertTrue('"error": ""' in decode_txt)
            self.assertTrue('"success": true' in decode_txt)

    def test_save_new_network_cx_with_no_status_ndexv1(self):
        with requests_mock.mock() as m:
            resurl = client.DEFAULT_SERVER + '/rest/network/asdf'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict(version=None))
            m.post(client.DEFAULT_SERVER + '/rest/network/asCX',
                   request_headers={'Connection': 'close'},
                   status_code=1,
                   text=resurl)
            ndex = Ndex2(username='bob', password='warnerbrandis')
            res = ndex.save_new_network([{'foo': '123'}])
            self.assertEqual(res, resurl)
            decode_txt = m.last_request.text.read().decode('UTF-8')
            self.assertTrue('Content-Disposition: form-data; '
                            'name="CXNetworkStream"; '
                            'filename="filename"' in decode_txt)
            self.assertTrue('Content-Type: application/'
                            'octet-stream' in decode_txt)
            self.assertTrue('{"foo": "123"}' in decode_txt)
            self.assertTrue('{"status": [{"' in decode_txt)
            self.assertTrue('"error": ""' in decode_txt)
            self.assertTrue('"success": true' in decode_txt)

    def test_save_new_network_cx_with_emptystatus_and_publicvisibility(self):
        with requests_mock.mock() as m:
            resurl = client.DEFAULT_SERVER + '/v2/network/asdf'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.post(client.DEFAULT_SERVER + '/v2/network?visibility=PUBLIC',
                   request_headers={'Connection': 'close'},
                   status_code=1,
                   text=resurl)
            ndex = Ndex2(username='bob', password='warnerbrandis')
            res = ndex.save_new_network([{'foo': '123'},
                                         {"status": []}],
                                        visibility='PUBLIC')
            self.assertEqual(res, resurl)
            decode_txt = m.last_request.text.read().decode('UTF-8')
            self.assertTrue('Content-Disposition: form-data; '
                            'name="CXNetworkStream"; '
                            'filename="filename"' in decode_txt)
            self.assertTrue('Content-Type: application/'
                            'octet-stream' in decode_txt)
            self.assertTrue('{"foo": "123"}' in decode_txt)
            self.assertTrue('{"status": [{"' in decode_txt)
            self.assertTrue('"error": ""' in decode_txt)
            self.assertTrue('"success": true' in decode_txt)

    def test_save_new_network_cx_with_status(self):
        with requests_mock.mock() as m:
            resurl = client.DEFAULT_SERVER + '/v2/network/asdf'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.post(client.DEFAULT_SERVER + '/v2/network',
                   request_headers={'Connection': 'close'},
                   status_code=1,
                   text=resurl)
            ndex = Ndex2(username='bob', password='warnerbrandis')
            res = ndex.save_new_network([{'foo': '123'},
                                         {"status": [{"error": "",
                                                      "success": True}]}])
            self.assertEqual(res, resurl)
            decode_txt = m.last_request.text.read().decode('UTF-8')
            self.assertTrue('Content-Disposition: '
                            'form-data; name="CXNetworkStream"; '
                            'filename="filename"' in decode_txt)
            self.assertTrue('Content-Type: application/'
                            'octet-stream' in decode_txt)
            self.assertTrue('{"foo": "123"}' in decode_txt)
            self.assertTrue('{"status": [{"' in decode_txt)
            self.assertTrue('"error": ""' in decode_txt)
            self.assertTrue('"success": true' in decode_txt)

    def test_save_new_cx2_network_none_as_cx(self):
        ndex = Ndex2(skip_version_check=True)
        try:
            ndex.save_new_cx2_network(None)
            self.fail('expected NDExInvalidCXError')
        except NDExInvalidCXError as ice:
            self.assertEqual(str(ice), 'CX is None')

    def test_save_new_cx2_network_invalid_as_cx(self):
        ndex = Ndex2(skip_version_check=True)
        try:
            ndex.save_new_cx2_network('hi')
            self.fail('expected NDExInvalidCXError')
        except NDExInvalidCXError as ice:
            self.assertEqual(str(ice), 'CX is not a list')

    def test_save_new_cx2_network_empty_cx(self):
        ndex = Ndex2(skip_version_check=True)
        try:
            ndex.save_new_cx2_network([])
            self.fail('expected NDExInvalidCXError')
        except NDExInvalidCXError as ice:
            self.assertEqual(str(ice), 'CX appears to be empty')

    def test_save_new_cx2_network_with_no_location_in_header(self):
        with requests_mock.mock() as m:
            resurl = client.DEFAULT_SERVER + '/v3/networks/asdf'
            m.post(client.DEFAULT_SERVER + '/v3/networks',
                   request_headers={'Connection': 'close'},
                   status_code=1,
                   text=resurl)
            ndex = Ndex2(username='bob', password='warnerbrandis',
                         skip_version_check=True)
            try:
                ndex.save_new_cx2_network([{'foo': '123'}])
                self.fail('Expected Exception')
            except NDExError as ne:
                self.assertTrue('Unable to get URL for newly' in str(ne))

    def test_save_new_cx2_network_with_server_error(self):
        with requests_mock.mock() as m:
            resurl = client.DEFAULT_SERVER + '/v3/networks/asdf'
            m.post(client.DEFAULT_SERVER + '/v3/networks',
                   request_headers={'Connection': 'close'},
                   json={'error': 'bad'},
                   status_code=500)
            ndex = Ndex2(username='bob', password='warnerbrandis',
                         skip_version_check=True)
            try:
                ndex.save_new_cx2_network([{'foo': '123'}],
                                          visibility='PUBLIC')
                self.fail('Expected Exception')
            except NDExError as ne:
                self.assertEqual('Caught 500 from server: '
                                 '{"error": "bad"}', str(ne))

    def test_save_new_cx2_network_with_visibility(self):
        with requests_mock.mock() as m:
            resurl = client.DEFAULT_SERVER + '/v3/networks/asdf'
            m.post(client.DEFAULT_SERVER + '/v3/networks?visibility=PUBLIC',
                   request_headers={'Connection': 'close'},
                   headers={'Location': resurl},
                   status_code=202)
            ndex = Ndex2(username='bob', password='warnerbrandis',
                         skip_version_check=True)
            res = ndex.save_new_cx2_network([{'foo': '123'}],
                                            visibility='PUBLIC')
            self.assertEqual(res, resurl)
            decode_txt = m.last_request.text.read().decode('UTF-8')
            self.assertTrue('Content-Disposition: form-data; '
                            'name="CXNetworkStream"; '
                            'filename="filename"' in decode_txt)
            self.assertTrue('Content-Type: application/'
                            'octet-stream' in decode_txt)
            self.assertTrue('{"foo": "123"}' in decode_txt)

    def test_save_new_cx2_network_with_nourl(self):
        with requests_mock.mock() as m:
            m.post(client.DEFAULT_SERVER + '/v3/networks',
                   request_headers={'Connection': 'close'},
                   status_code=202)
            ndex = Ndex2(username='bob', password='warnerbrandis',
                         skip_version_check=True)
            try:
                ndex.save_new_cx2_network([{'foo': '123'}])
                self.fail('Expected Exception')
            except NDExError as ne:
                self.assertTrue('Unable to get URL for newly '
                                'created network' in str(ne))

    def test_update_cx_network_success(self):
        with requests_mock.mock() as m:
            resurl = client.DEFAULT_SERVER + '/v2/network/asdf'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.put(client.DEFAULT_SERVER + '/v2/network/someid',
                  request_headers={'Connection': 'close'},
                  status_code=1,
                  text=resurl)
            ndex = Ndex2(username='bob', password='warnerbrandis')
            cx = [{'foo': '123'},
                  {"status": [{"error": "", "success": True}]}]

            if sys.version_info.major == 3:
                stream = io.BytesIO(json.dumps(cx,
                                               cls=DecimalEncoder)
                                    .encode('utf-8'))
            else:
                stream = io.BytesIO(json.dumps(cx, cls=DecimalEncoder))
            res = ndex.update_cx_network(stream, 'someid')
            self.assertEqual(res, resurl)
            decode_txt = m.last_request.text.read().decode('UTF-8')
            self.assertTrue('Content-Disposition: form-data; '
                            'name="CXNetworkStream"; '
                            'filename="filename"' in decode_txt)
            self.assertTrue('Content-Type: application/'
                            'octet-stream' in decode_txt)
            self.assertTrue('{"foo": "123"}' in decode_txt)
            self.assertTrue('{"status": [{"' in decode_txt)
            self.assertTrue('"error": ""' in decode_txt)
            self.assertTrue('"success": true' in decode_txt)

    def test_update_cx_network_success_ndexv1(self):
        with requests_mock.mock() as m:
            resurl = client.DEFAULT_SERVER + '/rest/network/asdf'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict(version=None))
            m.put(client.DEFAULT_SERVER + '/rest/network/asCX/someid',
                  request_headers={'Connection': 'close'},
                  status_code=1,
                  text=resurl)
            ndex = Ndex2(username='bob', password='warnerbrandis')
            cx = [{'foo': '123'},
                  {"status": [{"error": "", "success": True}]}]

            if sys.version_info.major == 3:
                stream = io.BytesIO(json.dumps(cx,
                                               cls=DecimalEncoder)
                                    .encode('utf-8'))
            else:
                stream = io.BytesIO(json.dumps(cx, cls=DecimalEncoder))
            res = ndex.update_cx_network(stream, 'someid')
            self.assertEqual(res, resurl)
            decode_txt = m.last_request.text.read().decode('UTF-8')
            self.assertTrue('Content-Disposition: form-data; '
                            'name="CXNetworkStream"; '
                            'filename="filename"' in decode_txt)
            self.assertTrue('Content-Type: application/'
                            'octet-stream' in decode_txt)
            self.assertTrue('{"foo": "123"}' in decode_txt)
            self.assertTrue('{"status": [{"' in decode_txt)
            self.assertTrue('"error": ""' in decode_txt)
            self.assertTrue('"success": true' in decode_txt)

    def test_update_cx2_network_success(self):
        with requests_mock.mock() as m:

            m.put(client.DEFAULT_SERVER + '/v3/networks/someid',
                  request_headers={'Connection': 'close'},
                  status_code=200)
            ndex = Ndex2(username='bob', password='warnerbrandis',
                         skip_version_check=True)
            cx = [{'foo': '123'},
                  {"status": [{"error": "", "success": True}]}]

            if sys.version_info.major == 3:
                stream = io.BytesIO(json.dumps(cx,
                                               cls=DecimalEncoder)
                                    .encode('utf-8'))
            else:
                stream = io.BytesIO(json.dumps(cx, cls=DecimalEncoder))

            ndex.update_cx2_network(stream, 'someid')

            decode_txt = m.last_request.text.read().decode('UTF-8')
            self.assertTrue('Content-Disposition: form-data; '
                            'name="CXNetworkStream"; '
                            'filename="filename"' in decode_txt)
            self.assertTrue('Content-Type: application/'
                            'octet-stream' in decode_txt)
            self.assertTrue('{"foo": "123"}' in decode_txt)
            self.assertTrue('{"status": [{"' in decode_txt)
            self.assertTrue('"error": ""' in decode_txt)
            self.assertTrue('"success": true' in decode_txt)

    def test_update_cx2_network_server_error(self):
        with requests_mock.mock() as m:

            m.put(client.DEFAULT_SERVER + '/v3/networks/someid',
                  request_headers={'Connection': 'close'},
                  json={'error': 'bad'},
                  status_code=500)
            ndex = Ndex2(username='bob', password='warnerbrandis',
                         skip_version_check=True)
            cx = [{'foo': '123'},
                  {"status": [{"error": "", "success": True}]}]

            if sys.version_info.major == 3:
                stream = io.BytesIO(json.dumps(cx,
                                               cls=DecimalEncoder)
                                    .encode('utf-8'))
            else:
                stream = io.BytesIO(json.dumps(cx, cls=DecimalEncoder))

            try:
                ndex.update_cx2_network(stream, 'someid')
                self.fail('Expected exception')
            except NDExError as ne:
                self.assertEqual('Caught 500 from server: '
                                 '{"error": "bad"}', str(ne))

    def test_update_cx2_network_other_error(self):
        with requests_mock.mock() as m:

            m.put(client.DEFAULT_SERVER + '/v3/networks/someid',
                  request_headers={'Connection': 'close'},
                  json={'error': 'bad'},
                  status_code=500)
            ndex = Ndex2(username='bob', password='warnerbrandis',
                         skip_version_check=True)
            ndex.host = None
            cx = [{'foo': '123'},
                  {"status": [{"error": "", "success": True}]}]

            if sys.version_info.major == 3:
                stream = io.BytesIO(json.dumps(cx,
                                               cls=DecimalEncoder)
                                    .encode('utf-8'))
            else:
                stream = io.BytesIO(json.dumps(cx, cls=DecimalEncoder))

            try:
                ndex.update_cx2_network(stream, 'someid')
                self.fail('Expected exception')
            except NDExError as ne:
                self.assertTrue('Caught TypeError' in str(ne))

    def test_validate_network_system_properties(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            ndex = Ndex2()

            # try passing none
            try:
                ndex._validate_network_system_properties(None)
                self.fail('Expected exception')
            except NDExInvalidParameterError as ne:
                self.assertEqual('network_properties must be a '
                                 'string or a dict', str(ne))

            # try passing empty string
            try:
                ndex._validate_network_system_properties('')
                self.fail('Expected exception')
            except NDExInvalidParameterError as ne:
                self.assertTrue('Error parsing json string' in str(ne))

            # try passing empty dict
            try:
                ndex._validate_network_system_properties({})
                self.fail('Expected exception')
            except NDExInvalidParameterError as ne:
                self.assertTrue('network_properties appears to '
                                'be empty' in str(ne))

            # try passing invalid property
            try:
                ndex._validate_network_system_properties({'showcase': True,
                                                          'foo': 'blah'})
                self.fail('Expected exception')
            except NDExInvalidParameterError as ne:
                self.assertEqual('foo is not a valid network system '
                                 'property', str(ne))

            # try passing invalid readOnly property
            try:
                ndex._validate_network_system_properties({'showcase': True,
                                                          'readOnly': 'blah'})
                self.fail('Expected exception')
            except NDExInvalidParameterError as ne:
                self.assertEqual('readOnly value must be a bool '
                                 'set to True or False', str(ne))

            # try passing invalid showcase property
            try:
                ndex._validate_network_system_properties({'showcase': 'haha'})
                self.fail('Expected exception')
            except NDExInvalidParameterError as ne:
                self.assertEqual('showcase value must be a bool '
                                 'set to True or False', str(ne))

            # try passing invalid index_level property as bool
            try:
                ndex._validate_network_system_properties({'index_level':
                                                          False})
                self.fail('Expected exception')
            except NDExInvalidParameterError as ne:
                self.assertEqual('index_level value must be '
                                 'a string set to NONE, META, or ALL', str(ne))

            # try passing invalid index_level property
            try:
                ndex._validate_network_system_properties({'index_level':
                                                          'blah'})
                self.fail('Expected exception')
            except NDExInvalidParameterError as ne:
                self.assertEqual('index_level value must be '
                                 'a string set to NONE, META, or ALL', str(ne))

            # try passing invalid visibility property bool
            try:
                ndex._validate_network_system_properties({'visibility': True})
                self.fail('Expected exception')
            except NDExInvalidParameterError as ne:
                self.assertEqual('visibility value must be '
                                 'a string set to PUBLIC or PRIVATE',
                                 str(ne))

            # try passing invalid visibility property
            try:
                ndex._validate_network_system_properties({'visibility':
                                                          'ha'})
                self.fail('Expected exception')
            except NDExInvalidParameterError as ne:
                self.assertEqual('visibility value must be '
                                 'a string set to PUBLIC or PRIVATE',
                                 str(ne))

            # try passing valid dict
            valid_dict = {'showcase': True,
                          'visibility': 'PUBLIC',
                          'index_level': 'ALL',
                          'readOnly': True}
            res = ndex._validate_network_system_properties(valid_dict)

            check_dict = json.loads(res)
            self.assertEqual(valid_dict, check_dict)

            # try passing dict with validation off
            res = ndex._validate_network_system_properties({},
                                                           skipvalidation=True)
            self.assertEqual('{}', res)

    def test_set_network_system_properties_test_no_auth(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            ndex = Ndex2()
            try:
                ndex.set_network_system_properties('236ecfce-be48-4652-'
                                                   'b488-b08f0cc9c795',
                                                   {'visibility': 'PUBLIC'})
                self.fail('Expected exception')
            except NDExUnauthorizedError as ne:
                self.assertEqual('This method requires user '
                                 'authentication', str(ne))

    def test_set_network_system_properties_invalid_propertytype(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            ndex = Ndex2(username='bob', password='warnerbrandis')
            try:
                ndex.set_network_system_properties('236ecfce-be48-4652-b488-'
                                                   'b08f0cc9c795',
                                                   True)
                self.fail('Expected exception')
            except NDExInvalidParameterError as ne:
                self.assertEqual('network_properties '
                                 'must be a string or a dict', str(ne))

    def test_set_network_system_properties_ndexv1(self):
        theuuid = '236ecfce-be48-4652-b488-b08f0cc9c795'
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict(version=None))

            ndex = Ndex2(username='bob', password='warnerbrandis')

            valid_dict = {'showcase': True,
                          'visibility': 'PUBLIC',
                          'index_level': 'ALL',
                          'readOnly': True}
            try:
                ndex.set_network_system_properties(theuuid,
                                                   valid_dict)
                self.fail('Expected NDExUnsupportedCallError')
            except NDExUnsupportedCallError as ne:
                self.assertEqual('This call only works with NDEx 2+',
                                 str(ne))

    def test_set_network_system_properties_success(self):
        theuuid = '236ecfce-be48-4652-b488-b08f0cc9c795'
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.put(client.DEFAULT_SERVER + '/v2/network/' +
                  theuuid + '/systemproperty',
                  request_headers={'Content-Type': 'application/json;'
                                                   'charset=UTF-8',
                                   'Accept': 'application/json',
                                   'User-Agent': client.userAgent},
                  headers={'Content-Type': 'application/foo'},
                  status_code=200,
                  text='')
            ndex = Ndex2(username='bob', password='warnerbrandis')

            valid_dict = {'showcase': True,
                          'visibility': 'PUBLIC',
                          'index_level': 'ALL',
                          'readOnly': True}
            res = ndex.set_network_system_properties(theuuid,
                                                     valid_dict)
            self.assertEqual('', res)
            checkdict = json.loads(m.last_request.text)
            self.assertEqual(valid_dict, checkdict)

    def test_make_network_public_noauth(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            ndex = Ndex2()
            try:
                ndex.make_network_public('236ecfce-be48-4652-b488-'
                                         'b08f0cc9c795')
                self.fail('Expected exception')
            except NDExUnauthorizedError as ne:
                self.assertEqual('This method requires user authentication',
                                 str(ne))

    def test_make_network_public_success(self):
        theuuid = '236ecfce-be48-4652-b488-b08f0cc9c795'
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.put(client.DEFAULT_SERVER + '/v2/network/' +
                  theuuid + '/systemproperty',
                  request_headers={'Content-Type': 'application/json;'
                                                   'charset=UTF-8',
                                   'Accept': 'application/json',
                                   'User-Agent': client.userAgent},
                  headers={'Content-Type': 'application/foo'},
                  status_code=200,
                  text='')
            ndex = Ndex2(username='bob', password='warnerbrandis')
            res = ndex.make_network_public(theuuid)
            self.assertEqual('', res)
            checkdict = json.loads(m.last_request.text)
            self.assertEqual({'visibility': 'PUBLIC'}, checkdict)

    def test_make_network_private_noauth(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            ndex = Ndex2()
            try:
                ndex.make_network_private('236ecfce-be48-4652-b488-'
                                          'b08f0cc9c795')
                self.fail('Expected exception')
            except NDExUnauthorizedError as ne:
                self.assertEqual('This method requires user authentication',
                                 str(ne))

    def test_make_network_private_success(self):
        theuuid = '236ecfce-be48-4652-b488-b08f0cc9c795'
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.put(client.DEFAULT_SERVER + '/v2/network/' +
                  theuuid + '/systemproperty',
                  request_headers={'Content-Type': 'application/json;'
                                                   'charset=UTF-8',
                                   'Accept': 'application/json',
                                   'User-Agent': client.userAgent},
                  headers={'Content-Type': 'application/foo'},
                  status_code=200,
                  text='')
            ndex = Ndex2(username='bob', password='warnerbrandis')
            res = ndex.make_network_private(theuuid)
            self.assertEqual('', res)
            checkdict = json.loads(m.last_request.text)
            self.assertEqual({'visibility': 'PRIVATE'}, checkdict)

    def test_make_network_public_indexed_noauth(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            ndex = Ndex2()
            try:
                ndex._make_network_public_indexed('236ecfce-be48-4652-'
                                                  'b488-b08f0cc9c795')
                self.fail('Expected exception')
            except NDExUnauthorizedError as ne:
                self.assertEqual('This method requires user authentication',
                                 str(ne))

    def test_make_network_public_indexed_success(self):
        theuuid = '236ecfce-be48-4652-b488-b08f0cc9c795'
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.put(client.DEFAULT_SERVER + '/v2/network/' +
                  theuuid + '/systemproperty',
                  request_headers={'Content-Type': 'application/json;'
                                                   'charset=UTF-8',
                                   'Accept': 'application/json',
                                   'User-Agent': client.userAgent},
                  headers={'Content-Type': 'application/foo'},
                  status_code=200,
                  text='')
            ndex = Ndex2(username='bob', password='warnerbrandis')
            res = ndex._make_network_public_indexed(theuuid)
            self.assertEqual('', res)
            checkdict = json.loads(m.last_request.text)
            self.assertEqual({'visibility': 'PUBLIC',
                              'index_level': 'ALL',
                              'showcase': True}, checkdict)

    def test_make_network_public_indexed_ndexv1(self):
        theuuid = '236ecfce-be48-4652-b488-b08f0cc9c795'
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict(version=None))

            ndex = Ndex2(username='bob', password='warnerbrandis')
            try:
                ndex._make_network_public_indexed(theuuid)
                self.fail('Expected NDExUnsupportedCallError')
            except NDExUnsupportedCallError as ne:
                self.assertEqual('Only 2+ of NDEx supports '
                                 'setting/changing index level', str(ne))

    def test_set_read_only_noauth(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            ndex = Ndex2()
            try:
                ndex.set_read_only('236ecfce-be48-4652-b488-b08f0cc9c795',
                                   True)
                self.fail('Expected exception')
            except NDExUnauthorizedError as ne:
                self.assertEqual('This method requires user authentication',
                                 str(ne))

    def test_set_read_only_true_success(self):
        theuuid = '236ecfce-be48-4652-b488-b08f0cc9c795'
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.put(client.DEFAULT_SERVER + '/v2/network/' +
                  theuuid + '/systemproperty',
                  request_headers={'Content-Type': 'application/json;'
                                                   'charset=UTF-8',
                                   'Accept': 'application/json',
                                   'User-Agent': client.userAgent},
                  headers={'Content-Type': 'application/foo'},
                  status_code=200,
                  text='')
            ndex = Ndex2(username='bob', password='warnerbrandis')
            res = ndex.set_read_only(theuuid, True)
            self.assertEqual('', res)
            checkdict = json.loads(m.last_request.text)
            self.assertEqual({'readOnly': True}, checkdict)

    def test_set_read_only_false_success(self):
        theuuid = '236ecfce-be48-4652-b488-b08f0cc9c795'
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.put(client.DEFAULT_SERVER + '/v2/network/' +
                  theuuid + '/systemproperty',
                  request_headers={'Content-Type': 'application/json;'
                                                   'charset=UTF-8',
                                   'Accept': 'application/json',
                                   'User-Agent': client.userAgent},
                  headers={'Content-Type': 'application/foo'},
                  status_code=200,
                  text='')
            ndex = Ndex2(username='bob', password='warnerbrandis')
            res = ndex.set_read_only(theuuid, False)
            self.assertEqual('', res)
            checkdict = json.loads(m.last_request.text)
            self.assertEqual({'readOnly': False}, checkdict)

    def test_get_network_as_cx_stream_success(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.get(client.DEFAULT_SERVER + '/v2/network/someid',
                  status_code=200,
                  json={'hi': 'bye'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.get_network_as_cx_stream('someid')
            self.assertEqual(res.json(), {'hi': 'bye'})
            self.assertEqual(res.status_code, 200)

    def test_get_network_as_cx_stream_success_ndexv1(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict(version=None))
            m.get(client.DEFAULT_SERVER + '/rest/network/someid/asCX',
                  status_code=200,
                  json={'hi': 'bye'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.get_network_as_cx_stream('someid')
            self.assertEqual(res.json(), {'hi': 'bye'})
            self.assertEqual(res.status_code, 200)

    def test_get_network_aspect_as_cx_stream_success(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.get(client.DEFAULT_SERVER + '/v2/network/someid/aspect/sa',
                  status_code=200,
                  json={'hi': 'bye'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.get_network_aspect_as_cx_stream('someid', 'sa')
            self.assertEqual(res.json(), {'hi': 'bye'})
            self.assertEqual(res.status_code, 200)

    def test_get_network_aspect_as_cx_stream_success_ndexv1(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict(version=None))
            m.get(client.DEFAULT_SERVER + '/rest/network/someid/asCX',
                  status_code=200,
                  json={'hi': 'bye'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.get_network_aspect_as_cx_stream('someid', 'sa')
            self.assertEqual(res.json(), {'hi': 'bye'})
            self.assertEqual(res.status_code, 200)

    def test_get_network_aspect_as_cx2_stream_success(self):
        with requests_mock.mock() as m:
            m.get(client.DEFAULT_SERVER + '/v3/networks/someid/aspects/sa',
                  status_code=200,
                  json={'hi': 'bye'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2(skip_version_check=True)
            ndex.set_debug_mode(True)
            res = ndex.get_network_aspect_as_cx2_stream('someid',
                                                        aspect_name='sa')
            self.assertEqual(res.json(), {'hi': 'bye'})
            self.assertEqual(res.status_code, 200)

    def test_get_network_aspect_as_cx2_stream_success_with_size(self):
        with requests_mock.mock() as m:
            m.get(client.DEFAULT_SERVER + '/v3/networks/someid/'
                                          'aspects/sa?size=4',
                  status_code=200,
                  json={'hi': 'bye'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2(skip_version_check=True)
            ndex.set_debug_mode(True)
            res = ndex.get_network_aspect_as_cx2_stream('someid',
                                                        aspect_name='sa',
                                                        size=4)
            self.assertEqual(res.json(), {'hi': 'bye'})
            self.assertEqual(res.status_code, 200)

    def test_get_network_aspect_as_cx2_stream_success_with_size_access(self):
        with requests_mock.mock() as m:
            m.get(client.DEFAULT_SERVER + '/v3/networks/someid/'
                                          'aspects/sa?accesskey=key&size=4',
                  status_code=200,
                  json={'hi': 'bye'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2(skip_version_check=True)
            ndex.set_debug_mode(True)
            res = ndex.get_network_aspect_as_cx2_stream('someid',
                                                        aspect_name='sa',
                                                        access_key='key',
                                                        size=4)
            self.assertEqual(res.json(), {'hi': 'bye'})
            self.assertEqual(res.status_code, 200)

    def test_get_network_aspect_as_cx2_stream_error(self):
        with requests_mock.mock() as m:
            m.get(client.DEFAULT_SERVER + '/v3/networks/someid/aspects/sa',
                  status_code=500,
                  json={'hi': 'bye'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2(skip_version_check=True)
            ndex.set_debug_mode(True)
            try:
                ndex.get_network_aspect_as_cx2_stream('someid',
                                                      aspect_name='sa')
                self.fail('Expected exception')
            except NDExError as ne:
                self.assertEqual('Caught 500 from server: {"hi": "bye"}',
                                 str(ne))

    def test_get_network_aspect_as_cx2_stream_low_level_error(self):
        with requests_mock.mock() as m:
            m.get(client.DEFAULT_SERVER + '/v3/networks/someid/aspects/sa',
                  status_code=200,
                  json={'error': 'bye'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2(skip_version_check=True)
            ndex.set_debug_mode(True)
            ndex.host = None
            try:
                ndex.get_network_aspect_as_cx2_stream('someid',
                                                      aspect_name='sa')
                self.fail('Expected exception')
            except NDExError as ne:
                self.assertTrue('Caught TypeError:' in str(ne))

    def test_get_network_as_cx2_stream_error(self):
        with requests_mock.mock() as m:
            m.get(client.DEFAULT_SERVER + '/v3/networks/someid',
                  status_code=500,
                  json={'error': 'bye'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2(skip_version_check=True)
            ndex.set_debug_mode(True)
            try:
                ndex.get_network_as_cx2_stream('someid')
                self.fail('Expected exception')
            except NDExError as ne:
                self.assertEqual(str(ne),
                                 'Caught 500 from server: {"error": "bye"}')

    def test_get_network_as_cx2_stream_low_level_error(self):
        with requests_mock.mock() as m:
            m.get(client.DEFAULT_SERVER + '/v3/networks/someid',
                  status_code=200,
                  json={'error': 'bye'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2(skip_version_check=True)
            ndex.set_debug_mode(True)

            # here we do a hack break by setting host to
            # None which will cause a TypeError
            ndex.host = None
            try:
                ndex.get_network_as_cx2_stream('someid')
                self.fail('Expected exception')
            except NDExError as ne:
                self.assertEqual(str(ne),
                                 'Caught TypeError: unsupported operand type(s) '
                                 'for +: \'NoneType\' and \'str\'')

    def test_get_network_as_cx2_stream_success(self):
        with requests_mock.mock() as m:
            m.get(client.DEFAULT_SERVER + '/v3/networks/someid',
                  status_code=200,
                  json={'hi': 'bye'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2(skip_version_check=True)
            ndex.set_debug_mode(True)
            res = ndex.get_network_as_cx2_stream('someid')
            self.assertEqual(res.json(), {'hi': 'bye'})
            self.assertEqual(res.status_code, 200)

    def test_get_network_as_cx2_stream_w_access_key_success(self):
        with requests_mock.mock() as m:
            a_key = 'b4487036-84cb-4764-b058-a2abeb034b76'
            m.get(client.DEFAULT_SERVER +
                  '/v3/networks/someid?accesskey=' + a_key,
                  status_code=200,
                  json={'hi': 'bye'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2(skip_version_check=True)
            ndex.set_debug_mode(True)
            res = ndex.get_network_as_cx2_stream('someid', access_key=a_key)
            self.assertEqual(res.json(), {'hi': 'bye'})
            self.assertEqual(res.status_code, 200)

    def test_get_neighborhood_as_cx_stream(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.post(client.DEFAULT_SERVER + '/v2/search/network/someid/query',
                   status_code=200,
                   json={'hi': 'bye'},
                   request_headers={'Connection': 'close'},
                   headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.get_neighborhood_as_cx_stream('someid',
                                                     'query')
            self.assertEqual(res.json(), {'hi': 'bye'})
            self.assertEqual(res.status_code, 200)

    def test_get_neighborhood_as_cx_stream_ndexv1(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict(version=None))
            m.post(client.DEFAULT_SERVER + '/rest/network/someid/query',
                   status_code=200,
                   json={'hi': 'bye'},
                   request_headers={'Connection': 'close'},
                   headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.get_neighborhood_as_cx_stream('someid',
                                                     'query')
            self.assertEqual(res.json(), {'hi': 'bye'})
            self.assertEqual(res.status_code, 200)

    def test_get_neighborhood(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.post(client.DEFAULT_SERVER + '/v2/search/network/someid/query',
                   status_code=200,
                   json={'data': [{'hi': 'bye'}]},
                   request_headers={'Connection': 'close'},
                   headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.get_neighborhood('someid', 'query')
            self.assertEqual(res, [{'hi': 'bye'}])

    def test_get_neighborhood_list_return(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.post(client.DEFAULT_SERVER + '/v2/search/network/someid/query',
                   status_code=200,
                   json=[{'hi': 'bye'}],
                   request_headers={'Connection': 'close'},
                   headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.get_neighborhood('someid', 'query')
            self.assertEqual(res, [{'hi': 'bye'}])

    def test_get_neighborhood_str_return(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.post(client.DEFAULT_SERVER + '/v2/search/network/someid/query',
                   status_code=200,
                   json='blah',
                   request_headers={'Connection': 'close'},
                   headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.get_neighborhood('someid', 'query')
            self.assertEqual(res, 'blah')

    def test_get_neighborhood_ndexv1(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict(version=None))

            ndex = Ndex2()
            ndex.set_debug_mode(True)
            try:
                ndex.get_neighborhood('someid', 'query')
                self.fail('Expected Exception')
            except Exception as e:
                self.assertEqual('get_neighborhood is not supported for '
                                 'versions prior to 2.0, use '
                                 'get_neighborhood_as_cx_stream', str(e))

    def test_upload_file(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            ndex = Ndex2()
            try:
                ndex.upload_file('foo')
                self.fail('Expected NDExError')
            except NDExError:
                pass

    def test_get_interconnectquery_as_cx_stream(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.post(client.DEFAULT_SERVER +
                   '/v2/search/network/someid/interconnectquery',
                   status_code=200,
                   json={'hi': 'bye'},
                   request_headers={'Connection': 'close'},
                   headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.get_interconnectquery_as_cx_stream('someid',
                                                          'query')
            self.assertEqual(res.json(), {'hi': 'bye'})
            self.assertEqual(res.status_code, 200)

    def test_get_interconnectquery(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.post(client.DEFAULT_SERVER +
                   '/v2/search/network/someid/interconnectquery',
                   status_code=200,
                   json={'data': [{'hi': 'bye'}]},
                   request_headers={'Connection': 'close'},
                   headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.get_interconnectquery('someid', 'query')
            self.assertEqual(res, [{'hi': 'bye'}])

    def test_get_interconnectquery_as_list(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.post(client.DEFAULT_SERVER +
                   '/v2/search/network/someid/interconnectquery',
                   status_code=200,
                   json=[{'hi': 'bye'}],
                   request_headers={'Connection': 'close'},
                   headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.get_interconnectquery('someid', 'query')
            self.assertEqual(res, [{'hi': 'bye'}])

    def test_get_interconnectquery_as_str(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.post(client.DEFAULT_SERVER +
                   '/v2/search/network/someid/interconnectquery',
                   status_code=200,
                   json='foo',
                   request_headers={'Connection': 'close'},
                   headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.get_interconnectquery('someid', 'query')
            self.assertEqual(res, 'foo')

    def test_search_networks(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.post(client.DEFAULT_SERVER +
                   '/v2/search/network?start=0&size=100',
                   status_code=200,
                   json={'hi': 'bye'},
                   headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.search_networks(search_string='hi',
                                       account_name='bob',
                                       include_groups=True)
            self.assertEqual(res, {'hi': 'bye'})

    def test_search_networks_ndexv1(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict(version=None))
            m.post(client.DEFAULT_SERVER + '/rest/network/search/0/100',
                   status_code=200,
                   json={'hi': 'bye'},
                   headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.search_networks(search_string='hi',
                                       account_name='bob',
                                       include_groups=True)
            self.assertEqual(res, {'hi': 'bye'})

    def test_search_networks_by_property_filter(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            ndex = Ndex2()
            try:
                ndex.search_networks_by_property_filter()
                self.fail('Expected Exception')
            except Exception:
                pass

    def test_get_network_summary(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.get(client.DEFAULT_SERVER + '/v2/network/someid/summary',
                  status_code=200,
                  json={'hi': 'bye'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.get_network_summary('someid')
            self.assertEqual(res, {'hi': 'bye'})

    def test_get_network_summary_ndexv1(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict(version=None))
            m.get(client.DEFAULT_SERVER + '/rest/network/someid',
                  status_code=200,
                  json={'hi': 'bye'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.get_network_summary('someid')
            self.assertEqual(res, {'hi': 'bye'})

    def test_delete_networkset_none_passed_in(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())

            ndex = Ndex2()
            ndex.set_debug_mode(True)
            try:
                ndex.delete_networkset(None)
                self.fail('Expected exception')
            except NDExInvalidParameterError as ne:
                self.assertEqual('networkset id cannot be None',
                                 str(ne))

    def test_delete_networkset_non_string_passed_in(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())

            ndex = Ndex2()
            ndex.set_debug_mode(True)
            try:
                ndex.delete_networkset(True)
                self.fail('Expected exception')
            except NDExInvalidParameterError as ne:
                self.assertEqual('networkset id must be a string',
                                 str(ne))

    def test_delete_networkset_not_authorized(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())

            ndex = Ndex2()
            try:
                ndex.delete_networkset('someid')
                self.fail('Expected exception')
            except NDExUnauthorizedError as ne:
                self.assertEqual('This method requires user authentication',
                                 str(ne))

    def test_delete_networkset_success(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.delete(client.DEFAULT_SERVER + '/v2/networkset/someid',
                     status_code=204,
                     headers={'Content-Type': 'application/json'})
            ndex = Ndex2(username='bob', password='warnerbrandis')
            self.assertEqual(None, ndex.delete_networkset('someid'))

    def test_delete_networkset_server_says_not_authorized(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.delete(client.DEFAULT_SERVER + '/v2/networkset/someid',
                     status_code=401,
                     headers={'Content-Type': 'application/json'})
            ndex = Ndex2(username='bob', password='warnerbrandis')
            try:
                ndex.delete_networkset('someid')
                self.fail('Expected exception')
            except NDExUnauthorizedError as ne:
                self.assertEqual('Not authorized', str(ne))

    def test_delete_networkset_server_says_not_found(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.delete(client.DEFAULT_SERVER + '/v2/networkset/someid',
                     status_code=404,
                     headers={'Content-Type': 'application/json'})
            ndex = Ndex2(username='bob', password='warnerbrandis')
            try:
                ndex.delete_networkset('someid')
                self.fail('Expected exception')
            except NDExNotFoundError as ne:
                self.assertEqual('Network set with id: someid not found',
                                 str(ne))

    def test_delete_networkset_server_500_error_no_json(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.delete(client.DEFAULT_SERVER + '/v2/networkset/someid',
                     status_code=500,
                     headers={'Content-Type': 'application/json'})
            ndex = Ndex2(username='bob', password='warnerbrandis')
            try:
                ndex.delete_networkset('someid')
                self.fail('Expected exception')
            except NDExError as ne:
                self.assertEqual('Unknown error server returned '
                                 'status code: 500',
                                 str(ne))

    def test_delete_networkset_server_503_with_json(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.delete(client.DEFAULT_SERVER + '/v2/networkset/someid',
                     status_code=503,
                     json={"errorCode": "string",
                           "message": "string",
                           "description": "string",
                           "stackTrace": "string",
                           "threadId": "string",
                           "timeStamp": "2019-09-09T16:36:25.699Z"},
                     headers={'Content-Type': 'application/json'})
            ndex = Ndex2(username='bob', password='warnerbrandis')
            try:
                ndex.delete_networkset('someid')
                self.fail('Expected exception')
            except NDExError as ne:
                self.assertTrue('Unknown error server returned '
                                'status code: 503 : ' in str(ne))

    def test_get_task_by_id_no_auth(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            ndex = Ndex2()
            try:
                ndex.get_task_by_id('someid')
                self.fail('Expected Exception')
            except NDExUnauthorizedError:
                pass

    def test_get_task_by_id_success(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.get(client.DEFAULT_SERVER + '/v2/task/someid',
                  status_code=200,
                  json={'hi': 'bye'},
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2(username='bob', password='warnerbrandis')
            res = ndex.get_task_by_id('someid')
            self.assertEqual('bye', res['hi'])

    def test_add_networks_to_networkset(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.post(client.DEFAULT_SERVER + '/v2/networkset/aid/members',
                  status_code=200,
                  json='',
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2(username='bob', password='warnerbrandis')
            res = ndex.add_networks_to_networkset('aid', ['someid'])
            self.assertEqual('', res)

    def test_get_network_ids_for_user_invalid_offset_limit(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())

            ndex = Ndex2()
            try:
                ndex.get_network_ids_for_user('bob', limit=None, offset=5)
                self.fail('Expected NDExInvalidParameterError')
            except NDExInvalidParameterError as ne:
                self.assertEqual('Limit must be set to a positive '
                                 'number to use offset', str(ne))

            # try where limit is str and offset is None
            try:
                ndex.get_network_ids_for_user('bob', limit='ha', offset=None)
                self.fail('Expected NDExInvalidParameterError')
            except NDExInvalidParameterError as ne:
                self.assertEqual('Limit must be an int', str(ne))

            # try where limit is str and offset is str
            try:
                ndex.get_network_ids_for_user('bob', offset='3')
                self.fail('Expected NDExInvalidParameterError')
            except NDExInvalidParameterError as ne:
                self.assertEqual('Offset must be an int', str(ne))

    def test_get_network_ids_for_user_success_no_ids(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            resurl = client.DEFAULT_SERVER + '/v2/user?username=bob'
            m.get(resurl, json={'externalId': '12345'},
                  headers={'Content-Type': 'application/json'})
            resurl = client.DEFAULT_SERVER + '/v2/user/12345/networksummary?offset=0&limit=1000'
            m.get(resurl,
                  json=[],
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            res = ndex.get_network_ids_for_user('bob')
            self.assertEqual([], res)

    def test_get_network_ids_for_user_success_with_ids(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            resurl = client.DEFAULT_SERVER + '/v2/user?username=bob'
            m.get(resurl, json={'externalId': '12345'},
                  headers={'Content-Type': 'application/json'})
            resurl = client.DEFAULT_SERVER + '/v2/user/12345/networksummary?offset=0&limit=1000'
            m.get(resurl,
                  json=[{'externalId': '1'}, {'externalId': '2'}],
                  headers={'Content-Type': 'application/json'})
            ndex = Ndex2()
            res = ndex.get_network_ids_for_user('bob')
            self.assertEqual(2, len(res))
            self.assertTrue('1' in res)
            self.assertTrue('2' in res)


