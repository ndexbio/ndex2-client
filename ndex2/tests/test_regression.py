__author__ = 'aarongary'

import unittest

import json
import pandas as pd
import csv
import networkx as nx
import ndex2
import os
from ndex2cx.nice_cx_builder import NiceCXBuilder

#upload_server = 'dev.ndexbio.org'
#upload_username = 'scratch'
#upload_password = 'scratch'
upload_server = 'public.ndexbio.org'
upload_username = 'scratch'
upload_password = 'scratch'

path_this = os.path.dirname(os.path.abspath(__file__))


class TestRegression(unittest.TestCase):
    #@unittest.skip("Temporary skipping")
    def test_context(self):
        print('Testing: context')
        context = {
            'signor': 'http://signor.uniroma2.it/relation_result.php?id=',
            'BTO': 'http://identifiers.org/bto/BTO:',
            'uniprot': 'http://identifiers.org/uniprot/',
            'pubmed': 'http://identifiers.org/pubmed/',
            'CID': 'http://identifiers.org/pubchem.compound/',
            'SID': 'http://identifiers.org/pubchem.substance/',
            'chebi': 'http://identifiers.org/chebi/CHEBI:'
        }

        nice_cx_builder = NiceCXBuilder()
        nice_cx_builder.set_context(context)

        node_id_1 = nice_cx_builder.add_node(name='ABC', represents='ABC')
        node_id_2 = nice_cx_builder.add_node(name='DEF', represents='DEF')

        nice_cx_builder.add_node_attribute(node_id_1, 'testing_attr_double', [1.2, 2.5, 2.7])
        nice_cx_builder.add_node_attribute(node_id_1, 'diffusion_output_heat', '1.4599107187941883E-4')
        nice_cx_builder.add_node_attribute(node_id_2, 'diffusion_output_heat', '1.2387941883E-4')
        nice_cx_builder.add_node_attribute(node_id_1, 'aliases', ['uniprot knowledgebase:Q5I2A4', 'uniprot knowledgebase:Q8N7E5', 'uniprot knowledgebase:Q8TAZ6'])
        nice_cx_builder.add_node_attribute(node_id_1, 'diffusion_output_rank', 1)
        nice_cx_builder.add_node_attribute(node_id_2, 'diffusion_output_rank', 2)


        edge_id = nice_cx_builder.add_edge(id=1, source=node_id_1, target=node_id_2, interaction='test-relationship')

        nice_cx_builder.add_edge_attribute(edge_id, 'citation', ['pubmed:21880741'], type='list_of_string')

        nice_cx = nice_cx_builder.get_nice_cx()


        node_attr_to_change = nice_cx.get_node_attribute(node_id_1, 'testing_attr_double')
        node_attr_to_change['v'] = [1.0, 2.0, 3.0]


        #for node_id, node in nice_cx.get_nodes():
            #node_attr_to_condition = nice_cx.get_node_attribute(node_id, 'diffusion_output_heat')
            #node_attr_to_condition['v'] = ("%0.15f" % float(node_attr_to_condition.get('v')))

            #node_attr_array_to_string = nice_cx.get_node_attribute(node_id, 'aliases')
            #node_attr_to_condition['v'] = ("%0.15f" % float(node_attr_to_condition.get('v')))

            #nice_cx.remove_node_attribute(node_id, 'aliases')

        R = nice_cx.to_networkx()
        nos = []
        for n in R.nodes():
            if R.node[n]['diffusion_output_rank'] < 10:
                R.node[n]['nid'] = n
                nos.append(R.node[n])
        nos = sorted(nos, key=lambda k: k['diffusion_output_rank'])
        for no in nos:
            print("id: " + str(no['nid']) + " name: " + no['nid'] + " rank: " + str(
                no['diffusion_output_rank']) + " heat: " + str(no['diffusion_output_heat']))

        node_list2 = next(iter(nice_cx.nodes))


        node_list = list(nice_cx.get_nodes())

        print(list(nice_cx.get_nodes()))


        with open('my_cx.cx', 'w') as file:
            json.dump(nice_cx.to_cx(), file)

        upload_message = nice_cx.upload_to(upload_server, upload_username, upload_password)

        self.assertTrue(upload_message)

    #@unittest.skip("Temporary skipping")
    def test_full_core_aspects_cx_file(self):
        print('Testing: Full_core_aspects.cx')
        path_to_network = os.path.join(path_this, 'Full_core_aspects.cx')

        with open(path_to_network, 'r') as ras_cx:
            nice_cx = ndex2.create_nice_cx_from_raw_cx(cx=json.load(ras_cx))

            upload_message = nice_cx.upload_to(upload_server, upload_username, upload_password)
            self.assertTrue(upload_message)

    #@unittest.skip("Temporary skipping")
    def test_pandas_loading(self):
        print('Testing: edge_list_network_adrian_small.txt')
        path_to_network = os.path.join(path_this, 'edge_list_network_adrian_small.txt')
        niceCxBuilder = NiceCXBuilder()
        context = {
            'signor': 'http://signor.uniroma2.it/relation_result.php?id=',
            'BTO': 'http://identifiers.org/bto/BTO:',
            'uniprot': 'http://identifiers.org/uniprot/',
            'pubmed': 'http://identifiers.org/pubmed/',
            'CID': 'http://identifiers.org/pubchem.compound/',
            'SID': 'http://identifiers.org/pubchem.substance/',
            'chebi': 'http://identifiers.org/chebi/CHEBI:'
        }

        with open(path_to_network, 'r') as tsvfile:
            header = ['Source', 'Target']

            df = pd.read_csv(tsvfile,delimiter='\t',engine='python',names=header)

            nice_cx = ndex2.create_nice_cx_from_pandas(df) #NiceCXNetwork(pandas_df=df)
            nice_cx.set_context(context)

            upload_message = nice_cx.upload_to(upload_server, upload_username, upload_password)

            self.assertTrue('error' not in upload_message)

    #@unittest.skip("Temporary skipping")
    def test_manual_build(self):
        print('Testing: Manual build with NiceCXBuilder')
        nice_cx_builder = NiceCXBuilder()

        node_id_1 = nice_cx_builder.add_node(name=1, represents=2)
        node_id_2 = nice_cx_builder.add_node(name='node%s' % str(2), represents='DEF')
        try:
            nice_cx_builder.add_node_attribute(node_id_1, 'testing_attr', None)
        except TypeError as te:
            print('Correctly identified bad node value')

        nice_cx_builder.add_node_attribute(node_id_1, 'testing_attr_double', [1.2, 2.5, 2.7])

        nice_cx_builder.add_node_attribute(node_id_1, 'testing_attr_int', [16, 4, 8])
        nice_cx_builder.add_node_attribute(node_id_1, 'testing_attr_int', [16, 4, 8]) # duplicate - should be ignored
        nice_cx_builder.add_node_attribute(node_id_1, 'testing_attr_int', [16, 4, 8]) # duplicate - should be ignored

        try:
            nice_cx_builder.add_node_attribute(node_id_1, 'testing_attr2', [10.2, 20.5, 'abc'], type='list_of_float')
        except ValueError:
            print('Correctly identified bad value in node attribute list')

        edge_id = nice_cx_builder.add_edge(id=1, source=node_id_1, target=node_id_2, interaction='test-relationship')

        nice_cx_builder.add_edge_attribute(edge_id, 'testing_attr', [1.2, 2.5, '2.7'], type='list_of_float')
        nice_cx_builder.add_edge_attribute(edge_id, 'testing_attr', [1.2, 2.5, '2.7'], type='list_of_float') # duplicate - should be ignored
        nice_cx_builder.add_edge_attribute(edge_id, 'testing_attr', [1.2, 2.5, '2.7'], type='list_of_float') # duplicate - should be ignored

        try:
            nice_cx_builder.add_edge_attribute(edge_id, 'testing_attr2', [10.2, 20.5, 'abc'], type='list_of_float')
        except ValueError:
            print('Correctly identified bad value in list')

        nice_cx_builder.set_name('Network manual build')
        nice_cx_builder.nice_cx.set_namespaces({'ndex context': 'http://dev.ndexbio.org'})
        nice_cx = nice_cx_builder.get_nice_cx()

        node_attrs = nice_cx.get_node_attributes(node_id_1)
        edge_attrs = nice_cx.get_edge_attributes(edge_id)

        upload_message = nice_cx.upload_to(upload_server, upload_username, upload_password)

        self.assertTrue(upload_message)

        node1_attr_double = nice_cx.get_node_attribute(node_id_1, 'testing_attr_double')
        self.assertTrue(node1_attr_double.get('d') == 'list_of_double')

        node1_attr_int = nice_cx.get_node_attribute(node_id_1, 'testing_attr_int')
        self.assertTrue(node1_attr_int.get('d') == 'list_of_integer')

        self.assertTrue(len(node_attrs) == 2)
        self.assertTrue(len(edge_attrs) == 1)

    #@unittest.skip("Temporary skipping") # PASS
    def test_create_from_server(self):
        print('Testing: Create from server with 548970 edges (uuid:75bf1e85-1bc7-11e6-a298-06603eb7f303)')
        #niceCx = ndex2.create_nice_cx_from_server(server='public.ndexbio.org', uuid='72ef5c3a-caff-11e7-ad58-0ac135e8bacf') #NiceCXNetwork(server='dev2.ndexbio.org', username='scratch', password='scratch', uuid='9433a84d-6196-11e5-8ac5-06603eb7f303')
        niceCx = ndex2.create_nice_cx_from_server(server='public.ndexbio.org', username='scratch', password='scratch', uuid='360a2311-c8c0-11e8-aaa6-0ac135e8bacf') #NiceCXNetwork(server='dev2.ndexbio.org', username='scratch', password='scratch', uuid='9433a84d-6196-11e5-8ac5-06603eb7f303')

        upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
        self.assertTrue(upload_message)

if __name__ == '__main__':
    unittest.main()


