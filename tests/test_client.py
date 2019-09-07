#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `nbgwas_rest` package."""

import sys
import io
import decimal
import unittest
import numpy as np
import json

import requests_mock
from requests.exceptions import HTTPError
from ndex2 import client
from ndex2.client import Ndex2
from ndex2.client import DecimalEncoder
from ndex2 import __version__
from ndex2.exceptions import NDExInvalidCXError
from ndex2.exceptions import NDExUnauthorizedError
from ndex2.exceptions import NDExInvalidParameterError


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
            m.post(client.DEFAULT_SERVER + '/v2/network',
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
            m.post(client.DEFAULT_SERVER + '/v2/network',
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
                stream = io.BytesIO(json.dumps(cx, cls=DecimalEncoder).encode('utf-8'))
            else:
                stream = io.BytesIO(json.dumps(cx, cls=DecimalEncoder))
            res = ndex.update_cx_network(stream, 'someid')
            self.assertEqual(res, resurl)
            decode_txt = m.last_request.text.read().decode('UTF-8')
            self.assertTrue('Content-Disposition: form-data; name="CXNetworkStream"; filename="filename"' in decode_txt)
            self.assertTrue('Content-Type: application/octet-stream' in decode_txt)
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
                stream = io.BytesIO(json.dumps(cx, cls=DecimalEncoder).encode('utf-8'))
            else:
                stream = io.BytesIO(json.dumps(cx, cls=DecimalEncoder))
            res = ndex.update_cx_network(stream, 'someid')
            self.assertEqual(res, resurl)
            decode_txt = m.last_request.text.read().decode('UTF-8')
            self.assertTrue('Content-Disposition: form-data; name="CXNetworkStream"; filename="filename"' in decode_txt)
            self.assertTrue('Content-Type: application/octet-stream' in decode_txt)
            self.assertTrue('{"foo": "123"}' in decode_txt)
            self.assertTrue('{"status": [{"' in decode_txt)
            self.assertTrue('"error": ""' in decode_txt)
            self.assertTrue('"success": true' in decode_txt)

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
                self.assertEqual('network_properties must be a string or a dict', str(ne))

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
                self.assertTrue('network_properties appears to be empty' in str(ne))

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
                ndex._validate_network_system_properties({'index_level': False})
                self.fail('Expected exception')
            except NDExInvalidParameterError as ne:
                self.assertEqual('index_level value must be '
                                 'a string set to NONE, META, or ALL', str(ne))

            # try passing invalid index_level property
            try:
                ndex._validate_network_system_properties({'index_level': 'blah'})
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
                                 'a string set to PUBLIC or PRIVATE', str(ne))

            # try passing invalid visibility property
            try:
                ndex._validate_network_system_properties({'visibility': 'ha'})
                self.fail('Expected exception')
            except NDExInvalidParameterError as ne:
                self.assertEqual('visibility value must be '
                                 'a string set to PUBLIC or PRIVATE', str(ne))

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
                ndex.set_network_system_properties('236ecfce-be48-4652-b488-b08f0cc9c795',
                                                   {'visibility': 'PUBLIC'})
                self.fail('Expected exception')
            except NDExUnauthorizedError as ne:
                self.assertEqual('This method requires user authentication', str(ne))

    def test_set_network_system_properties_invalid_propertytype(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            ndex = Ndex2(username='bob', password='warnerbrandis')
            try:
                ndex.set_network_system_properties('236ecfce-be48-4652-b488-b08f0cc9c795',
                                                   True)
                self.fail('Expected exception')
            except NDExInvalidParameterError as ne:
                self.assertEqual('network_properties '
                                 'must be a string or a dict', str(ne))

    def test_set_network_system_properties_success(self):
        theuuid = '236ecfce-be48-4652-b488-b08f0cc9c795'
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.put(client.DEFAULT_SERVER + '/v2/network/' +
                  theuuid + '/systemproperty',
                  request_headers={'Content-Type': 'application/json;charset=UTF-8',
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
                ndex.make_network_public('236ecfce-be48-4652-b488-b08f0cc9c795')
                self.fail('Expected exception')
            except NDExUnauthorizedError as ne:
                self.assertEqual('This method requires user authentication', str(ne))

    def test_make_network_public_success(self):
        theuuid = '236ecfce-be48-4652-b488-b08f0cc9c795'
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.put(client.DEFAULT_SERVER + '/v2/network/' +
                  theuuid + '/systemproperty',
                  request_headers={'Content-Type': 'application/json;charset=UTF-8',
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
                ndex.make_network_private('236ecfce-be48-4652-b488-b08f0cc9c795')
                self.fail('Expected exception')
            except NDExUnauthorizedError as ne:
                self.assertEqual('This method requires user authentication', str(ne))

    def test_make_network_private_success(self):
        theuuid = '236ecfce-be48-4652-b488-b08f0cc9c795'
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.put(client.DEFAULT_SERVER + '/v2/network/' +
                  theuuid + '/systemproperty',
                  request_headers={'Content-Type': 'application/json;charset=UTF-8',
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
                ndex._make_network_public_indexed('236ecfce-be48-4652-b488-b08f0cc9c795')
                self.fail('Expected exception')
            except NDExUnauthorizedError as ne:
                self.assertEqual('This method requires user authentication', str(ne))

    def test_make_network_public_indexed_success(self):
        theuuid = '236ecfce-be48-4652-b488-b08f0cc9c795'
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.put(client.DEFAULT_SERVER + '/v2/network/' +
                  theuuid + '/systemproperty',
                  request_headers={'Content-Type': 'application/json;charset=UTF-8',
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
                self.assertEqual('This method requires user authentication', str(ne))

    def test_set_read_only_true_success(self):
        theuuid = '236ecfce-be48-4652-b488-b08f0cc9c795'
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.put(client.DEFAULT_SERVER + '/v2/network/' +
                  theuuid + '/systemproperty',
                  request_headers={'Content-Type': 'application/json;charset=UTF-8',
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
                  request_headers={'Content-Type': 'application/json;charset=UTF-8',
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

