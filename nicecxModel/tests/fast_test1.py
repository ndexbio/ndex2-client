import json
import pandas as pd
import csv
import networkx as nx
from nicecxModel.NiceCXNetwork import NiceCXNetwork
from nicecxModel.cx.aspects.NodesElement import NodesElement
from nicecxModel.cx.aspects.EdgesElement import EdgesElement

#with open('CTD_genes_pathways.txt', 'rU') as tsvfile:
#with open('CTD_chem_path_enriched.txt', 'rU') as tsvfile:
with open('SIMPLE3.txt', 'rU') as tsvfile:
    #header = [h.strip() for h in tsvfile.next().split('\t')]

    #df = pd.read_csv(tsvfile,delimiter='\t',engine='python',names=header)
    df = pd.read_csv(tsvfile,delimiter='\t',engine='python',header=None)

    #====================================
    # BUILD NICECX FROM PANDAS DATAFRAME
    #====================================
    niceCx = NiceCXNetwork()
    #niceCx.create_from_pandas(df, source_field='GeneSymbol', target_field='PathwayName', source_node_attr=['GeneID'], target_node_attr=['Pathway Source'], edge_attr=[])
    #niceCx.create_from_pandas(df, source_field='ChemicalName', target_field='PathwayName', source_node_attr=['Chemical ID (MeSH)'], target_node_attr=['Pathway Source'], edge_attr=[])
    niceCx.create_from_pandas(df)
    #my_cx_json = niceCx.to_json()
    print 'nx created'
    niceCx.apply_template('dev2.ndexbio.org', 'scratch', 'scratch', '3daff7cd-9a6b-11e7-9743-0660b7976219')
    print 'template applied'

    niceCx.upload_new_network_stream('dev2.ndexbio.org', 'scratch', 'scratch')

    #niceCx.upload_to('dev2.ndexbio.org', 'scratch', 'scratch')
    print 'Done!'

