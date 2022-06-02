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
import math
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
    CX2_GLYPICAN2_FILE = os.path.join(TEST_DIR, 'data', 'glypican2.cx2')

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
                                     num_retries=5, retry_wait=0.5):
        retrycount = 1
        while retrycount < num_retries:
            netsum = client.get_network_summary(network_id=netid)
            if netsum['completed'] is True:
                return netsum
            retrycount += 1
            time.sleep(retry_wait)
        return None

    def check_glypican_cx2_is_correct(self, cx):
        """
        Bunch of checks to verify CX2 passed in **cx** is valid

        :param cx:
        :return:
        """
        self.assertEqual({'CXVersion': '2.0',
                          'hasFragments': False}, cx[0])
        found_aspects = set()
        for frag in cx[1:-1]:
            self.assertEqual(1, len(frag.keys()), 'expected 1 key per fragment')
            cur_aspect = list(frag.keys())[0]
            found_aspects.add(cur_aspect)

            if cur_aspect == 'metaData':
                self.assertEqual(6, len(frag[cur_aspect]))
            elif cur_aspect == 'attributeDeclarations':
                self.assertEqual(1, len(frag[cur_aspect]))
                self.assertEqual(3, len(frag[cur_aspect][0].keys()))
                self.assertTrue('nodes' in frag[cur_aspect][0])
                self.assertTrue('edges' in frag[cur_aspect][0])
                self.assertTrue('networkAttributes' in frag[cur_aspect][0])
            elif cur_aspect == 'nodes':
                self.assertEqual(2, len(frag[cur_aspect]))
                node_dict = {}
                for n in frag[cur_aspect]:
                    node_dict[n['id']] = n
                # check node with id 0
                self.assertTrue(math.fabs(node_dict[0]['x'] + 398) < 1.0)
                self.assertTrue(math.fabs(node_dict[0]['y'] - 70) < 1.0)
                self.assertEqual('MDK', node_dict[0]['v']['n'])
                self.assertEqual('uniprot knowledgebase:P21741',
                                 node_dict[0]['v']['r'])
                self.assertEqual('Protein', node_dict[0]['v']['type'])
                self.assertEqual(2, len(node_dict[0]['v']['alias']))
                self.assertTrue('uniprot knowledgebase:Q2LEK4' in node_dict[0]['v']['alias'])
                self.assertTrue('uniprot knowledgebase:Q9UCC7' in node_dict[0]['v']['alias'])

                # check node with id 1
                self.assertTrue(math.fabs(node_dict[1]['x'] + 353) < 1.0)
                self.assertTrue(math.fabs(node_dict[1]['y'] - 70) < 1.0)
                self.assertEqual('GPC2', node_dict[1]['v']['n'])
                self.assertEqual('uniprot knowledgebase:A4D2A7',
                                 node_dict[1]['v']['r'])
                self.assertEqual('Protein', node_dict[1]['v']['type'])
                self.assertEqual(1, len(node_dict[1]['v']['alias']))
                self.assertTrue('uniprot knowledgebase:Q8N158' in node_dict[1]['v']['alias'])
            elif cur_aspect == 'networkAttributes':
                self.assertEqual(1, len(frag[cur_aspect]))
                # @context aspect if found is converted to network attribute hence
                # the 9 count. This occurs in version 3.5.0 and newer
                self.assertTrue(len(frag[cur_aspect][0].keys()) == 9, frag[cur_aspect][0].keys())
            elif cur_aspect == 'edges':
                self.assertEqual(1, len(frag[cur_aspect]))
                self.assertEqual(0, frag[cur_aspect][0]['id'])
                self.assertEqual(1, frag[cur_aspect][0]['s'])
                self.assertEqual(0, frag[cur_aspect][0]['t'])
                self.assertEqual({'directed': False,
                                  'i': 'in-complex-with'},
                                 frag[cur_aspect][0]['v'])
            elif cur_aspect == 'visualEditorProperties':
                self.assertEqual(1, len(frag[cur_aspect]))
                self.assertEqual(True, frag[cur_aspect][0]['properties']['nodeSizeLocked'])
                self.assertEqual(True, frag[cur_aspect][0]['properties']['arrowColorMatchesEdge'])
                self.assertEqual(True, frag[cur_aspect][0]['properties']['nodeCustomGraphicsSizeSync'])
                self.assertEqual(0.0, frag[cur_aspect][0]['properties']['NETWORK_CENTER_Y_LOCATION'])
                self.assertEqual(0.0, frag[cur_aspect][0]['properties']['NETWORK_CENTER_X_LOCATION'])
                self.assertEqual(1.0, frag[cur_aspect][0]['properties']['NETWORK_SCALE_FACTOR'])
            elif cur_aspect == 'visualProperties':
                self.assertEqual(1, len(frag[cur_aspect]))
                self.assertEqual(3, len(frag[cur_aspect][0]['default']))
                self.assertTrue('edge' in frag[cur_aspect][0]['default'])
                self.assertTrue('network' in frag[cur_aspect][0]['default'])
                self.assertTrue('node' in frag[cur_aspect][0]['default'])
            else:
                self.fail('Unknown aspect: ' + str(cur_aspect) + ' : ' + str(frag[cur_aspect]))

        self.assertEqual({'status': [{'success': True}]}, cx[-1])

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

    def test_get_network_as_cx2_stream_not_found(self):
        client = self.get_ndex2_client()
        try:
            # UUID that was just created so it should not exist in NDEx
            client.get_network_as_cx2_stream('0EE12A3D-6594-4D4D-'
                                             '9FF0-AF33D1982E94')
            self.fail('Expected exception')
        except NDExNotFoundError as not_found:
            self.assertTrue('Caught 404 from server: ' in str(not_found))

    def test_get_network_as_cx2_stream_from_cx_uploaded_net(self):
        client = self.get_ndex2_client()

        # create network and add it
        net = ndex2.create_nice_cx_from_file(TestClientIntegration.GLYPICAN2_FILE)
        netname = 'ndex2-client integration test network2' + str(datetime.now())
        net.set_name(netname)
        res = client.save_new_network(net.to_cx(), visibility='PUBLIC')
        self.assertTrue('http' in res)
        netid = re.sub('^.*/', '', res)
        try:
            netsum = self.wait_for_network_to_be_ready(client, netid)
            self.assertIsNotNone(netsum, 'Network is still not ready,'
                                         ' maybe server is busy?')
            res = client.get_network_as_cx2_stream(netid)
            self.assertEqual(200, res.status_code)
            self.check_glypican_cx2_is_correct(res.json())
        finally:
            client.delete_network(network_id=netid)

    def test_save_new_cx2_network(self):
        client = self.get_ndex2_client()

        # load network
        with open(TestClientIntegration.CX2_GLYPICAN2_FILE, 'r') as f:
            cx = json.load(f)

        # set the name
        for frag in cx[1:-1]:
            cur_aspect = list(frag.keys())[0]
            if cur_aspect == 'networkAttributes':
                frag[cur_aspect][0]['name'] = 'ndex2-client integration ' \
                                              'test network2 ' +\
                                              str(datetime.now())
                break

        res = client.save_new_cx2_network(cx, visibility='PUBLIC')
        self.assertTrue('http' in res)
        netid = re.sub('^.*/', '', res)
        try:
            netsum = self.wait_for_network_to_be_ready(client, netid)
            self.assertIsNotNone(netsum, 'Network is still not ready,'
                                         ' maybe server is busy?')
            res = client.get_network_as_cx2_stream(netid)
            self.assertEqual(200, res.status_code)
            self.check_glypican_cx2_is_correct(res.json())
        finally:
            client.delete_network(network_id=netid)

    def test_update_cx2_network_that_was_uploaded_as_cx1(self):
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

            # load network
            with open(TestClientIntegration.CX2_GLYPICAN2_FILE, 'r') as f:
                cx = json.load(f)

            # set the name
            for frag in cx[1:-1]:
                cur_aspect = list(frag.keys())[0]
                if cur_aspect == 'networkAttributes':
                    frag[cur_aspect][0]['name'] = 'ndex2-client integration ' \
                                                  'test network2 ' + \
                                                  str(datetime.now())
                    break

            if sys.version_info.major == 3:
                stream = io.BytesIO(json.dumps(cx,
                                               cls=DecimalEncoder)
                                    .encode('utf-8'))
            else:
                stream = io.BytesIO(json.dumps(cx,
                                               cls=DecimalEncoder))
            client.update_cx2_network(stream, netid)

            netsum = self.wait_for_network_to_be_ready(client, netid)
            self.assertIsNotNone(netsum, 'Network is still not ready,'
                                         ' maybe server is busy?')

            res = client.get_network_as_cx2_stream(netid)
            self.assertEqual(200, res.status_code)
            self.check_glypican_cx2_is_correct(res.json())
        finally:
            client.delete_network(netid)
            try:
                client.get_network_as_cx_stream(netid)
                self.fail('Expected exception')
            except HTTPError:
                pass

    def test_update_cx2_network_with_invalid_network(self):
        client = self.get_ndex2_client()
        try:
            # load network
            with open(TestClientIntegration.CX2_GLYPICAN2_FILE, 'r') as f:
                cx = json.load(f)

                # set the name
                for frag in cx[1:-1]:
                    cur_aspect = list(frag.keys())[0]
                    if cur_aspect == 'networkAttributes':
                        frag[cur_aspect][0]['name'] = 'ndex2-client integration update ' \
                                                      'test network2 ' + \
                                                      str(datetime.now())
                        break
            resurl = client.save_new_cx2_network(cx, visibility='PUBLIC')
            self.assertTrue('http' in resurl)
            netid = resurl[resurl.rindex('/')+1:]

            if sys.version_info.major == 3:
                stream = io.BytesIO(json.dumps([],
                                               cls=DecimalEncoder)
                                    .encode('utf-8'))
            else:
                stream = io.BytesIO(json.dumps([],
                                               cls=DecimalEncoder))

            netsum = self.wait_for_network_to_be_ready(client, netid)
            self.assertEqual('PUBLIC', netsum['visibility'])
            self.assertTrue('ndex2-client' in netsum['name'])
            self.assertEqual(False, netsum['isReadOnly'])
            self.assertEqual(1, netsum['edgeCount'])
            self.assertEqual(2, netsum['nodeCount'])
            self.assertEqual(False, netsum['isShowcase'])
            self.assertEqual('NONE', netsum['indexLevel'])
            self.assertEqual('cx2', netsum['cxFormat'])
            self.assertTrue('errorMessage' not in netsum)
            self.assertEqual(True, netsum['isValid'])

            # updating with invalid network works silently
            client.update_cx2_network(stream, network_id=netid)

            netsum = self.wait_for_network_to_be_ready(client, netid)
            self.assertIsNotNone(netsum, 'Network is still not ready,'
                                         ' maybe server is busy?')
            self.assertEqual(netid, netsum['externalId'])
            # there wont be a name in the summary
            self.assertTrue('name' not in netsum, msg=str(netsum))
            
            # visibility is reset to private
            self.assertEqual('PRIVATE', netsum['visibility'])
            self.assertEqual(False, netsum['isReadOnly'])
            self.assertEqual(0, netsum['edgeCount'])
            self.assertEqual(0, netsum['nodeCount'])
            self.assertEqual(False, netsum['isShowcase'])
            self.assertEqual('NONE', netsum['indexLevel'])
            self.assertEqual('cx2', netsum['cxFormat'])
            self.assertTrue('Expect \'{\' at line' in netsum['errorMessage'])
            self.assertEqual(True, netsum['isValid'])
            
            # trying to get the CX2 of the network will just fail
            client.get_network_as_cx2_stream(netid)

        except NDExNotFoundError as nfe:
            self.assertTrue('Caught 404 from server' in str(nfe))
        finally:
            client.delete_network(network_id=netid)

    def test_upload_network_with_no_network_attributes(self):
        """
        So if one uploads a network with NO network attributes
        to NDEx and then edits the network (setting name visibility, description)
        via [updateNetworkSummary]	[/v2/network/6b89b286-e142-11ec-b397-0ac135e8bacf/summary
        the CX2 endpoint shows the changed network attributes, but the CX1
        is missing the network attributes
        :return:
        """
        client = self.get_ndex2_client()
        # create network and add it
        net = NiceCXNetwork()
        oneid = net.create_node('node1')
        twoid = net.create_node('node2')
        net.create_edge(oneid, twoid, 'hello')

        res = client.save_new_network(net.to_cx(), visibility='PRIVATE')
        try:
            self.assertTrue('http' in res)
            netid = re.sub('^.*/', '', res)
            netsum = self.wait_for_network_to_be_ready(client, netid)
            self.assertIsNotNone(netsum, 'Network is still not ready,'
                                         ' maybe server is busy?')
            self.assertEqual(netid, netsum['externalId'])
            self.assertTrue('name' not in netsum, msg=str(netsum))

            # okay now we have the network, lets update the name
            # and description and then get the network back again
            # via cx1 and cx2 endpoints
            netname = 'ndex2-client integration test network' + str(datetime.now())
            client.update_network_profile(netid,
                                          {'name': netname})
            netsum = self.wait_for_network_to_be_ready(client, netid)
            self.assertIsNotNone(netsum, 'Network is still not ready,'
                                         ' maybe server is busy?')
            cx2_resp = client.get_network_as_cx2_stream(network_id=netid)
            cx2_json = json.loads(cx2_resp.content)
            net_attrs = None
            for aspect in cx2_json:
                print(aspect)
                if 'networkAttributes' in aspect:
                    net_attrs = aspect['networkAttributes']
                    break
            self.assertEqual([{'name': netname}],
                             net_attrs)

            client_resp = client.get_network_as_cx_stream(network_id=netid)
            cx1_net = ndex2.create_nice_cx_from_raw_cx(json.loads(client_resp.content))
            self.assertEqual(netname, cx1_net.get_name(), 'Special test to expose '
                                                          'bug in NDEx server')
        finally:
            client.delete_network(netid)

