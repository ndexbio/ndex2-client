__author__ = 'aarongary'

import unittest

import sys
import time
import ijson
import pickle
import json
import pandas as pd
import csv
import networkx as nx
import ndex2
import os
from nicecxModel.NiceCXNetwork import NiceCXNetwork
from nicecxModel.cx.aspects.NodeElement import NodeElement
from nicecxModel.cx.aspects.EdgeElement import EdgeElement
from nicecxModel.cx.aspects.NetworkAttributesElement import NetworkAttributesElement
from nicecxModel.cx.aspects.NodeAttributesElement import NodeAttributesElement
from nicecxModel.cx.aspects.EdgeAttributesElement import EdgeAttributesElement
from nicecxModel.cx.aspects.CitationElement import CitationElement
from nicecxModel.cx.aspects.SupportElement import SupportElement
from nicecxModel.cx.aspects import ATTRIBUTE_DATA_TYPE
from nicecxModel.cx.aspects.SimpleNode import SimpleNode
from nicecxModel.cx import CX_CONSTANTS
from ndex2.NetworkQuery import NetworkQuery
from ndex2.client import Ndex2
from ndex2.NiceCXBuilder import NiceCXBuilder
from ndex2.client import DecimalEncoder

upload_server = 'dev.ndexbio.org'
upload_username = 'scratch'
upload_password = 'scratch'
here = os.path.dirname(__file__)

