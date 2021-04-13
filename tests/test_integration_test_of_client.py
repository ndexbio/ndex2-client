# -*- coding: utf-8 -*-

"""Integration/acceptance tests for `ndex2.client` package."""

import os
import re
import sys
import io
import time
import unittest
import json
import uuid
from datetime import datetime
import requests

from requests.exceptions import HTTPError
import ndex2
from ndex2.nice_cx_network import NiceCXNetwork
from ndex2.client import Ndex2
from ndex2.client import DecimalEncoder
from ndex2.exceptions import NDExUnauthorizedError

SKIP_REASON = 'NDEX2_TEST_SERVER, NDEX2_TEST_USER, NDEX2_TEST_PASS ' \
              'environment variables not set, cannot run integration' \
              ' tests with server'


@unittest.skipUnless(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestClient(unittest.TestCase):

    TEST_DIR = os.path.dirname(__file__)
    WNT_SIGNAL_FILE = os.path.join(TEST_DIR, 'data', 'wntsignaling.cx')
    GLYPICAN2_FILE = os.path.join(TEST_DIR, 'data', 'glypican2.cx')

    def get_ndex2_client(self):
        return Ndex2(os.getenv('NDEX2_TEST_SERVER'),
                     os.getenv('NDEX2_TEST_USER'),
                     os.getenv('NDEX2_TEST_PASS'),
                     debug=True,
                     user_agent='ndex2-client integration test')

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

    def test_update_network(self):
        client = self.get_ndex2_client()
        # create network and add it
        net = NiceCXNetwork()
        oneid = net.create_node('node1')
        twoid = net.create_node('node2')
        net.create_edge(oneid, twoid, 'hello')
        netname = 'ndex2-client integration test network' + str(datetime.now())
        net.set_name(netname)
        res = client.save_new_network(net.to_cx(), visibility='PRIVATE')
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

            net.create_node(node_name='hello', node_represents='something')
            net.create_node(node_name='hoho', node_represents='heheh')
            newnetname = 'update ' + netname
            self.assertEqual(4, len(net.get_nodes()))
            net.set_name(newnetname)
            if sys.version_info.major == 3:
                stream = io.BytesIO(json.dumps(net.to_cx(),
                                               cls=DecimalEncoder)
                                    .encode('utf-8'))
            else:
                stream = io.BytesIO(json.dumps(net.to_cx(),
                                               cls=DecimalEncoder))
            newres = client.update_cx_network(stream, netid)
            self.assertEqual('', newres)
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
            self.assertEqual(4, netsum['nodeCount'])
            self.assertEqual(False, netsum['isShowcase'])
            self.assertEqual('NONE', netsum['indexLevel'])
        finally:
            pass
            client.delete_network(netid)
            try:
                client.get_network_as_cx_stream(netid)
                self.fail('Expected exception')
            except HTTPError:
                pass

    def test_network_permissions(self):
        client = self.get_ndex2_client()
        # create network and add it
        net = ndex2.create_nice_cx_from_file(TestClient.GLYPICAN2_FILE)
        netname = 'ndex2-client integration test network' + str(datetime.now())
        net.set_name(netname)
        res = client.save_new_network(net.to_cx(), visibility='PUBLIC')
        try:
            self.assertTrue('http' in res)
            netid = re.sub('^.*/', '', res)

            # verify network was uploaded
            netsum = self.wait_for_network_to_be_ready(client, netid)
            self.assertIsNotNone(netsum, 'Network is still not ready,'
                                         ' maybe server is busy?')
            self.assertEqual(netid, netsum['externalId'])
            self.assertTrue('name' in netsum, str(netsum))
            self.assertEqual(netname, netsum['name'], str(netsum))
            self.assertEqual('PUBLIC', netsum['visibility'])
            self.assertEqual(False, netsum['isReadOnly'])
            self.assertEqual(1, netsum['edgeCount'])
            self.assertEqual(2, netsum['nodeCount'])
            self.assertEqual(False, netsum['isShowcase'])
            self.assertEqual('NONE', netsum['indexLevel'])

            # make network private
            self.assertEqual('', client.make_network_private(netid))
            netsum = client.get_network_summary(network_id=netid)
            self.assertEqual('PRIVATE', netsum['visibility'])

            # make network public
            self.assertEqual('', client.make_network_public(netid))
            netsum = client.get_network_summary(network_id=netid)
            self.assertEqual('PUBLIC', netsum['visibility'])

            # make network readonly
            self.assertEqual('', client.set_read_only(netid, True))
            netsum = client.get_network_summary(network_id=netid)
            self.assertEqual(True, netsum['isReadOnly'])

            self.assertEqual('', client.set_read_only(netid, False))
            netsum = client.get_network_summary(network_id=netid)
            self.assertEqual(False, netsum['isReadOnly'])

            # make network indexed and showcased
            netperm = {'index_level': 'ALL',
                       'showcase': True}
            self.assertEqual('', client.set_network_system_properties(netid,
                                                                      netperm))
            netsum = client.get_network_summary(network_id=netid)
            self.assertEqual(True, netsum['isShowcase'])
            self.assertEqual('ALL', netsum['indexLevel'])

            netperm = {'index_level': 'META',
                       'showcase': False}
            self.assertEqual('', client.set_network_system_properties(netid,
                                                                      netperm))
            netsum = client.get_network_summary(network_id=netid)
            self.assertEqual(False, netsum['isShowcase'])
            self.assertEqual('META', netsum['indexLevel'])
        finally:
            # delete network
            client.delete_network(netid)

    def test_deletenetworkset_nonexistant(self):
        client = self.get_ndex2_client()
        invalidnetworksetid = str(uuid.uuid4())
        try:
            client.delete_networkset(invalidnetworksetid)
            self.fail('Expected NDExNotFoundError')
        except NDExUnauthorizedError as ne:
            self.assertEqual('Not authorized', str(ne))

    def test_networksets(self):
        client = self.get_ndex2_client()

        # create networkset
        netsetname = 'testnetworkset: ' + str(datetime.now())
        res = client.create_networkset(netsetname, 'some description')
        self.assertTrue('http' in res)
        netset_id = re.sub('^.*/', '', res)

        net = ndex2.create_nice_cx_from_file(TestClient.GLYPICAN2_FILE)
        netname = 'ndex2-client integration test network' + str(datetime.now())
        net.set_name(netname)
        res = client.save_new_network(net.to_cx(), visibility='PUBLIC')
        net_id = re.sub('^.*/', '', res)
        try:
            # get the networkset back
            res = client.get_network_set(netset_id)
            self.assertEqual('some description', res['description'])
            self.assertEqual(netsetname, res['name'])
            self.assertEqual(False, res['showcased'])
            self.assertEqual(netset_id, res['externalId'])
            self.assertEqual([], res['networks'])

            # add network to networkset
            client.add_networks_to_networkset(netset_id, [net_id])
            res = client.get_network_set(netset_id)
            self.assertEqual([net_id], res['networks'])

            # remove network from networkset
            client.delete_networks_from_networkset(netset_id, [net_id])
            res = client.get_network_set(netset_id)
            self.assertEqual([], res['networks'])
        finally:
            # delete the network
            client.delete_network(net_id)

            # delete the networkset
            res = client.delete_networkset(netset_id)
            self.assertEqual(None, res)
            try:
                client.get_network_set(netset_id)
                self.fail('Expected Exception')
            except HTTPError:
                pass

    def test_get_user_by_username(self):
        client = self.get_ndex2_client()
        theuser = os.getenv('NDEX2_TEST_USER')
        res = client.get_user_by_username(theuser)
        self.assertEqual(theuser, res['userName'])
        self.assertTrue('externalId' in res)

    def test_set_network_properties(self):
        client = self.get_ndex2_client()
        # create network and add it
        net = ndex2.create_nice_cx_from_file(TestClient.GLYPICAN2_FILE)
        netname = 'ndex2-client integration test network2' + str(datetime.now())
        net.set_name(netname)
        res = client.save_new_network(net.to_cx(), visibility='PUBLIC')
        try:
            self.assertTrue('http' in res)
            netid = re.sub('^.*/', '', res)

            # verify network was uploaded
            netsum = self.wait_for_network_to_be_ready(client, netid)
            self.assertIsNotNone(netsum, 'Network is still not ready,'
                                         ' maybe server is busy?')
            self.assertEqual(netid, netsum['externalId'])
            self.assertTrue('name' in netsum, str(netsum))

            # get all network attributes
            res = client.get_network_aspect_as_cx_stream(netid, 'networkAttributes')
            net_attrs = res.json()

            # Versions of NDEx server pre 2.5.1 will add a new description attribute
            # but it is a duplicate
            netprops = [{'subNetworkId': '',
                         'predicateString': 'fookey',
                         'dataType': 'string',
                         'value': 'foo'}]
            res = client.set_network_properties(netid, network_properties=netprops)
            self.assertTrue(str(res) == '' or str(res) == '1')

            updated_net_attrs = client.get_network_aspect_as_cx_stream(netid,
                                                                       'networkAttributes')
            res_attrs = updated_net_attrs.json()
            found_fookey = False
            found_name = False
            for attr in res_attrs:
                if attr['n'] == 'fookey':
                    self.assertEqual('foo', attr['v'])
                    found_fookey = True
                if attr['n'] == 'name':
                    self.assertEqual(netname, attr['v'])
                    found_name = True
            self.assertTrue(found_fookey)
            self.assertTrue(found_name)
        finally:
            # delete network
            client.delete_network(netid)
