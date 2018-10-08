__author__ = 'aarongary'

import ndex2.client as nc
import os
import unittest
import ndex2

here = os.path.dirname(__file__)

class TestNdex2Client(unittest.TestCase):
    #@unittest.skip("Temporary skipping")
    def test_get_set(self):
        username = 'scratch'
        password = 'scratch'
        server = 'dev.ndexbio.org'
        my_network_set = '70800b06-29d2-11e7-8059-06832d634f41' # Test 5

        ndex2_client = nc.Ndex2(host=server, username=username, password=password, debug=True)
        set_response = ndex2_client.get_network_set(my_network_set)

        self.assertTrue(set_response.get('externalId') is not None)

    #@unittest.skip("Temporary skipping")
    def test_set_add(self):
        username = 'scratch'
        password = 'scratch'
        server = 'dev.ndexbio.org'
        my_network_set = '70800b06-29d2-11e7-8059-06832d634f41' # Test 5
        my_test_networks = ['270e6bc1-d935-11e7-aa3d-06832d634f41']

        ndex2_client = nc.Ndex2(host=server, username=username, password=password, debug=True)
        set_response = ndex2_client.add_networks_to_networkset(my_network_set, my_test_networks)

        self.assertTrue('http' in set_response) # Successful response is the URL to the set

    #@unittest.skip("Temporary skipping")
    def test_set_add_private(self):
        username = 'scratch'
        password = 'scratch'
        server = 'dev.ndexbio.org'
        my_network_set = '70800b06-29d2-11e7-8059-06832d634f41' # Test 5
        my_test_networks = ['270e6bc1-d935-11e7-aa3d-06832d634f41']

        ndex2_client = nc.Ndex2(host=server, username=username, password=password, debug=True)
        set_response = ndex2_client.delete_networks_from_networkset(my_network_set, my_test_networks)

        self.assertTrue(len(set_response) == 0) # Empty response means no errors


    #@unittest.skip("Temporary skipping")
    def test_get_set(self):
        niceCx = ndex2.create_nice_cx_from_server(server='public.ndexbio.org', uuid='c7f3660b-df7e-11e7-adc1-0ac135e8bacf')

        context = [{'ncbigene': 'http://identifiers.org/ncbigene/',
                   'hgnc.symbol': 'http://identifiers.org/hgnc.symbol/',
                   'uniprot': 'http://identifiers.org/uniprot/'}]
        niceCx.set_context(context)
        niceCx.set_name('Testing Context')
        upload_message = niceCx.upload_to('public.ndexbio.org', 'scratch', 'scratch')

        print(niceCx.__str__())

