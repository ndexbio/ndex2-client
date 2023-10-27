# -*- coding: utf-8 -*-

"""Integration/acceptance tests for `ndex2.nice_cx_network` package."""

import os
import re
import sys
import io
import time
import unittest
import json
import uuid
from datetime import datetime

from requests.exceptions import HTTPError
from ndex2.exceptions import NDExError
from ndex2.exceptions import NDExNotFoundError
from ndex2.exceptions import NDExUnauthorizedError
from ndex2.client import Ndex2
from ndex2.cx2 import CX2Network
from ndex2.nice_cx_network import NiceCXNetwork
from ndex2.client import DecimalEncoder
import ndex2

SKIP_REASON = 'NDEX2_TEST_SERVER, NDEX2_TEST_USER, NDEX2_TEST_PASS ' \
              'environment variables not set, cannot run integration' \
              ' tests with server'


@unittest.skipUnless(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestNiceCXNetworkIntegration(unittest.TestCase):

    TEST_DIR = os.path.dirname(__file__)
    WNT_SIGNAL_FILE = os.path.join(TEST_DIR, 'data', 'wntsignaling.cx')
    GLYPICAN2_FILE = os.path.join(TEST_DIR, 'data', 'glypican2.cx')

    def get_ndex_credentials_as_tuple(self):
        """
        Gets ndex user credentials as tuple

        :return: {'server': SERVER, 'user': USER,
                  'password': PASS, 'user_agent': USER_AGENT}
        :rtype: dict
        """
        return {'server': os.getenv('NDEX2_TEST_SERVER'),
                'user': os.getenv('NDEX2_TEST_USER'),
                'password': os.getenv('NDEX2_TEST_PASS'),
                'user_agent': 'ndex2-client integration test'}

    def get_ndex2_client(self):
        creds = self.get_ndex_credentials_as_tuple()
        return Ndex2(creds['server'],
                     creds['user'],
                     creds['password'],
                     debug=True,
                     user_agent=creds['user_agent'])

    def wait_for_network_to_be_ready(self, client, netid,
                                     num_retries=3, retry_weight=0.5):
        retrycount = 1
        while retrycount < num_retries:
            netsum = client.get_network_summary(network_id=netid)
            if netsum['completed'] is True:
                return netsum
            retrycount += 1
            time.sleep(retry_weight)
        return None

    def test_update_network_with_client(self):
        client = self.get_ndex2_client()
        # create network and add it
        net = CX2Network()
        net.add_node(0, attributes={'name': 'node0'})
        net.add_node(1, attributes={'name': 'node1'})
        net.add_edge(0, source=0, target=1, attributes={'foo': 1})
        netname = 'CX2Network test network' + str(datetime.now())
        net.set_network_attributes({'name': netname,
                                    'description': 'Created by test_update_network_with_client() in '
                                                   'test_integration_cx2network.py integration test in ndex2-client'})
        res = client.save_new_cx2_network(net.to_cx2())
        try:
            self.assertTrue('http' in res)
            netid = re.sub('^.*/', '', res)
            netsum = self.wait_for_network_to_be_ready(client, netid)
            self.assertIsNotNone(netsum, 'Network is still not ready,'
                                         ' maybe server is busy?')
            self.assertEqual(netid, netsum['externalId'])
            self.assertTrue('name' in netsum, msg=str(netsum))
            self.assertEqual(netname, netsum['name'], str(netsum))
            self.assertEqual('PRIVATE', netsum['visibility'])
            self.assertEqual(False, netsum['isReadOnly'])
            self.assertEqual(1, netsum['edgeCount'])
            self.assertEqual(2, netsum['nodeCount'])
            self.assertEqual(False, netsum['isShowcase'])
            self.assertEqual('NONE', netsum['indexLevel'])

            net.add_node(2, attributes={'name': 'node2'})
            cur_net_attrs = net.get_network_attributes()
            newnetname = 'update via update_cx2_network() ' + netname
            cur_net_attrs['name'] = newnetname
            self.assertEqual(3, len(net.get_nodes()))

            cx_stream = io.BytesIO(json.dumps(net.to_cx2(),
                                              cls=DecimalEncoder).encode('utf-8'))
            client.update_cx2_network(cx_stream, netid)

            netsum = self.wait_for_network_to_be_ready(client, netid,
                                                       num_retries=5,
                                                       retry_weight=1)
            self.assertIsNotNone(netsum, 'Network is still not ready,'
                                         ' maybe server is busy?')
            self.assertEqual(netid, netsum['externalId'])
            self.assertEqual(newnetname, netsum['name'])
            self.assertEqual('PRIVATE', netsum['visibility'])
            self.assertEqual(False, netsum['isReadOnly'])
            self.assertEqual(1, netsum['edgeCount'])
            self.assertEqual(3, netsum['nodeCount'])
            self.assertEqual(False, netsum['isShowcase'])
            self.assertEqual('NONE', netsum['indexLevel'])
        finally:
            client.delete_network(netid)
            try:
                client.get_network_as_cx_stream(netid)
                self.fail('Expected exception')
            except HTTPError:
                pass

