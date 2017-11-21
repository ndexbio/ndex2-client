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
import ndex2

upload_server = 'dev.ndexbio.org'
upload_username = 'scratch'
upload_password = 'scratch'
here = os.path.dirname(__file__)

class TestLoadByAspects(unittest.TestCase):

    @unittest.skip("Temporary skipping")
    def test_simple_create(self):
        niceCx_creatures = NiceCXNetwork()
        niceCx_creatures.set_name("Food Web")
        fox_node = niceCx_creatures.create_node(node_name='Fox')
        mouse_node = niceCx_creatures.create_node(node_name='Mouse')
        bird_node = niceCx_creatures.create_node(node_name='Bird')

        fox_bird_edge = niceCx_creatures.create_edge(edge_source=fox_node, edge_target=bird_node, edge_interaction='interacts-with')

        fox_mouse_edge = niceCx_creatures.create_edge(edge_source=fox_node, edge_target=mouse_node, edge_interaction='interacts-with')

        niceCx_creatures.add_node_attribute(property_of=fox_node, name='Color', values='Red')

        niceCx_creatures.add_node_attribute(property_of=mouse_node, name='Color', values='Gray')

        niceCx_creatures.add_node_attribute(property_of=bird_node, name='Color', values='Blue')

        niceCx_creatures.add_edge_attribute(property_of=fox_mouse_edge, name='Hunted', values='On the ground')

        print(niceCx_creatures.get_node_attribute(fox_node, 'Color'))

    @unittest.skip("Temporary skipping")
    def test_edit_network_attributes(self):
        with open('SIMPLE_WITH_ATTRIBUTES.txt', 'rU') as tsvfile:
            header = [h.strip() for h in tsvfile.next().split('\t')]

            df = pd.read_csv(tsvfile,delimiter='\t',engine='python',names=header)

            niceCx = ndex2.create_nice_cx_from_pandas(df, source_field='SOURCE', target_field='TARGET', source_node_attr=['NODEATTR'], target_node_attr=[], edge_attr=['EDGEATTR']) #NiceCXNetwork()

            for k, v in niceCx.get_nodes():
                node_attr = niceCx.get_node_attribute_object(k, 'NODEATTR')
                if node_attr:
                    niceCx.set_node_attribute(k, 'NODEATTR', node_attr.get_values() + 'xyz')
                print(node_attr)

            for k, v in niceCx.get_edges():
                edge_attr = niceCx.get_edge_attribute_object(k, 'EDGEATTR')
                if edge_attr:
                    niceCx.set_edge_attribute(k, 'EDGEATTR', edge_attr.get_values() + 'abc')
                print(edge_attr)


            my_cx_json = niceCx.to_cx()
            print(json.dumps(my_cx_json))
            #upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
            #self.assertTrue(upload_message)

    #@unittest.skip("Temporary skipping")
    def test_example_notebook(self):
        my_network_uuid = 'd3c5ca09-bb42-11e7-94d3-0ac135e8bacf'
        my_account = "drh"
        my_password = "drh"

        print("downloading network and buiding NiceCX...")
        my_network = ndex2.create_nice_cx_from_server(server='public.ndexbio.org', uuid=my_network_uuid)
        print("done")
        print(my_network.get_summary())

        # (for clarity, this example code is rather verbose)

        source_attribute1 = "TYPEA"
        source_attribute2 = "TYPEB"
        target_attribute = "TYPE"

        for node_id, node in my_network.nodes.items():
            value1 = my_network.get_node_attribute(node, source_attribute1)
            value2 = my_network.get_node_attribute(node, source_attribute2)
            merged_value = value1 or value2
            if merged_value:
                my_network.set_node_attribute(node, target_attribute, merged_value)
                my_network.remove_node_attribute(node, source_attribute1)
                my_network.remove_node_attribute(node, source_attribute2)

        print(my_network.get_summary())
