#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `nbgwas_rest` package."""

import sys
import decimal
import unittest
import numpy as np

import requests_mock
from requests.exceptions import HTTPError
from ndex2 import client
from ndex2.client import Ndex2
from ndex2.client import DecimalEncoder
from ndex2 import __version__
from ndex2.exceptions import NDExInvalidCXError


class TestClient(unittest.TestCase):

    def get_rest_admin_status_dict(self):
        return {"networkCount": 1321,
                "userCount": 12,
                "groupCount": 0,
                "message": "Online",
                "properties": {"ServerVersion": "2.1",
                               "ServerResultLimit": "10000"}}

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
        self.assertEqual(ndex.version, 1.3)
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
        self.assertEqual(ndex.version, 1.3)
        self.assertEqual(ndex.status, {})
        self.assertEqual(ndex.username, 'bob')
        self.assertEqual(ndex.password, 'smith')
        self.assertEqual(ndex.user_agent, ' yo')
        self.assertEqual(ndex.host, 'http://localhost:8080/ndexbio-rest')
        self.assertTrue(ndex.s is not None)
        self.assertTrue(ndex.timeout, 1)

        # try with user_agent set to None Issue #34
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
            self.assertEqual(ndex.host, client.DEFAULT_SERVER + '/rest')
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
            self.assertEqual(ndex.host, client.DEFAULT_SERVER + '/rest')
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
            self.assertEqual(ndex.host, client.DEFAULT_SERVER + '/rest')
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
                ndex = Ndex2()
                self.fail('Expected exception')
            except Exception as e:
                self.assertEqual(str(e), 'This release only supports NDEx 2.x server.')

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
            self.assertEqual(ndex.host, client.DEFAULT_SERVER + '/v2')
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
                  request_headers={'Content-Type': 'application/json;charset=UTF-8',
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
                  request_headers={'Content-Type': 'application/json;charset=UTF-8',
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
                  request_headers={'Content-Type': 'application/json;charset=UTF-8',
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
            m.post(client.DEFAULT_SERVER + '/v2/network/asCX',
                   request_headers={'Connection': 'close'},
                   status_code=1,
                   text=resurl)
            ndex = Ndex2(username='bob', password='warnerbrandis')
            res = ndex.save_new_network([{'foo': '123'}])
            self.assertEqual(res, resurl)
            decode_txt = m.last_request.text.read().decode('UTF-8')
            self.assertTrue('Content-Disposition: form-data; name="CXNetworkStream"; filename="filename"' in decode_txt)
            self.assertTrue('Content-Type: application/octet-stream' in decode_txt)
            self.assertTrue('{"foo": "123"}' in decode_txt)
            self.assertTrue('{"status": [{"' in decode_txt)
            self.assertTrue('"error": ""' in decode_txt)
            self.assertTrue('"success": true' in decode_txt)

    def test_save_new_network_cx_with_emptystatus_and_publicvisibility(self):
        with requests_mock.mock() as m:
            resurl = client.DEFAULT_SERVER + '/v2/network/asdf'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.post(client.DEFAULT_SERVER + '/v2/network/asCX?visibility=PUBLIC',
                   request_headers={'Connection': 'close'},
                   status_code=1,
                   text=resurl)
            ndex = Ndex2(username='bob', password='warnerbrandis')
            res = ndex.save_new_network([{'foo': '123'},
                                         {"status": []}],
                                        visibility='PUBLIC')
            self.assertEqual(res, resurl)
            decode_txt = m.last_request.text.read().decode('UTF-8')
            self.assertTrue('Content-Disposition: form-data; name="CXNetworkStream"; filename="filename"' in decode_txt)
            self.assertTrue('Content-Type: application/octet-stream' in decode_txt)
            self.assertTrue('{"foo": "123"}' in decode_txt)
            self.assertTrue('{"status": [{"' in decode_txt)
            self.assertTrue('"error": ""' in decode_txt)
            self.assertTrue('"success": true' in decode_txt)

    def test_save_new_network_cx_with_status(self):
        with requests_mock.mock() as m:
            resurl = client.DEFAULT_SERVER + '/v2/network/asdf'
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.post(client.DEFAULT_SERVER + '/v2/network/asCX',
                   request_headers={'Connection': 'close'},
                   status_code=1,
                   text=resurl)
            ndex = Ndex2(username='bob', password='warnerbrandis')
            res = ndex.save_new_network([{'foo': '123'},
                                         {"status": [{"error": "", "success": True}]}])
            self.assertEqual(res, resurl)
            decode_txt = m.last_request.text.read().decode('UTF-8')
            self.assertTrue('Content-Disposition: form-data; name="CXNetworkStream"; filename="filename"' in decode_txt)
            self.assertTrue('Content-Type: application/octet-stream' in decode_txt)
            self.assertTrue('{"foo": "123"}' in decode_txt)
            self.assertTrue('{"status": [{"' in decode_txt)
            self.assertTrue('"error": ""' in decode_txt)
            self.assertTrue('"success": true' in decode_txt)
