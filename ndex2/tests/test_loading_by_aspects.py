__author__ = 'aarongary'

import unittest

import json
import pandas as pd
import csv
import networkx as nx
import ndex2
import ndex2.client as nc
import os
from ndex2.nice_cx_network import NiceCXNetwork
from ndex2.client import DecimalEncoder
from ndex2cx.nice_cx_builder import NiceCXBuilder
import numpy as np

upload_server = 'dev.ndexbio.org'
upload_username = 'scratch'
upload_password = 'scratch'

path_this = os.path.dirname(os.path.abspath(__file__))

@unittest.skip('Test needs to be moved and refactored')
class TestLoadByAspects(unittest.TestCase):
    #@unittest.skip("Temporary skipping")
    def test_create_from_pandas_with_headers2(self):
        print('Testing: CTD_genes_pathways_small.txt')
        path_to_network = os.path.join(path_this, 'CTD_genes_pathways_small.txt')

        with open(path_to_network, 'r') as tsvfile:
            header = [h.strip() for h in tsvfile.readline().split('\t')]

            df = pd.read_csv(tsvfile,delimiter='\t',engine='python',names=header)

            niceCx = ndex2.create_nice_cx_from_pandas(df, source_field='GeneSymbol', target_field='PathwayName', source_node_attr=['GeneID'], target_node_attr=['Pathway Source'], edge_attr=[])

            upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
            self.assertTrue(upload_message)

    #@unittest.skip("Temporary skipping")
    def test_load_nodes(self):
        print('Testing: Manual network build')
        niceCxBuilder = NiceCXBuilder()
        #niceCx = ndex2.create_empty_nice_cx() #NiceCXNetwork()
        gene_list = ['OR2J3', 'AANAT', 'CCDC158', 'PLAC8L1', 'CLK1', 'GLTP', 'PITPNM2','TRAPPC8', 'EIF2S2', 'ST14',
                     'NXF1', 'H3F3B','FOSB', 'MTMR4', 'USP46', 'CDH11', 'ENAH', 'CNOT7', 'STK39', 'CAPZA1', 'STIM2',
                     'DLL4', 'WEE1', 'MYO1D', 'TEAD3']
        max_edge = 1004
        for i in range(1,max_edge):
            node_id = niceCxBuilder.add_node(name='node%s' % str(i), represents=gene_list[i % 10])
            if i > 1 and i < (max_edge - 1):
                niceCxBuilder.add_edge(i - 1, i, 'neighbor-of')

            #niceCx.create_node(id=i, node_name='node%s' % str(i), node_represents=gene_list[i])

        niceCx = niceCxBuilder.get_nice_cx()

        upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
        self.assertTrue(upload_message)
        #print(niceCx.to_cx())

    #@unittest.skip("Temporary skipping")
    def test_load_edges(self):
        print('Testing: NiceCXBuilder')
        niceCxBuilder = NiceCXBuilder()

        node_id_1 = niceCxBuilder.add_node(name='node%s' % str(1), represents='ABC')
        node_id_2 = niceCxBuilder.add_node(name='node%s' % str(2), represents='DEF')
        niceCxBuilder.add_edge(id=1, source=node_id_1, target=node_id_2, interaction='neighbor')
        niceCxBuilder.set_name('Network manual build')
        niceCxBuilder.nice_cx.set_namespaces({'ndex context': 'http://dev.ndexbio.org'})
        niceCx = niceCxBuilder.get_nice_cx()

        #niceCx.set_provenance(['Provenance'])
        upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
        self.assertTrue(upload_message)

    #@unittest.skip("Temporary skipping")
    def test_pandas_loading(self):
        print('Testing: MDA1.txt')
        path_to_network = os.path.join(path_this, 'MDA1.txt')
        niceCxBuilder = NiceCXBuilder()

        with open(path_to_network, 'r') as tsvfile:
            header = [h.strip() for h in tsvfile.readline().split('\t')]

            df = pd.read_csv(tsvfile,delimiter='\t',engine='python',names=header)

            for index, row in df.iterrows():
                node_id_1 = niceCxBuilder.add_node(name=row['Bait'], represents=row['Bait'])
                node_id_2 = niceCxBuilder.add_node(name=row['Prey'], represents=row['Prey'])
                niceCxBuilder.add_edge(id=index, source=node_id_1, target=node_id_2, interaction='interacts-with')

            niceCx = niceCxBuilder.get_nice_cx()

            upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)

        my_df = pd.DataFrame(data=[(4,14),(5,15),(6,16),(7,17)], index=range(0,4), columns=['A','B'])
        self.assertIsNotNone(my_df)
        #print(pd.DataFrame(my_df))

    #@unittest.skip("Temporary skipping")
    def test_create_from_pandas_no_headers(self):
        print('Testing: SIMPLE.txt')
        path_to_network = os.path.join(path_this, 'SIMPLE.txt')

        with open(path_to_network, 'r') as tsvfile:
            df = pd.read_csv(tsvfile,delimiter='\t',engine='python',header=None)

            niceCx = ndex2.create_nice_cx_from_pandas(df) #NiceCXNetwork(pandas_df=df)
            upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
            self.assertTrue(upload_message)

    #@unittest.skip("Temporary skipping")
    def test_create_from_pandas_with_headers(self):
        print('Testing: MDA1.txt')
        path_to_network = os.path.join(path_this, 'MDA1.txt')

        with open(path_to_network, 'r') as tsvfile:
            header = [h.strip() for h in tsvfile.readline().split('\t')]

            df = pd.read_csv(tsvfile,delimiter='\t',engine='python',names=header)

            niceCx = ndex2.create_nice_cx_from_pandas(df, source_field='Bait', target_field='Prey', source_node_attr=['AvePSM'], target_node_attr=['WD'], edge_attr=['Z', 'Entropy']) #NiceCXNetwork()
            #niceCx.create_from_pandas(df, source_field='Bait', target_field='Prey', source_node_attr=['AvePSM'], target_node_attr=['WD'], edge_attr=['Z', 'Entropy'])
            my_cx_json = niceCx.to_cx()
            #print(json.dumps(my_cx_json, cls=DecimalEncoder))
            upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
            self.assertTrue(upload_message)

    #@unittest.skip("Temporary skipping") # PASS
    def test_create_from_server(self):
        print('Testing: Create from server with 548970 edges (uuid:75bf1e85-1bc7-11e6-a298-06603eb7f303)')
        #niceCx = ndex2.create_nice_cx_from_server(server='public.ndexbio.org', uuid='72ef5c3a-caff-11e7-ad58-0ac135e8bacf') #NiceCXNetwork(server='dev2.ndexbio.org', username='scratch', password='scratch', uuid='9433a84d-6196-11e5-8ac5-06603eb7f303')
        niceCx = ndex2.create_nice_cx_from_server(server='public.ndexbio.org', username='scratch', password='scratch', uuid='75bf1e85-1bc7-11e6-a298-06603eb7f303') #NiceCXNetwork(server='dev2.ndexbio.org', username='scratch', password='scratch', uuid='9433a84d-6196-11e5-8ac5-06603eb7f303')

        upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
        self.assertTrue(upload_message)

    #@unittest.skip("Temporary skipping") # PASS
    def test_create_from_pandas_no_headers_3_columns(self):
        print('Testing: SIMPLE3.txt')
        path_to_network = os.path.join(path_this, 'SIMPLE3.txt')

        with open(path_to_network, 'r') as tsvfile:
            df = pd.read_csv(tsvfile,delimiter='\t',engine='python',header=None)

            #====================================
            # BUILD NICECX FROM PANDAS DATAFRAME
            #====================================
            niceCx = ndex2.create_nice_cx_from_pandas(df) #NiceCXNetwork(pandas_df=df)
            niceCx.apply_template('public.ndexbio.org', '56cbe15a-5f7e-11e8-a4bf-0ac135e8bacf')
            upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
            self.assertTrue(upload_message)

    #@unittest.skip("Temporary skipping") #PASS
    def test_create_from_networkx(self):
        print('Testing: SIMPLE3.txt with DictReader')
        path_to_network = os.path.join(path_this, 'SIMPLE3.txt')

        with open(path_to_network, 'r') as tsvfile:
            reader = csv.DictReader(filter(lambda row: row[0] != '#', tsvfile), dialect='excel-tab', fieldnames=['s','t','e'])

            #===========================
            # BUILD NETWORKX GRAPH
            #===========================
            G = nx.Graph(name='loaded from Simple3.txt')
            for row in reader:
                G.add_node(row.get('s'), test1='test1_s', test2='test2_s')
                G.add_node(row.get('t'), test1='test1_t', test2='test2_t')
                G.add_edges_from([(row.get('s'), row.get('t'), {'interaction': 'controls-production-of', 'test3': 'test3',
                                                        'non-number': np.nan})])

            #====================================
            # BUILD NICECX FROM NETWORKX GRAPH
            #====================================
            niceCx = ndex2.create_nice_cx_from_networkx(G) #NiceCXNetwork(networkx_G=G)
            niceCx.apply_template('public.ndexbio.org', '51247435-1e5f-11e8-b939-0ac135e8bacf')
            upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
            self.assertTrue(upload_message)

    #@unittest.skip("Temporary skipping")
    def test_create_from_cx_file(self):
        print('Testing: MEDIUM_NETWORK.cx')
        path_to_network = os.path.join(path_this, 'MEDIUM_NETWORK.cx')

        with open(path_to_network, 'r') as ras_cx:
            #====================================
            # BUILD NICECX FROM CX OBJECT
            #====================================
            niceCx = ndex2.create_nice_cx_from_raw_cx(cx=json.load(ras_cx)) #NiceCXNetwork(cx=json.load(ras_cx))
            my_cx = niceCx.to_cx()
            #print(my_cx)
            upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
            self.assertTrue(upload_message)

    #@unittest.skip("Temporary skipping")
    def test_create_from_cx_file2(self):
        print('Testing: CitationsAndSupports.cx')
        path_to_network = os.path.join(path_this, 'CitationsAndSupports.cx')

        with open(path_to_network, 'r') as ras_cx:
            #====================================
            # BUILD NICECX FROM CX OBJECT
            #====================================
            niceCx = ndex2.create_nice_cx_from_raw_cx(cx=json.load(ras_cx))
            my_cx = niceCx.to_cx()
            #print(my_cx)
            upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
            self.assertTrue(upload_message)

    #@unittest.skip("Temporary skipping")
    def test_create_from_cx_file_with_context(self):
        print('Testing: Metabolism_of_RNA_data_types.cx')
        path_to_network = os.path.join(path_this, 'Metabolism_of_RNA_data_types.cx')

        with open(path_to_network, 'r') as ras_cx:
            #====================================
            # BUILD NICECX FROM CX OBJECT
            #====================================
            niceCx = ndex2.create_nice_cx_from_raw_cx(json.load(ras_cx)) #NiceCXNetwork(cx=json.load(ras_cx))
            my_cx = niceCx.to_cx()
            #print(my_cx)
            upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
            self.assertTrue(upload_message)

    #@unittest.skip("Temporary skipping")
    def test_create_from_server_1(self):
        print('Testing: Create from serve (uuid:b7190ca4-aec2-11e7-9b0a-06832d634f41)')
        #====================================
        # BUILD NICECX FROM SERVER
        #====================================
        niceCx = ndex2.create_nice_cx_from_server(server='dev.ndexbio.org', username='scratch', password='scratch', uuid='b7190ca4-aec2-11e7-9b0a-06832d634f41') #NiceCXNetwork(server='dev.ndexbio.org', username='scratch', password='scratch', uuid='b7190ca4-aec2-11e7-9b0a-06832d634f41')
        upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
        self.assertTrue(upload_message)

    #@unittest.skip("Temporary skipping") # PASS
    def test_export_to_cx_file(self):
        print('Testing: MEDIUM_NETWORK.cx')
        path_to_network = os.path.join(path_this, 'MEDIUM_NETWORK.cx')

        with open(path_to_network, 'r') as ras_cx:
            niceCx = ndex2.create_nice_cx_from_raw_cx(cx=json.load(ras_cx)) #NiceCXNetwork(cx=json.load(ras_cx))
            niceCx.apply_template('public.ndexbio.org', '51247435-1e5f-11e8-b939-0ac135e8bacf')

            nice_networkx = niceCx.to_networkx()

            upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
            self.assertTrue(upload_message)

    #@unittest.skip("Temporary skipping") # PASS
    def test_cx_file_with_position(self):
        print('Testing: network_with_position.cx')
        path_to_network = os.path.join(path_this, 'network_with_position.cx')

        with open(path_to_network, 'r') as ras_cx:
            niceCx = ndex2.create_nice_cx_from_raw_cx(cx=json.load(ras_cx)) #NiceCXNetwork(cx=json.load(ras_cx))
            nice_networkx = niceCx.to_networkx()

            niceCx_from_netx = ndex2.create_nice_cx_from_networkx(nice_networkx)

            upload_message = niceCx_from_netx.upload_to(upload_server, upload_username, upload_password)
            self.assertTrue(upload_message)

    #@unittest.skip("Temporary skipping")
    def test_manual_build(self):
        print('Testing: Build from empty nice cx')
        niceCx = ndex2.create_empty_nice_cx() #NiceCXNetwork()

        fox_node_id = niceCx.create_node(node_name='Fox')
        mouse_node_id = niceCx.create_node(node_name='Mouse')
        bird_node_id = niceCx.create_node(node_name='Bird')

        fox_bird_edge = niceCx.create_edge(edge_source=fox_node_id, edge_target=bird_node_id, edge_interaction='interacts-with')
        fox_mouse_edge = niceCx.create_edge(edge_source=fox_node_id, edge_target=mouse_node_id, edge_interaction='interacts-with')

        niceCx.add_node_attribute(property_of=fox_node_id, name='Color', values='Red')
        niceCx.add_node_attribute(property_of=mouse_node_id, name='Color', values='Gray')
        niceCx.add_node_attribute(property_of=bird_node_id, name='Color', values='Blue')

        upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
        #print(niceCx)

    #@unittest.skip("Temporary skipping")
    def test_create_from_small_cx(self):
        print('Testing: Pandas DataFrame.from_items')
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
                                        ('EdgeProp', [np.float(0.843), 1.2345])])

        #niceCx = ndex2.create_empty_nice_cx() #NiceCXNetwork()
        #niceCx.create_from_pandas(df, source_field='Source', target_field='Target', edge_attr=['EdgeProp'], edge_interaction='Interaction')

        niceCx = ndex2.create_nice_cx_from_pandas(df, source_field='Source', target_field='Target', edge_attr=['EdgeProp'], edge_interaction='Interaction')
        #niceCx = '' #NiceCXNetwork(server='public.ndexbio.org', uuid='f1dd6cc3-0007-11e6-b550-06603eb7f303')

        upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
        #print(niceCx)

    #@unittest.skip("Temporary skipping") # PASS
    def test_create_from_server_manipulate_and_save(self):
        print('Testing: Create from server and manupulate (uuid:51247435-1e5f-11e8-b939-0ac135e8bacf)')
        niceCx = ndex2.create_nice_cx_from_server(server='public.ndexbio.org', uuid='51247435-1e5f-11e8-b939-0ac135e8bacf')

        nice_networkx = niceCx.to_networkx()

        niceCx_from_netx = ndex2.create_nice_cx_from_networkx(nice_networkx)

        # Restore template
        niceCx_from_netx.apply_template('public.ndexbio.org', '51247435-1e5f-11e8-b939-0ac135e8bacf')
        niceCx_from_netx.set_name('Round trip from server to networkx to NDEx')

        upload_message = niceCx_from_netx.upload_to(upload_server, upload_username, upload_password)
        self.assertTrue(upload_message)

    #@unittest.skip("Temporary skipping") # PASS
    def test_create_from_server_manipulate_and_save2(self):
        print('Testing: Create from server and generate networkx (uuid:51247435-1e5f-11e8-b939-0ac135e8bacf)')
        niceCx = ndex2.create_nice_cx_from_server(server='public.ndexbio.org', uuid='51247435-1e5f-11e8-b939-0ac135e8bacf')

        #serialized = pickle.dumps(niceCx.to_cx(), protocol=0)
        #print('Serialized memory:', sys.getsizeof(serialized))

        nice_networkx = niceCx.to_networkx()

        niceCx_from_netx   = ndex2.create_nice_cx_from_networkx(nice_networkx)

        # Restore template
        niceCx_from_netx.apply_template('public.ndexbio.org', '51247435-1e5f-11e8-b939-0ac135e8bacf')
        niceCx_from_netx.set_name('Round trip from server to networkx to NDEx')

        print(niceCx_from_netx)

        upload_message = niceCx_from_netx.upload_to(upload_server, upload_username, upload_password)
        self.assertTrue(upload_message)

    #@unittest.skip("Temporary skipping") # PASS
    def test_create_from_tsv_manipulate_and_save(self):
        print('Testing: mgdb_mutations.txt')
        path_to_network = os.path.join(path_this, 'mgdb_mutations.txt')

        with open(path_to_network, 'r') as tsvfile:
            header = [h.strip() for h in tsvfile.readline().split('\t')]

            df = pd.read_csv(tsvfile,delimiter='\t',engine='python',names=header)

            niceCx = ndex2.create_nice_cx_from_pandas(df, source_field='CDS Mutation', target_field='Gene Symbol', source_node_attr=['Primary Tissue', 'Histology', 'Genomic Locus'], target_node_attr=['Gene ID'], edge_interaction='variant-gene-relationship') #NiceCXNetwork()

            nice_networkx = niceCx.to_networkx()
            nice_pandas = niceCx.to_pandas_dataframe()
            my_csv = nice_pandas.to_csv(sep='\t')

            with open("pandas_to_cx_to_tsv_results.txt", "w") as text_file:
                text_file.write(my_csv)

            niceCx_from_netx = ndex2.create_nice_cx_from_networkx(nice_networkx)

            # Restore template
            niceCx_from_netx.apply_template('ndexbio.org', '2e8f9bdc-1e5f-11e8-b939-0ac135e8bacf')
            niceCx_from_netx.set_name('Round trip from server to networkx to NDEx')

            upload_message = niceCx_from_netx.upload_to(upload_server, upload_username, upload_password)
            self.assertTrue(upload_message)



    #@unittest.skip("Temporary skipping") # PASS
    def test_create_from_big_tsv(self):
        print('Testing: identifier_mappings_small.txt')
        path_to_network = os.path.join(path_this, 'identifier_mappings_small.txt')

        with open(path_to_network, 'r') as tsvfile:
            header = [h.strip() for h in tsvfile.readline().split('\t')]

            df = pd.read_csv(tsvfile,delimiter='\t',engine='python',names=header)

            niceCx = ndex2.create_nice_cx_from_pandas(df, source_field='Preferred_Name', target_field='Name',
                                                      source_node_attr=['Source'],
                                                      edge_interaction='neighbor-of')

            upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
            self.assertTrue(upload_message)

    @unittest.skip("Temporary skipping") # PASS
    def test_update_style(self):
        print('!!!!! WARNING !!!!!')
        print('This test will load a network with 63 Million edges.  It will take a while to run and consume a lot of RAM')
        test_uuid = '83013c93-75ca-11e8-8b82-525400c25d22'
        test_user = 'scratch2'
        test_pass = 'scratch2'
        test_server = 'dev.ndexbio.org'
        print('loading network to nice cx')
        niceCx = ndex2.create_nice_cx_from_server(server=test_server, uuid=test_uuid, username=test_user, password=test_pass)
        print('done loading network to nice cx')

        print('applying template')
        niceCx.apply_template('public.ndexbio.org', '2ccec370-6689-11e7-a03e-0ac135e8bacf')
        print('done applying template')
        print('uploading to server')
        message = niceCx.update_to(test_uuid, test_server, test_user, test_pass)
        print('FINISHED')

    #@unittest.skip("Temporary skipping") # PASS
    def test_netx_plot(self):
        print('Testing: Get user networks (user: scratch) and networkx building')
        my_ndex=ndex2.client.Ndex2('http://test.ndexbio.org', 'scratch', 'scratch')
        my_ndex.update_status()

        test1 = my_ndex.get_network_ids_for_user('scratch')

        #nx_my_graph = nx.read_edgelist("edge_list_network_adrian.txt", nodetype=str)

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

        niceCx_full = ndex2.create_nice_cx_from_networkx(G)
        niceCx_full_networkx = niceCx_full.to_networkx()

        names = nx.get_node_attributes(niceCx_full_networkx, 'name')
        for n in niceCx_full_networkx.nodes():
            print(n)
        print(niceCx_full_networkx.nodes)
        niceCx_full.upload_to(upload_server, upload_username, upload_password)
        print(names)


    #@unittest.skip("Temporary skipping") # PASS
    def test_encoding_file(self):
        print(nx.__version__)
        #pass
        #with open('/Users/aarongary/Development/DataSets/Alzheimer Disease.graphml', 'r', encoding='utf-8', errors='ignore') as gml:
        #    gml_read = gml.read()

        #    print(gml_read)
        #test_uuid = '83013c93-75ca-11e8-8b82-525400c25d22'


if __name__ == '__main__':
    unittest.main()