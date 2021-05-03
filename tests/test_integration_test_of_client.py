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
from ndex2.exceptions import NDExNotFoundError
from ndex2.exceptions import NDExError

SKIP_REASON = 'NDEX2_TEST_SERVER, NDEX2_TEST_USER, NDEX2_TEST_PASS ' \
              'environment variables not set, cannot run integration' \
              ' tests with server'


@unittest.skipUnless(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestClientIntegration(unittest.TestCase):

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
                                     num_retries=3, retry_wait=0.5):
        retrycount = 1
        while retrycount < num_retries:
            netsum = client.get_network_summary(network_id=netid)
            if netsum['completed'] is True:
                return netsum
            retrycount += 1
            time.sleep(retry_wait)
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
                                                       retry_wait=1)
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
        net = ndex2.create_nice_cx_from_file(TestClientIntegration.GLYPICAN2_FILE)
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

        net = ndex2.create_nice_cx_from_file(TestClientIntegration.GLYPICAN2_FILE)
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

    def test_get_networksets_for_user_invalid_user(self):
        client = self.get_ndex2_client()
        nonexistant_user = str(uuid.uuid4())
        res = client.get_networksets_for_user_id(nonexistant_user)
        self.assertEqual([], res)

    def test_get_networksets_for_user_empty_networkset(self):
        client = self.get_ndex2_client()

        try:
            user_id = client.get_id_for_user(None)
            # get all the networksets for the user whose
            # credentials were used to connect to NDEx
            # with all default parameters
            res = client.get_networksets_for_user_id(user_id)

            num_networksets_existing = len(res)

            # now lets add a networkset and run query several
            # times to make sure we get it back correctly
            netsetname = 'testnetworkset1: ' + str(datetime.now())
            netset_desc = '1st networkset'
            res = client.create_networkset(netsetname, netset_desc)
            self.assertTrue('http' in res)
            netset_id = re.sub('^.*/', '', res)

            res = client.get_networksets_for_user_id(user_id)
            self.assertEqual(num_networksets_existing+1, len(res))
            found_netset = False
            for netset in res:
                if netset['name'] == netsetname:
                    matching_netset = netset
                    found_netset = True

            self.assertTrue(found_netset)
            self.assertEqual(netset_desc, matching_netset['description'])
            self.assertEqual(user_id,
                             matching_netset['ownerId'])
            self.assertEqual(False, matching_netset['showcased'])
            self.assertEqual(False, matching_netset['isDeleted'])
            self.assertEqual({}, matching_netset['properties'])

            # query again this time with summary_only set to False
            # and set the username
            res = client.get_networksets_for_user_id(user_id,
                                                     summary_only=False,
                                                     showcase=False)
            self.assertEqual(num_networksets_existing + 1, len(res))
            found_netset = False
            counter = 0
            for netset in res:
                if netset['name'] == netsetname:
                    matching_netset = netset
                    found_netset = True
                    break
                counter += 1

            self.assertTrue(found_netset)
            self.assertEqual(netset_desc, matching_netset['description'])
            self.assertEqual(user_id,
                             matching_netset['ownerId'])
            self.assertEqual(False, matching_netset['showcased'])
            self.assertEqual(False, matching_netset['isDeleted'])
            self.assertEqual({}, matching_netset['properties'])

            # try limit and offset set to 0
            res = client.get_networksets_for_user_id(user_id,
                                                     summary_only=False,
                                                     showcase=False,
                                                     offset=0,
                                                     limit=0)
            self.assertEqual(num_networksets_existing+1, len(res))

            # try limit=1 and offset set to 0
            res = client.get_networksets_for_user_id(user_id,
                                                     summary_only=False,
                                                     showcase=False,
                                                     offset=counter,
                                                     limit=1)
            self.assertEqual(1, len(res))
            matching_netset = res[0]
            self.assertEqual(netset_desc, matching_netset['description'])
            self.assertEqual(user_id,
                             matching_netset['ownerId'])
            self.assertEqual(False, matching_netset['showcased'])
            self.assertEqual(False, matching_netset['isDeleted'])
            self.assertEqual({}, matching_netset['properties'])
        finally:
            # delete networkset
            res = client.delete_networkset(netset_id)
            self.assertEqual(None, res)

            # verify networkset is not there
            try:
                client.get_network_set(netset_id)
                self.fail('Expected Exception')
            except HTTPError:
                pass

            # and verify it is not returned when looking for all
            # networksets
            res = client.get_networksets_for_user_id(user_id)
            self.assertEqual(num_networksets_existing, len(res))

    def test_get_networksets_for_user_full_networkset(self):
        client = self.get_ndex2_client()
        creds = self.get_ndex_credentials_as_tuple()
        net_one_id = None
        net_two_id = None
        try:
            user_id = client.get_id_for_user(None)

            # now lets add a networkset
            netsetname = 'testnetworkset1: ' + str(datetime.now())
            netset_desc = '1st networkset'
            res = client.create_networkset(netsetname, netset_desc)
            self.assertTrue('http' in res)
            netset_id = re.sub('^.*/', '', res)

            # add a couple networks to networkset
            net_one = ndex2.create_nice_cx_from_file(TestClientIntegration.GLYPICAN2_FILE)
            net_one_name = 'ndex2-client integration test network' + str(datetime.now())
            net_one.set_name(net_one_name)
            res = client.save_new_network(net_one.to_cx(), visibility='PUBLIC')
            self.assertTrue('http' in res)
            net_one_id = re.sub('^.*/', '', res)

            net_two = ndex2.create_nice_cx_from_file(TestClientIntegration.GLYPICAN2_FILE)
            net_two_name = 'ndex2-client integration test network 2 ' + str(datetime.now())
            net_two.set_name(net_two_name)
            res = client.save_new_network(net_two.to_cx(), visibility='PUBLIC')
            self.assertTrue('http' in res)
            net_two_id = re.sub('^.*/', '', res)

            client.add_networks_to_networkset(netset_id,
                                              [net_one_id, net_two_id])

            res = client.get_networksets_for_user_id(user_id)
            found_netset = False
            counter = 0
            for netset in res:
                if netset['name'] == netsetname:
                    matching_netset = netset
                    found_netset = True
                    break
                counter += 1

            self.assertTrue(found_netset)
            self.assertEqual(netset_desc, matching_netset['description'])
            self.assertTrue('networks' not in matching_netset)
            res = client.get_networksets_for_user_id(user_id,
                                                     summary_only=False,
                                                     offset=counter, limit=1)
            matching_netset = res[0]
            self.assertTrue(2, len(matching_netset['networks']))
            self.assertTrue(net_one_id in matching_netset['networks'])
            self.assertTrue(net_two_id in matching_netset['networks'])

        finally:
            # delete networks
            if net_one_id is not None:
                res = client.delete_network(net_one_id)
                self.assertEqual('', res)
            if net_two_id is not None:
                res = client.delete_network(net_two_id)
                self.assertEqual('', res)

            # delete networkset
            res = client.delete_networkset(netset_id)
            self.assertEqual(None, res)

            # verify networkset is not there
            try:
                client.get_network_set(netset_id)
                self.fail('Expected Exception')
            except HTTPError:
                pass

    def test_get_user_by_username(self):
        client = self.get_ndex2_client()
        creds = self.get_ndex_credentials_as_tuple()
        theuser = creds['user']
        res = client.get_user_by_username(theuser)
        self.assertEqual(theuser, res['userName'])
        self.assertTrue('externalId' in res)

    def test_get_id_for_user(self):
        client = self.get_ndex2_client()
        creds = self.get_ndex_credentials_as_tuple()

        # try with user used in connection
        user_id = client.get_id_for_user(None)
        # compare with value from get_user_by_username
        user_json = client.get_user_by_username(creds['user'])
        self.assertEqual(user_json['externalId'], user_id)

        bad_user_id = str(uuid.uuid4())
        # try with user that does not exist
        try:
            client.get_id_for_user(bad_user_id)
            self.fail('Expected NDExNotFoundError')
        except NDExNotFoundError as e:
            self.assertTrue('Caught 404 from server:' in str(e))

    def test_get_user_by_id(self):
        client = self.get_ndex2_client()

        # try with current user
        user_id = client.get_id_for_user(None)
        self.assertTrue(user_id is not None)

        user_json = client.get_user_by_id(user_id)
        self.assertEqual(user_id, user_json['externalId'])

        # compare with user json from get_user_by_name()
        alt_user_json = client.get_user_by_username(user_json['userName'])
        prop_list = ['isIndividual', 'userName', 'isVerified',
                     'firstName', 'lastName', 'emailAddress', 'diskQuota',
                     'externalId', 'isDeleted', 'creationTime']
        # there is also modificationTime, and diskUsed, but those
        # might change as test is running so will skip for now
        for prop in prop_list:
            self.assertEqual(user_json[prop],
                             alt_user_json[prop])

        bad_user_id = str(uuid.uuid4())
        # try with user that does not exist
        try:
            client.get_user_by_id(bad_user_id)
            self.fail('Expected NDExNotFoundError')
        except NDExNotFoundError as e:
            self.assertTrue('Caught 404 from server:' in str(e))

    def test_set_network_properties(self):
        client = self.get_ndex2_client()
        # create network and add it
        net = ndex2.create_nice_cx_from_file(TestClientIntegration.GLYPICAN2_FILE)
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

    def test_get_network_ids_for_user(self):
        client = self.get_ndex2_client()
        creds = self.get_ndex_credentials_as_tuple()
        netid_one = None
        netid_two = None
        try:
            # query for networks for user in creds
            network_ids = client.get_network_ids_for_user(creds['user'])
            num_network_ids = len(network_ids)
            self.assertTrue(num_network_ids >= 0)

            # set offset to number of network ids and limit 1
            network_ids = client.get_network_ids_for_user(creds['user'],
                                                          offset=num_network_ids,
                                                          limit=1)
            self.assertTrue(len(network_ids) == 0)

            # add two networks just in case there are none and verify
            # they are returned
            net = ndex2.create_nice_cx_from_file(TestClientIntegration.GLYPICAN2_FILE)
            netname = 'ndex2-client integration test network1' + str(datetime.now())
            net.set_name(netname)
            res = client.save_new_network(net.to_cx(), visibility='PUBLIC')
            self.assertTrue('http' in res)
            netid_one = re.sub('^.*/', '', res)
            # verify network was uploaded
            netsum = self.wait_for_network_to_be_ready(client, netid_one)
            self.assertEqual(netid_one, netsum['externalId'])

            net.set_name('ndex2-client integration test network2' + str(datetime.now()))
            res = client.save_new_network(net.to_cx(), visibility='PUBLIC')
            self.assertTrue('http' in res)
            netid_two = re.sub('^.*/', '', res)
            # verify network was uploaded
            netsum = self.wait_for_network_to_be_ready(client, netid_two)
            self.assertEqual(netid_two, netsum['externalId'])

            network_ids = client.get_network_ids_for_user(creds['user'],
                                                          limit=num_network_ids+5)

            self.assertTrue(netid_one in network_ids)
            self.assertTrue(netid_two in network_ids)
            self.assertEqual(num_network_ids+2, len(network_ids))

            network_ids = client.get_network_ids_for_user(creds['user'],
                                                          offset=num_network_ids+1,
                                                          limit=5)
            self.assertTrue(len(network_ids) == 1)
        finally:
            if netid_one is not None:
                client.delete_network(netid_one)
            if netid_two is not None:
                client.delete_network(netid_two)

