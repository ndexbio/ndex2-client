__author__ = 'aarongary'

import unittest
import numpy as np
import base64
import ndex2
import time
import scipy
from scipy import sparse, io

class TestLoadMatrixBasedContent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test init"""
        cls.params = {
            'name': 'SIM MATRIX TEST',
            'ndex_server': 'http://dev.ndexbio.org',
            'ndex_user': 'scratch3',
            'ndex_pass': 'scratch3'
        }
        #'ndex_user': 'ENTER YOUR USERNAME!!!!!',
        #'ndex_pass': 'ENTER YOUR PASSWORD!!!!!'
        if cls.params.get('ndex_user') == 'ENTER YOUR USERNAME!!!!!':
            print('*********************************************')
            print('*********************************************')
            print('*********************************************')
            print('   WARNING: PLEASE CHANGE USERNAME BEFORE RUNNING TESTS')
            raise Exception('PLEASE CHANGE THE USERNAME BEFORE ATTEMPTING THESE TESTS')

    #@unittest.skip("Temporary skipping")
    def test_load_sparse_matrix(self):
        M = sparse.random(1000, 1000, .2)
        print(M.data.tobytes())

        print(M)

    #@unittest.skip("Temporary skipping")
    def test_load_large_sim_matrix(self):
        #==========================================
        # Create 2d array with 10,000,000 elements
        #==========================================
        n = 25000000
        X = np.c_[np.random.randint(1,11,(n))].reshape(5000, 5000)
        print('Array created')

        X_cols = ['Col' + str(col) for col in range(0,5000)]
        X_rows = ['Node' + str(x) for x in range(0, 5000)]
        print('Labels created')

        #==========================================
        # Generate and upload network to NDEx
        #==========================================
        new_network_url = ndex2.load_matrix_to_ndex(X, X_cols, X_rows, self.params['ndex_server'], self.params['ndex_user'], self.params['ndex_pass'], 'matrix test')
        uuid = new_network_url.split('/')[-1]
        print('Upload complete')

        #==========================================
        # Get network from NDEx in np.array format
        #==========================================
        time.sleep(2)
        try:
            new_network, x_cols, y_rows = ndex2.get_matrix_from_ndex(self.params['ndex_server'], self.params['ndex_user'], self.params['ndex_pass'], uuid)
        except Exception as e:
            time.sleep(5)
            new_network, x_cols, y_rows = ndex2.get_matrix_from_ndex(self.params['ndex_server'], self.params['ndex_user'], self.params['ndex_pass'], uuid)

        print(new_network)
        print('Download complete')

        self.assertTrue(isinstance(new_network, np.ndarray))

    #@unittest.skip("Temporary skipping")
    def test_load_small_matrix(self):
        X = np.array(
            [[1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0],
             [0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0],
             [0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0],
             [0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0],
             [0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0],
             [0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0],
             [0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1],
             [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 1],
             [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0],
             [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0],
             [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0],
             [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1]]
        )

        X_cols = ['ABC', 'DEF', 'GHI', 'XYZ', 'ABC1', 'DEF1', 'GHI1', 'XYZ1', 'ABC2', 'DEF2', 'GHI2', 'XYZ2', 'ABC3',
                   'DEF3', 'GHI3']
        X_rows = ['ABC', 'DEF', 'GHI', 'XYZ', 'ABC1', 'DEF1', 'GHI1', 'XYZ1', 'ABC2', 'DEF2', 'GHI2', 'XYZ2', 'ABC3',
                   'DEF3', 'GHI3']

        array_data_type = X.dtype.name
        as_bytes = X.tobytes()
        array_shape = X.shape
        serialized = base64.b64encode(as_bytes)

        deserialized = base64.b64decode(serialized)

        print(np.frombuffer(deserialized, dtype=array_data_type).reshape(array_shape))

        new_network_url = ndex2.load_matrix_to_ndex(X, X_cols, X_rows, self.params['ndex_server'], self.params['ndex_user'],
                                                    self.params['ndex_pass'], 'matrix test')
        uuid = new_network_url.split('/')[-1]

        time.sleep(2)
        new_network, x_cols, y_rows = ndex2.get_matrix_from_ndex(self.params['ndex_server'], self.params['ndex_user'],
                                                                 self.params['ndex_pass'], uuid)
        print(new_network)
        self.assertTrue(new_network.shape == (15, 15))


