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
from nicecxModel.NiceCXNetwork import NiceCXNetwork
from nicecxModel.cx.aspects.NodesElement import NodesElement
from nicecxModel.cx.aspects.EdgesElement import EdgesElement
from nicecxModel.cx.aspects.NetworkAttributesElement import NetworkAttributesElement
from nicecxModel.cx.aspects.NodeAttributesElement import NodeAttributesElement
from nicecxModel.cx.aspects.EdgeAttributesElement import EdgeAttributesElement
from nicecxModel.cx.aspects.CitationElement import CitationElement
from nicecxModel.cx.aspects.SupportElement import SupportElement
from nicecxModel.cx.aspects import ATTRIBUTE_DATA_TYPE
from nicecxModel.cx.aspects.SimpleNode import SimpleNode
from nicecxModel.cx import CX_CONSTANTS
from nicecxNdex.NetworkQuery import NetworkQuery
from nicecxNdex.client import Ndex
from nicecxNdex.NiceCXBuilder import NiceCXBuilder


class TestLoadByAspects(unittest.TestCase):
    @unittest.skip("Temporary skipping")
    def test_load_nodes(self):
        niceCx = NiceCXNetwork()
        gene_list = ['OR2J3', 'AANAT', 'CCDC158', 'PLAC8L1', 'CLK1', 'GLTP', 'PITPNM2','TRAPPC8', 'EIF2S2', 'ST14',
                     'NXF1', 'H3F3B','FOSB', 'MTMR4', 'USP46', 'CDH11', 'ENAH', 'CNOT7', 'STK39', 'CAPZA1', 'STIM2',
                     'DLL4', 'WEE1', 'MYO1D', 'TEAD3']
        for i in range(1,10):
            niceCx.addNode(NodesElement(id=i, node_name='node%s' % str(i), node_represents=gene_list[i]))

        niceCx.upload_to('dev2.ndexbio.org', 'scratch', 'scratch')
        print niceCx.to_json()

    @unittest.skip("Temporary skipping")
    def test_load_edges(self):
        niceCx = NiceCXNetwork()
        niceCx.addNode(NodesElement(id=1, node_name='node%s' % str(1), node_represents='ABC'))
        niceCx.addNode(NodesElement(id=2, node_name='node%s' % str(2), node_represents='DEF'))
        niceCx.addEdge(EdgesElement(id=1, edge_source=1, edge_target=2, edge_interaction='neighbor'))

        niceCx.upload_to('dev2.ndexbio.org', 'scratch', 'scratch')

    @unittest.skip("Temporary skipping")
    def test_pandas_loading(self):
        with open('MDA1.txt', 'rU') as tsvfile:
            header = [h.strip() for h in tsvfile.next().split('\t')]

            df = pd.read_csv(tsvfile,delimiter='\t',engine='python',names=header)

            niceCx = NiceCXNetwork()
            for index, row in df.iterrows():
                niceCx.addNode(NodesElement(id=row['Bait'], node_name=row['Bait'], node_represents=row['Bait']))
                niceCx.addNode(NodesElement(id=row['Prey'], node_name=row['Prey'], node_represents=row['Prey']))

                niceCx.addEdge(EdgesElement(id=index, edge_source=row['Bait'], edge_target=row['Prey'], edge_interaction='interacts-with'))

            niceCx.add_metadata_stub('nodes')
            niceCx.add_metadata_stub('edges')
            if niceCx.nodeAttributes:
                niceCx.add_metadata_stub('nodeAttributes')
            if niceCx.edgeAttributes:
                niceCx.add_metadata_stub('edgeAttributes')
            niceCx.upload_to('dev2.ndexbio.org', 'scratch', 'scratch')

            print df

        my_df = pd.DataFrame(data=[(4,14),(5,15),(6,16),(7,17)], index=range(0,4), columns=['A','B'])
        #print(pd.DataFrame(my_df))

    @unittest.skip("Temporary skipping")
    def test_create_from_pandas_no_headers(self):
        with open('SIMPLE.txt', 'rU') as tsvfile:
            df = pd.read_csv(tsvfile,delimiter='\t',engine='python',header=None)

            niceCx = NiceCXNetwork()
            niceCx.create_from_pandas(df)
            niceCx.upload_to('dev2.ndexbio.org', 'scratch', 'scratch')

    @unittest.skip("Temporary skipping")
    def test_create_from_pandas_with_headers(self):
        #G = NdexGraph(server='http://public.ndexbio.org', uuid='c0e70804-d848-11e6-86b1-0ac135e8bacf')
        with open('MDA1.txt', 'rU') as tsvfile:
            header = [h.strip() for h in tsvfile.next().split('\t')]

            df = pd.read_csv(tsvfile,delimiter='\t',engine='python',names=header)

            niceCx = NiceCXNetwork()
            niceCx.create_from_pandas(df, source_field='Bait', target_field='Prey', source_node_attr=['AvePSM'], target_node_attr=['WD'], edge_attr=['Z', 'Entropy'])
            my_cx_json = niceCx.to_json()
            print json.dumps(my_cx_json)
            niceCx.upload_to('dev2.ndexbio.org', 'scratch', 'scratch')

    @unittest.skip("Temporary skipping")
    def test_create_from_server(self):
        niceCx = NiceCXNetwork()
        niceCx.create_from_server('dev2.ndexbio.org', 'scratch', 'scratch', '9433a84d-6196-11e5-8ac5-06603eb7f303')
        niceCx.upload_to('dev2.ndexbio.org', 'scratch', 'scratch')

    #@unittest.skip("Temporary skipping")
    def test_create_from_pandas_no_headers_3_columns(self):
        with open('SIMPLE3.txt', 'rU') as tsvfile:
            df = pd.read_csv(tsvfile,delimiter='\t',engine='python',header=None)

            #====================================
            # BUILD NICECX FROM PANDAS DATAFRAME
            #====================================
            niceCx = NiceCXNetwork()
            niceCx.create_from_pandas(df)
            niceCx.apply_template('dev2.ndexbio.org', 'scratch', 'scratch', '3daff7cd-9a6b-11e7-9743-0660b7976219')
            niceCx.upload_to('dev2.ndexbio.org', 'scratch', 'scratch')

    @unittest.skip("Temporary skipping")
    def test_create_from_networkx(self):
        with open('SIMPLE3.txt', 'rU') as tsvfile:
            reader = csv.DictReader(filter(lambda row: row[0] != '#', tsvfile), dialect='excel-tab', fieldnames=['s','t','e'])

            #===========================
            # BUILD NETWORKX GRAPH
            #===========================
            G = nx.Graph()
            for row in reader:
                G.add_node(row.get('s'), test1='test1_s', test2='test2_s')
                G.add_node(row.get('t'), test1='test1_t', test2='test2_t')
                G.add_edge(row.get('s'), row.get('t'), {'interaction': 'controls-production-of', 'test3': 'test3'})

            #====================================
            # BUILD NICECX FROM NETWORKX GRAPH
            #====================================
            niceCx = NiceCXNetwork()
            niceCx.create_from_networkx(G)
            niceCx.apply_template('dev2.ndexbio.org', 'scratch', 'scratch', '3daff7cd-9a6b-11e7-9743-0660b7976219')
            niceCx.upload_to('dev2.ndexbio.org', 'scratch', 'scratch')

    @unittest.skip("Temporary skipping")
    def test_create_from_pandas_with_headers2(self):
        with open('CTD_genes_pathways.txt', 'rU') as tsvfile:
            header = [h.strip() for h in tsvfile.next().split('\t')]

            df = pd.read_csv(tsvfile,delimiter='\t',engine='python',names=header)

            niceCx = NiceCXNetwork()
            niceCx.create_from_pandas(df, source_field='GeneSymbol', target_field='PathwayName', source_node_attr=['GeneID'], target_node_attr=['Pathway Source'], edge_attr=[])
            my_cx_json = niceCx.to_json()
            print json.dumps(my_cx_json)
            niceCx.upload_to('dev2.ndexbio.org', 'scratch', 'scratch')
