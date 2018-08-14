__author__ = 'aarongary'

import ndex2.client as nc
import os
import unittest
import ndex2
import json
import pandas as pd
from ndex2.NiceCXNetwork import NiceCXNetwork

import ndex2.client as nc
import networkx as nx



upload_server = 'dev.ndexbio.org'
upload_username = 'cc.zhang'
upload_password = 'cc.zhang'

path_this = os.path.dirname(os.path.abspath(__file__))

class TestNdex2Release(unittest.TestCase):
    @unittest.skip("Temporary skipping")
    def test_load_from_pandas(self):
        path_to_network = os.path.join(path_this, 'SIMPLE3.txt')

        with open(path_to_network, 'r') as tsvfile:
            df = pd.read_csv(tsvfile,delimiter='\t',engine='python',header=None)

            #====================================
            # BUILD NICECX FROM PANDAS DATAFRAME
            #====================================
            niceCx = ndex2.create_nice_cx_from_pandas(df) #NiceCXNetwork(pandas_df=df)
            niceCx.apply_template('public.ndexbio.org', '56cbe15a-5f7e-11e8-a4bf-0ac135e8bacf')
            upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
            #self.assertTrue(upload_message)

    @unittest.skip("Temporary skipping")
    #@unittest.expectedFailure
    def test_set_name(self):
        niceCx_creatures = NiceCXNetwork()
        niceCx_creatures.set_name(43)
        niceCx_creatures.create_node(node_name="tree")
        upload_message = niceCx_creatures.upload_to(upload_server, upload_username, upload_password)
        self.assertTrue(upload_message)

    @unittest.skip("Temporary skipping")
    def test_bad_name_add_node(self):
        niceCx_creatures = NiceCXNetwork()
        niceCx_creatures.set_name("Test Network")
        niceCx_creatures.create_node(node_name=54, id = 45, node_represents="Tree")
        upload_message = niceCx_creatures.upload_to(upload_server, upload_username, upload_password)
        self.assertTrue(upload_message)


    @unittest.skip("Temporary skipping")
    def test_bad_nodes_add_edge(self):
        niceCx_creatures = NiceCXNetwork()
        niceCx_creatures.set_name("Test Network")
        niceCx_creatures.create_node(node_name=324,id=324)
        niceCx_creatures.create_node(node_name=453, id=453)
        niceCx_creatures.create_edge(edge_source="324", edge_target= "453", edge_interaction=['inte'])
        upload_message = niceCx_creatures.upload_to(upload_server, upload_username, upload_password)
        self.assertTrue(upload_message)


    @unittest.skip("Temporary skipping")
    def test_bad_node_attr(self):
        niceCx_creatures = NiceCXNetwork()
        niceCx_creatures.set_name("Test Network")
        fox_node = niceCx_creatures.create_node(node_name=453, id=453)
        niceCx_creatures.add_node_attribute(property_of=fox_node, name='Color', values=['Red',"tree"])

        upload_message = niceCx_creatures.upload_to(upload_server, upload_username, upload_password)
        self.assertTrue(upload_message)



    @unittest.skip("Temporary skipping")
    def test_bad_edge_attr(self):
        niceCx_creatures = NiceCXNetwork()
        niceCx_creatures.set_name("Test Network")
        niceCx_creatures.create_node(node_name=324, id=324)
        niceCx_creatures.create_node(node_name=453, id=453)
        edge = niceCx_creatures.create_edge(edge_source="324", edge_target="453", edge_interaction='inte')
        niceCx_creatures.add_edge_attribute(property_of=edge, name= "djks", values= "jfkl")

        upload_message = niceCx_creatures.upload_to(upload_server, upload_username, upload_password)
        self.assertTrue(upload_message)
        #with self.assertRaises(TypeError):
        #    print("type error raised, passed test")


    @unittest.skip("Temporary skipping")
    def test_creating_from_file(self):
        niceCx_from_cx_file = ndex2.create_nice_cx_from_file('WNT.cx')

        upload_message = niceCx_from_cx_file.upload_to(upload_server, upload_username, upload_password)
        self.assertTrue(upload_message)
        #with self.assertRaises(TypeError):
        #    print("type error raised, passed test")

    @unittest.skip("Temporary skipping")
    def test_creating_from_server(self):
        niceCx_from_server = ndex2.create_nice_cx_from_server(server='public.ndexbio.org', uuid='3f08d557-1e5f-11e8-b939-0ac135e8bacf')

        upload_message = niceCx_from_server.upload_to(upload_server, upload_username, upload_password)
        self.assertTrue(upload_message)

    @unittest.skip("Temporary skipping")
    def test_to_pandas(self):
        niceCx_from_server = ndex2.create_nice_cx_from_server(server='public.ndexbio.org',
                                                              uuid='3f08d557-1e5f-11e8-b939-0ac135e8bacf')

        niceCx_from_server_df = niceCx_from_server.to_pandas_dataframe()
        upload_message = niceCx_from_server_df
        print(upload_message)
        self.assertFalse(upload_message.empty)

    @unittest.skip("Temporary skipping")
    def test_pandas(self):

        df = pd.DataFrame.from_dict({'Source': ['a', 'b', 'c','e'],
                                      'Target': ['b', 'c', 'd', 'f'],
                                      'Interaction': ['touches', 'smells', 'tastes', 'hears'],
                                      'color': ['red', 'blue', 'yellow', 'green'],
                                      'size':['1', '2', '3', '4'],
                                      'width': ['az', 'by', 'cx', 'mn']})
        niceCx_df_with_headers = ndex2.create_nice_cx_from_pandas(df, source_field='Source', target_field='Target',
                                                                  edge_attr=['color'],
                                                                  edge_interaction='Interaction', source_node_attr=["size"],
                                                                  target_node_attr=["width"])
        upload_message = niceCx_df_with_headers.upload_to(upload_server, upload_username, upload_password)
        print(niceCx_df_with_headers.get_summary())

        self.assertTrue(upload_message)

    @unittest.skip("Temporary skipping")
    def test_to_netx(self):
        niceCx_from_server = ndex2.create_nice_cx_from_server(server='public.ndexbio.org',
                                                               uuid='3f08d557-1e5f-11e8-b939-0ac135e8bacf')

        niceCx_from_server_to_netx = niceCx_from_server.to_networkx()

        print(niceCx_from_server_to_netx)
        self.assertTrue(niceCx_from_server_to_netx)

    #@unittest.skip("Temporary skipping")
    def test_add_bad_net_attrs(self):
        niceCx_creatures = NiceCXNetwork()
        niceCx_creatures.set_name("Test")
        niceCx_creatures.create_node(node_name="Fox")
        niceCx_creatures.set_network_attribute(name="version", values="1.0")
        print(niceCx_creatures)
        upload_message = niceCx_creatures.upload_to(upload_server, upload_username, upload_password)

        self.assertTrue(upload_message)


    @unittest.skip("Temporary skipping")
    def test_context(self):
        niceCx_creatures = NiceCXNetwork()
        niceCx_creatures.set_name("Test")
        niceCx_creatures.create_node(node_name="Fox")
        niceCx_creatures.set_context("hkjhnk")
        upload_message = niceCx_creatures.upload_to(upload_server, upload_username, upload_password)

        self.assertTrue(upload_message)




