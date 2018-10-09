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

upload_server = 'dev.ndexbio.org'
upload_username = 'username'
upload_password = 'password'

path_this = os.path.dirname(os.path.abspath(__file__))

class TestCitations(unittest.TestCase):
    # @unittest.skip("Temporary skipping")
    def test_load_edges(self):
        self.assertFalse(upload_username == 'username')

        nice_cx = NiceCXNetwork()

        node_id_1 = nice_cx.create_node(node_name='node%s' % str(1), node_represents='ABC')
        node_id_2 = nice_cx.create_node(node_name='node%s' % str(2), node_represents='DEF')

        edge_id_1 = nice_cx.create_edge(edge_source=node_id_1, edge_target=node_id_2, edge_interaction='neighbor')

        citation1 = nice_cx.add_citation(id=0, title='Hi 1', identifier='pmid:28947956')
        nice_cx.add_edge_citations(edge_id_1, citation1.get('@id'))

        supports1 = nice_cx.add_support(id=0, text='Hi supports 1')
        nice_cx.add_edge_supports(edge_id_1, supports1.get('@id'))

        nice_cx.set_name('Citation testing')
        upload_message = nice_cx.upload_to(upload_server, upload_username, upload_password)
        print(upload_message)
