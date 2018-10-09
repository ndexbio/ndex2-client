__author__ = 'aarongary'

import unittest

import json
import pandas as pd
import networkx as nx
import ndex2
import os
#from ndex2.cx.aspects import ATTRIBUTE_DATA_TYPE

upload_server = 'dev.ndexbio.org'
upload_username = 'scratch'
upload_password = 'scratch'

path_this = os.path.dirname(os.path.abspath(__file__))

class TestLoadByAspects(unittest.TestCase):
    #@unittest.skip("Temporary skipping")
    def test_node_data_types2(self):
        self.assertFalse(upload_username == 'username')
        niceCx = ndex2.create_nice_cx_from_server(server='public.ndexbio.org', uuid='a18fd45e-68d5-11e7-961c-0ac135e8bacf') #NiceCXNetwork(server='dev2.ndexbio.org', username='scratch', password='scratch', uuid='9433a84d-6196-11e5-8ac5-06603eb7f303')
        found_double_type = False
        for id, node in niceCx.get_nodes():
            abc_node_attrs = niceCx.get_node_attributes(node)

            if abc_node_attrs is not None:
                for node_attr in abc_node_attrs:
                    if node_attr.get('d') == 'double':
                        found_double_type = True
                        break

        self.assertTrue(found_double_type)

        print(niceCx.__str__())

    #@unittest.skip("Temporary skipping") # PASS
    def test_node_data_types_from_tsv(self):
        self.assertFalse(upload_username == 'username')
        path_to_network = os.path.join(path_this, 'mgdb_mutations.txt')

        with open(path_to_network, 'r') as tsvfile:
            header = [h.strip() for h in tsvfile.readline().split('\t')]

            df = pd.read_csv(tsvfile,delimiter='\t',engine='python',names=header)
            print(df.head())

            niceCx = ndex2.create_nice_cx_from_pandas(df, source_field='CDS Mutation', target_field='Gene Symbol',
                                                      source_node_attr=['Primary Tissue', 'Histology', 'Genomic Locus',
                                                                        'Gene ID'], target_node_attr=['Gene ID'],
                                                      edge_interaction='variant-gene-relationship') #NiceCXNetwork()

            found_string_type = False
            for id, node in niceCx.get_nodes():
                abc_node_attrs = niceCx.get_node_attributes(node)

                if abc_node_attrs is not None:
                    for node_attr in abc_node_attrs:
                        if node_attr.get('d') == 'string':
                            found_string_type = True

            self.assertTrue(found_string_type)

    #@unittest.skip("Temporary skipping") # PASS
    def test_data_types_from_networkx(self):
        self.assertFalse(upload_username == 'username')
        G = nx.Graph()
        G.add_node('ABC')
        G.add_node('DEF')
        G.add_node('GHI')
        G.add_node('JKL')
        G.add_node('MNO')
        G.add_node('PQR')
        G.add_node('XYZ')

        G.add_edges_from([('ABC','DEF'), ('DEF', 'GHI'),('GHI', 'JKL'),
                          ('DEF', 'JKL'), ('JKL', 'MNO'), ('DEF', 'MNO'),
                         ('MNO', 'XYZ'), ('DEF', 'PQR')])

        G['ABC']['DEF']['ABC'] = 1
        G['DEF']['GHI']['DEF'] = 2
        G['GHI']['JKL']['GHI'] = 3
        G['MNO']['XYZ']['JKL'] = 4
        G['MNO']['XYZ']['MNO'] = 5

        G['ABC']['DEF']['weight'] = 0.321
        G['DEF']['GHI']['weight'] = 0.434
        G['GHI']['JKL']['weight'] = 0.555
        G['MNO']['XYZ']['weight'] = 0.987

        G.nodes['ABC']['attr1'] = 1
        G.nodes['DEF']['attr1'] = 1
        G.nodes['GHI']['attr1'] = 1
        G.nodes['JKL']['attr1'] = 1
        G.nodes['MNO']['attr1'] = 1
        G.nodes['PQR']['attr1'] = 1
        G.nodes['XYZ']['attr1'] = 1

        G.nodes['ABC']['attr2'] = 0.1
        G.nodes['DEF']['attr2'] = 0.1
        G.nodes['GHI']['attr2'] = 0.1
        G.nodes['JKL']['attr2'] = 0.1
        G.nodes['MNO']['attr2'] = 0.1
        G.nodes['PQR']['attr2'] = 0.1
        G.nodes['XYZ']['attr2'] = 0.1

        niceCx_full = ndex2.create_nice_cx_from_networkx(G)

        abc_node_attrs = niceCx_full.get_node_attributes(0)

        found_int_type = False
        found_float_type = False
        if abc_node_attrs is not None:
            for node_attr in abc_node_attrs:
                if node_attr.get('d') == 'integer':
                    found_int_type = True
                if node_attr.get('d') == 'double':
                    found_float_type = True

        found_edge_float_type = False
        for id, edge in niceCx_full.get_edges():
            edge_attrs = niceCx_full.get_edge_attributes(edge)
            if edge_attrs is not None:
                for edge_attr in edge_attrs:
                    if edge_attr.get('d') == 'double':
                        found_edge_float_type = True

        self.assertTrue(found_int_type)
        self.assertTrue(found_float_type)
        self.assertTrue(found_edge_float_type)

    #@unittest.skip("Temporary skipping") # PASS
    def test_data_types_with_special_chars(self):
        self.assertFalse(upload_username == 'username')
        path_to_network = os.path.join(path_this, 'Metabolism_of_RNA_data_types.cx')

        with open(path_to_network, 'r') as data_types_cx:
            #============================
            # BUILD NICECX FROM CX FILE
            #============================
            niceCx = ndex2.create_nice_cx_from_raw_cx(cx=json.load(data_types_cx))

            found_list_of_strings_type = False
            for id, node in niceCx.get_nodes():
                abc_node_attrs = niceCx.get_node_attributes(node)

                if abc_node_attrs is not None:
                    for node_attr in abc_node_attrs:
                        if node_attr.get('d') == 'list_of_string':
                            found_list_of_strings_type = True

            self.assertTrue(found_list_of_strings_type)

    #@unittest.skip("Temporary skipping") # PASS
    def test_data_types_with_special_chars2(self):
        self.assertFalse(upload_username == 'username')
        niceCx = ndex2.create_empty_nice_cx()

        fox_node_id = niceCx.create_node(node_name='A#"')
        mouse_node_id = niceCx.create_node(node_name='B!@#$%')
        bird_node_id = niceCx.create_node(node_name='*&^%^$')

        fox_bird_edge = niceCx.create_edge(edge_source=fox_node_id, edge_target=bird_node_id, edge_interaction='&"""""""')
        fox_mouse_edge = niceCx.create_edge(edge_source=fox_node_id, edge_target=mouse_node_id, edge_interaction='//////\\\\\\')

        niceCx.add_node_attribute(property_of=fox_node_id, name='Color', values='Red')
        niceCx.add_node_attribute(property_of=mouse_node_id, name='Color', values='Gray')
        niceCx.add_node_attribute(property_of=bird_node_id, name='Color', values='Blue')


        upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
        spec_char_network_uuid = upload_message.split('\\')[-1]

        #niceCx = ndex2.create_nice_cx_from_server(server='public.ndexbio.org', uuid='fc63173e-df66-11e7-adc1-0ac135e8bacf') #NiceCXNetwork(server='dev2.ndexbio.org', username='scratch', password='scratch', uuid='9433a84d-6196-11e5-8ac5-06603eb7f303')

        self.assertTrue(upload_message)

    #@unittest.skip("Temporary skipping")
    def test_node_data_types(self):
        self.assertFalse(upload_username == 'username')
        niceCx = ndex2.create_nice_cx_from_server(server='public.ndexbio.org', uuid='f1dd6cc3-0007-11e6-b550-06603eb7f303')
        my_aspect = []
        my_aspect.append({'node': '1', 'value': 'test1'})
        my_aspect.append({'node': '2', 'value': 'test2'})
        my_aspect.append({'node': '3', 'value': 'test3'})
        my_aspect.append({'node': '4', 'value': 'test4'})
        my_aspect.append({'node': '5', 'value': 'test5'})
        my_aspect.append({'node': '6', 'value': 'test6'})
        niceCx.add_opaque_aspect('fakeAspect', my_aspect)
        upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()