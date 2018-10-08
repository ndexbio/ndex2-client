__author__ = 'aarongary'

import unittest

import json
import pandas as pd
import csv
import networkx as nx
import ndex2
import ndex2.client as nc
import os
import base64
import numpy as np
import ndex2.client as nc
import io
import json
from time import sleep

from ndex2.nice_cx_network import NiceCXNetwork
from ndex2.client import DecimalEncoder
from ndex2cx.nice_cx_builder import NiceCXBuilder

upload_server = 'dev.ndexbio.org'
upload_username = 'scratch'
upload_password = 'scratch'

path_this = os.path.dirname(os.path.abspath(__file__))

class TestCxWriter(unittest.TestCase):

    #@unittest.skip("Temporary skipping")
    def test_cx_writer(self):
        cx_network = NiceCXNetwork()

        cx_network = NiceCXNetwork()
        cx_network.set_name('Test Name')

        a, b, c, d, e = [
            cx_network.create_node(node_name=letter)
            for letter in 'ABCDE'
        ]

        e1 = cx_network.create_edge(
            edge_source=a,
            edge_target=b,
        )

        e2 = cx_network.create_edge(
            edge_source=b,
            edge_target=c,
            edge_interaction='increases',
        )

        cx_network.add_citation(0, title='Hi')

        #s1 = SupportElement(id=0, text='Hi')
        #cx_network.add_support(s1)

        cx_network.add_node_attribute(property_of=a, name='Color', values='Red')
        cx_network.add_node_attribute(property_of=b, name='Color', values='Red')
        cx_network.add_node_attribute(property_of=c, name='Color', values='Red')
        cx_network.add_node_attribute(property_of=d, name='Color', values='Blue')
        cx_network.add_node_attribute(property_of=e, name='Color', values='Blue')

        cx_network.add_edge_attribute(property_of=e1, name='Color', values='Green')
        cx_network.add_edge_attribute(property_of=e2, name='Color', values='Purple')

        #cx_network.add_edge_citations(edge_id=e1, citation_id=c1.get_id())

        #edge_support_element_1 = {'po': [e1], 'supports': [c1.get_id()]}
        #cx_network.add_edge_supports(edge_supports_element=edge_support_element_1)

        with open('my_cx.cx', 'w') as file:
            json.dump(cx_network.to_cx(), file)