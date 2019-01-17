#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `nbgwas_rest` package."""


import decimal
import unittest
import numpy as np

import requests
import requests_mock

from ndex2 import client
from ndex2.client import Ndex2
from ndex2.client import DecimalEncoder


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
            res = dec.default(1)
            self.fail('Expected exception')
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

        # try with user, pass and user_agent set oh and host
        # with extra text prepended to localhost
        ndex = Ndex2(host='xxxlocalhost', username='bob',
                     password='smith', user_agent='yo', debug=True)
        self.assertEqual(ndex.debug, True)
        self.assertEqual(ndex.version, 1.3)
        self.assertEqual(ndex.status, {})
        self.assertEqual(ndex.username, 'bob')
        self.assertEqual(ndex.password, 'smith')
        self.assertEqual(ndex.user_agent, ' yo')
        self.assertEqual(ndex.host, 'http://localhost:8080/ndexbio-rest')
        self.assertTrue(ndex.s is not None)

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
            ndex.require_auth()
            self.fail('Expected exception')
        except Exception as e:
            self.assertEqual(str(e),
                             'this method requires user authentication')

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
                  headers={'content-type': 'application/foo'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.put('/hi')
            self.assertEqual(res, 'hehe')

    def test_ndex2_put_with_json_and_json_resp(self):
        with requests_mock.mock() as m:
            m.get(self.get_rest_admin_status_url(),
                  json=self.get_rest_admin_status_dict())
            m.put(client.DEFAULT_SERVER + '/v2/hi',
                  status_code=200,
                  json={'hi': 'bye'},
                  headers={'content-type': 'application/json'})
            ndex = Ndex2()
            ndex.set_debug_mode(True)
            res = ndex.put('/hi', put_json='{"x": "y"}')
            self.assertEqual(res, {'hi': 'bye'})
