__author__ = 'aarongary'

import ndex2.client as nc
import os
import unittest

here = os.path.dirname(__file__)

class TestNdex2Client(unittest.TestCase):
    #@unittest.skip("Temporary skipping")
    def test_set_add(self):
        username = 'scratch'
        password = 'scratch'
        server = 'dev.ndexbio.org'
        my_network_set = '70800b06-29d2-11e7-8059-06832d634f41' # Test 5
        my_test_networks = ['270e6bc1-d935-11e7-aa3d-06832d634f41']

        ndex2_client = nc.Ndex2(host=server, username=username, password=password, debug=True)
        set_response = ndex2_client.add_networks_to_networkset(my_network_set, my_test_networks)

        print(set_response)

        self.assertTrue('http' in set_response)

    #@unittest.skip("Temporary skipping")
    def test_set_add_private(self):
        username = 'scratch'
        password = 'scratch'
        server = 'dev.ndexbio.org'
        my_network_set = '70800b06-29d2-11e7-8059-06832d634f41' # Test 5
        my_test_networks = ['270e6bc1-d935-11e7-aa3d-06832d634f41']

        ndex2_client = nc.Ndex2(host=server, username=username, password=password, debug=True)
        set_response = ndex2_client.delete_networks_from_networkset(my_network_set, my_test_networks)

        print(set_response)

        self.assertTrue(len(set_response) == 0)