class TestLoadByAspects(unittest.TestCase):
    @unittest.skip("Temporary skipping")
    def test_create_from_pandas_with_headers2(self):
        cx_file = os.path.join(os.getcwd(), 'SimpleNetwork.cx')
        print(cx_file)
        niceCx_from_cx_file = ndex2.create_nice_cx_from_filename(cx_file)

        with open('CTD_genes_pathways.txt', 'rU') as tsvfile:
            header = [h.strip() for h in tsvfile.readline().split('\t')]

            df = pd.read_csv(tsvfile,delimiter='\t',engine='python',names=header)

            niceCx = NiceCXNetwork()
            niceCx = ndex2.create_nice_cx_from_pandas(df, source_field='GeneSymbol', target_field='PathwayName', source_node_attr=['GeneID'], target_node_attr=['Pathway Source'], edge_attr=[])

            for k, v in niceCx.get_edges():
                print(k)
                print(v)
            #niceCx.create_from_pandas(df, source_field='GeneSymbol', target_field='PathwayName', source_node_attr=['GeneID'], target_node_attr=['Pathway Source'], edge_attr=[])
            #my_cx_json = niceCx.to_cx()
            #print(json.dumps(my_cx_json))
            upload_message = True #niceCx.upload_to(upload_server, upload_username, upload_password)
            self.assertTrue(upload_message)

    @unittest.skip("Temporary skipping")
    def test_load_nodes(self):
        niceCx = ndex2.create_empty_nice_cx() #NiceCXNetwork()
        gene_list = ['OR2J3', 'AANAT', 'CCDC158', 'PLAC8L1', 'CLK1', 'GLTP', 'PITPNM2','TRAPPC8', 'EIF2S2', 'ST14',
                     'NXF1', 'H3F3B','FOSB', 'MTMR4', 'USP46', 'CDH11', 'ENAH', 'CNOT7', 'STK39', 'CAPZA1', 'STIM2',
                     'DLL4', 'WEE1', 'MYO1D', 'TEAD3']
        for i in range(1,10):
            niceCx.create_node(id=i, node_name='node%s' % str(i), node_represents=gene_list[i])

        upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
        self.assertTrue(upload_message)
        print(niceCx.to_cx())

    @unittest.skip("Temporary skipping")
    def test_load_edges(self):
        niceCx = ndex2.create_empty_nice_cx() #NiceCXNetwork()
        niceCx.create_node(id=1, node_name='node%s' % str(1), node_represents='ABC')
        niceCx.create_node(id=2, node_name='node%s' % str(2), node_represents='DEF')
        niceCx.create_edge(id=1, edge_source=1, edge_target=2, edge_interaction='neighbor')

        upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
        self.assertTrue(upload_message)

    @unittest.skip("Temporary skipping")
    def test_pandas_loading(self):
        with open('MDA1.txt', 'rU') as tsvfile:
            header = [h.strip() for h in tsvfile.readline().split('\t')]

            df = pd.read_csv(tsvfile,delimiter='\t',engine='python',names=header)

            niceCx = ndex2.create_empty_nice_cx() #NiceCXNetwork()
            for index, row in df.iterrows():
                niceCx.create_node(id=row['Bait'], node_name=row['Bait'], node_represents=row['Bait'])
                niceCx.create_node(id=row['Prey'], node_name=row['Prey'], node_represents=row['Prey'])

                niceCx.create_edge(id=index, edge_source=row['Bait'], edge_target=row['Prey'], edge_interaction='interacts-with')

            niceCx.add_metadata_stub('nodes')
            niceCx.add_metadata_stub('edges')
            if niceCx.nodeAttributes:
                niceCx.add_metadata_stub('nodeAttributes')
            if niceCx.edgeAttributes:
                niceCx.add_metadata_stub('edgeAttributes')
            upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)

            print(df)

        my_df = pd.DataFrame(data=[(4,14),(5,15),(6,16),(7,17)], index=range(0,4), columns=['A','B'])
        self.assertIsNotNone(my_df)
        #print(pd.DataFrame(my_df))

    @unittest.skip("Temporary skipping")
    def test_create_from_pandas_no_headers(self):
        with open('SIMPLE.txt', 'rU') as tsvfile:
            df = pd.read_csv(tsvfile,delimiter='\t',engine='python',header=None)

            niceCx = ndex2.create_nice_cx_from_pandas(df) #NiceCXNetwork(pandas_df=df)
            upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
            self.assertTrue(upload_message)

    @unittest.skip("Temporary skipping")
    def test_create_from_pandas_with_headers(self):
        with open('MDA1.txt', 'rU') as tsvfile:
            header = [h.strip() for h in tsvfile.readline().split('\t')]

            df = pd.read_csv(tsvfile,delimiter='\t',engine='python',names=header)

            niceCx = ndex2.create_nice_cx_from_pandas(df, source_field='Bait', target_field='Prey', source_node_attr=['AvePSM'], target_node_attr=['WD'], edge_attr=['Z', 'Entropy']) #NiceCXNetwork()
            #niceCx.create_from_pandas(df, source_field='Bait', target_field='Prey', source_node_attr=['AvePSM'], target_node_attr=['WD'], edge_attr=['Z', 'Entropy'])
            my_cx_json = niceCx.to_cx()
            print(json.dumps(my_cx_json, cls=DecimalEncoder))
            upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
            self.assertTrue(upload_message)

    @unittest.skip("Temporary skipping") # PASS
    def test_create_from_server(self):
        niceCx = ndex2.create_nice_cx_from_server(server='dev2.ndexbio.org', username='scratch', password='scratch', uuid='9433a84d-6196-11e5-8ac5-06603eb7f303') #NiceCXNetwork(server='dev2.ndexbio.org', username='scratch', password='scratch', uuid='9433a84d-6196-11e5-8ac5-06603eb7f303')
        #niceCx = ndex2.create_nice_cx_from_server(server='public.ndexbio.org', username='scratch', password='scratch', uuid='75bf1e85-1bc7-11e6-a298-06603eb7f303') #NiceCXNetwork(server='dev2.ndexbio.org', username='scratch', password='scratch', uuid='9433a84d-6196-11e5-8ac5-06603eb7f303')

        upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
        self.assertTrue(upload_message)

    @unittest.skip("Temporary skipping") # PASS
    def test_create_from_pandas_no_headers_3_columns(self):
        with open('SIMPLE3.txt', 'rU') as tsvfile:
            df = pd.read_csv(tsvfile,delimiter='\t',engine='python',header=None)

            #====================================
            # BUILD NICECX FROM PANDAS DATAFRAME
            #====================================
            niceCx = ndex2.create_nice_cx_from_pandas(df) #NiceCXNetwork(pandas_df=df)
            niceCx.apply_template('dev2.ndexbio.org', 'scratch', 'scratch', '3daff7cd-9a6b-11e7-9743-0660b7976219')
            upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
            self.assertTrue(upload_message)

    @unittest.skip("Temporary skipping") #PASS
    def test_create_from_networkx(self):
        with open('SIMPLE3.txt', 'rU') as tsvfile:
            reader = csv.DictReader(filter(lambda row: row[0] != '#', tsvfile), dialect='excel-tab', fieldnames=['s','t','e'])

            #===========================
            # BUILD NETWORKX GRAPH
            #===========================
            G = nx.Graph(name='loaded from Simple3.txt')
            for row in reader:
                G.add_node(row.get('s'), test1='test1_s', test2='test2_s')
                G.add_node(row.get('t'), test1='test1_t', test2='test2_t')
                G.add_edge(row.get('s'), row.get('t'), {'interaction': 'controls-production-of', 'test3': 'test3'})

            #====================================
            # BUILD NICECX FROM NETWORKX GRAPH
            #====================================
            niceCx = ndex2.create_nice_cx_from_networkx(G) #NiceCXNetwork(networkx_G=G)
            niceCx.apply_template('dev2.ndexbio.org', 'scratch', 'scratch', '3daff7cd-9a6b-11e7-9743-0660b7976219')
            upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
            self.assertTrue(upload_message)

    #@unittest.skip("Temporary skipping")
    def test_create_from_cx_file(self):
        with open('MEDIUM_NETWORK.cx', 'rU') as ras_cx:
            #====================================
            # BUILD NICECX FROM PANDAS DATAFRAME
            #====================================
            niceCx = ndex2.create_nice_cx_from_cx(cx=json.load(ras_cx)) #NiceCXNetwork(cx=json.load(ras_cx))
            my_cx = niceCx.to_cx()
            print(my_cx)
            upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
            self.assertTrue(upload_message)

    @unittest.skip("Temporary skipping")
    def test_create_from_server_1(self):
        #====================================
        # BUILD NICECX FROM SERVER
        #====================================
        niceCx = ndex2.create_nice_cx_from_server(server='dev.ndexbio.org', username='scratch', password='scratch', uuid='b7190ca4-aec2-11e7-9b0a-06832d634f41') #NiceCXNetwork(server='dev.ndexbio.org', username='scratch', password='scratch', uuid='b7190ca4-aec2-11e7-9b0a-06832d634f41')
        upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
        self.assertTrue(upload_message)

    @unittest.skip("Temporary skipping") # PASS
    def test_export_to_cx_file(self):
        with open('MEDIUM_NETWORK.cx', 'rU') as ras_cx:
            #====================================
            # BUILD NICECX FROM PANDAS DATAFRAME
            #====================================
            niceCx = ndex2.create_nice_cx_from_cx(cx=json.load(ras_cx)) #NiceCXNetwork(cx=json.load(ras_cx))
            nice_networkx = niceCx.to_networkx()
            #my_cx = niceCx.to_cx()
            print(nice_networkx)
            upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
            self.assertTrue(upload_message)

    @unittest.skip("Temporary skipping")
    def test_manual_build(self):
        niceCx = ndex2.create_empty_nice_cx() #NiceCXNetwork()

        fox_node_id = niceCx.create_node(node_name='Fox')
        mouse_node_id = niceCx.create_node(node_name='Mouse')
        bird_node_id = niceCx.create_node(node_name='Bird')

        fox_bird_edge = niceCx.create_edge(edge_source=fox_node_id, edge_target=bird_node_id, edge_interaction='interacts-with')
        fox_mouse_edge = niceCx.create_edge(edge_source=fox_node_id, edge_target=mouse_node_id, edge_interaction='interacts-with')

        niceCx.add_node_attribute(property_of=fox_node_id, name='Color', values='Red')
        niceCx.add_node_attribute(property_of=mouse_node_id, name='Color', values='Gray')
        niceCx.add_node_attribute(property_of=bird_node_id, name='Color', values='Blue')

        print(niceCx)

    @unittest.skip("Temporary skipping")
    def test_create_from_small_cx(self):
        my_cx = [
            {"numberVerification":[{"longNumber":281474976710655}]},
            {"metaData":[{"consistencyGroup":1,"elementCount":2,"idCounter":2,"name":"nodes","version":"1.0"},
            {"consistencyGroup":1,"elementCount":1,"idCounter":1,"name":"edges","version":"1.0"}]},
            {"nodes":[{"@id": 1, "n": "node1", "r": "ABC"}, {"@id": 2, "n": "node2", "r": "DEF"}]},
            {"edges":[{"@id": 1, "s": 1, "t": 2, "i": "neighbor"}]},
            {"status":[{"error":"","success":True}]}
        ]

        #niceCx = NiceCXNetwork(cx=my_cx)

        #data = [('Source', 'Target', 'interaction', 'EdgeProp'), ('ABC', 'DEF', 'interacts-with', 'Edge property 1'), ('DEF', 'XYZ', 'neighbor-of', 'Edge property 2')]
        #df = pd.DataFrame.from_records(data)
        #niceCx = NiceCXNetwork(pandas_df=df)

        df = pd.DataFrame.from_items([('Source', ['ABC', 'DEF']),
                                        ('Target', ['DEF', 'XYZ']),
                                        ('Interaction', ['interacts-with', 'neighbor-of']),
                                        ('EdgeProp', ['Edge property 1', 'Edge property 2'])])

        niceCx = ndex2.create_empty_nice_cx() #NiceCXNetwork()
        niceCx.create_from_pandas(df, source_field='Source', target_field='Target', edge_attr=['EdgeProp'], edge_interaction='Interaction')

        niceCx = '' #NiceCXNetwork(server='public.ndexbio.org', uuid='f1dd6cc3-0007-11e6-b550-06603eb7f303')

        #upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
        print(niceCx)
