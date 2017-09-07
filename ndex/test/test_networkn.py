__author__ = 'aarongary'

import unittest
import ndex
from ndex.networkn import  NdexGraph
import json

class NetworkNTests(unittest.TestCase):
    #==============================
    # TEST LARGE NETWORK
    #==============================
    def test_data_to_type(self):
        self.assertTrue(self, ndex.networkn.data_to_type('true','boolean'))
        print(type(ndex.networkn.data_to_type('1.3','double')))
        print(type(ndex.networkn.data_to_type('1.3','float')))
        print(type(ndex.networkn.data_to_type('1','integer')))
        print(type(ndex.networkn.data_to_type('1','long')))
        print(type(ndex.networkn.data_to_type('1','short')))
        print(type(ndex.networkn.data_to_type('1','string')))
        list_of_boolean = type(ndex.networkn.data_to_type('["true","false"]','list_of_boolean'))
        print(list_of_boolean)

        list_of_double = ndex.networkn.data_to_type('[1.3,1.4]','list_of_double')
        print(list_of_double)

        list_of_float = ndex.networkn.data_to_type('[1.3,1.4]','list_of_float')
        print(list_of_float)

        list_of_integer = ndex.networkn.data_to_type('[1,4]','list_of_integer')
        print(list_of_integer)

        list_of_long = ndex.networkn.data_to_type('[1,4]','list_of_long')
        print(list_of_long)

        list_of_short = ndex.networkn.data_to_type('[1,4]','list_of_short')
        print(list_of_short)

        list_of_string = ndex.networkn.data_to_type(['abc'],'list_of_string')
        print(list_of_string)

    def test_edge_float_type(self):
        G = NdexGraph()
        n_a = G.add_new_node(name='A')
        n_b = G.add_new_node(name='B')
        n_c = G.add_new_node(name='C')
        n_d = G.add_new_node(name='D')

        e_1 = G.add_edge(n_a, n_b, 10, {'weight': 1.234})
        e_2 = G.add_edge(n_a, n_c, 11, {'weight': 2.554})
        e_3 = G.add_edge(n_a, n_d, 12, {'weight': 5.789})
        e_4 = G.add_edge(n_b, n_c, 13, {'weight': 2.011})
        e_5 = G.add_edge(n_b, n_d, 14, {'weight': 7.788})

        print json.dumps(G.to_cx())
        G.upload_to('http://dev.ndexbio.org', 'scratch', 'scratch')


if __name__ == '__main__':
    unittest.main()