__author__ = 'aarongary'

import unittest

import json
import pandas as pd
import csv
import networkx as nx
import ndex2
import os
from ndex2cx.nice_cx_builder import NiceCXBuilder
import requests
import json
import base64
import ndex2

upload_server = 'dev.ndexbio.org'
upload_username = 'scratch'
upload_password = 'scratch'

path_this = os.path.dirname(os.path.abspath(__file__))


class TestDiffusion(unittest.TestCase):
    #@unittest.skip("Temporary skipping")
    def test_diffusion(self):
        print('Testing: diffusion')
        anon_ndex = ndex2.client.Ndex2("http://public.ndexbio.org")

        G = ndex2.create_nice_cx_from_server(server='http://public.ndexbio.org',
                                             uuid='c0e70804-d848-11e6-86b1-0ac135e8bacf')

        nodeid = G.get_node_by_name('CMTM2').get('@id')

        node_attr_to_change = G.get_node_attribute(nodeid, 'diffusion_input')
        node_attr_to_change['v'] = '1.0'

        print(G.get_node_attributes(nodeid))


        RG = G.to_networkx()


        for node_id, node in G.get_nodes():
            if G.get_node_attributes(node) is not None:
                for attr in G.get_node_attributes(node):
                    if isinstance(attr['v'], dict) or isinstance(attr['v'], list):
                        attr['v'] = json.dumps(attr['v'])
                    elif not isinstance(attr['v'], str):
                        attr['v'] = str(attr['v'])


        #for node_id, node in G.get_nodes():
        #    aliases = G.get_node_attribute(node_id, 'aliases')
        #    aliases['v'] = json.dumps(aliases.get('v'))
            #G.remove_node_attribute(node_id, 'aliases')

        url = 'http://v3.heat-diffusion.cytoscape.io'
        payload = G.to_cx()
        headers = {'content-type': 'application/json'}
        response = requests.post(url, data=json.dumps(payload), headers=headers)

        nos = []
        response_json = response.json()['data']

        with open('diffusion_response1.cx', "w") as text_file:
            text_file.write(json.dumps(response_json))

        network = ndex2.create_nice_cx_from_raw_cx(response.json()['data'])
        R = network.to_networkx()
        nos = []
        for n in R.nodes():
            if int(R.node[n]['diffusion_output_rank']) < 10:
                R.node[n]['nid'] = n
                nos.append(R.node[n])
        nos = sorted(nos, key=lambda k: k['diffusion_output_rank'])
        for no in nos:
            print("id: " + str(no['nid']) + " name: " + no['nid'] + " rank: " + str(
                no['diffusion_output_rank']) + " heat: " + str(no['diffusion_output_heat']))



