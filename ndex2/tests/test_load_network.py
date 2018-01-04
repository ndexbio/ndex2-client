__author__ = 'aarongary'

import unittest

import sys
import time
import ijson
import pickle
import json
from ndex2.NiceCXNetwork import NiceCXNetwork
from nicecxModel.cx.aspects.NodeElement import NodeElement
from nicecxModel.cx.aspects.EdgeElement import EdgeElement
from nicecxModel.cx.aspects.NetworkAttributesElement import NetworkAttributesElement
from nicecxModel.cx.aspects.NodeAttributesElement import NodeAttributesElement
from nicecxModel.cx.aspects.EdgeAttributesElement import EdgeAttributesElement
from nicecxModel.cx.aspects.CitationElement import CitationElement
from nicecxModel.cx.aspects.SupportElement import SupportElement
from nicecxModel.cx.aspects import ATTRIBUTE_DATA_TYPE
from nicecxModel.cx.aspects.SimpleNode import SimpleNode
from nicecxModel.NetworkQuery import NetworkQuery
import ndex2
from nicecxModel.NiceCXBuilder import NiceCXBuilder

if sys.version_info.major == 3:
    from urllib.request import urlopen
else:
    from urllib import urlopen


def get_nodes():
    for number in range(0, 10000):
        yield_this = SimpleNode(id=str(number), node_name='Node' + str(number), node_represents='Node' + str(number))
        #yield_this = NodesElement(id=str(number), node_name='Node' + str(number), node_represents='Node' + str(number))
        #yield_this = {'@id': str(number), 'n': 'Node' + str(number), 'r': 'Node' + str(number)}
        yield yield_this

if False:
    node_getter = get_nodes()

    node_array = []

    for node in node_getter:
        node_array.append(node)

    serialized = pickle.dumps(node_array, protocol=0)
    print('Serialized memory:', sys.getsizeof(serialized))


    print(len(node_array))


def loadAspect(aspect_name):
    #with open('Signal1.cx', mode='r') as cx_f:
    with open('network1.cx', mode='r') as cx_f:
        aspect_json = json.loads(cx_f.read())
        for aspect in aspect_json:
            if aspect.get(aspect_name) is not None:
                return aspect.get(aspect_name)


class MyTestCase(unittest.TestCase):
    def test_ndex_load_cx_model(self):
        niceCxBuilder = NiceCXBuilder()
        #nice_cx_from_builder = niceCxBuilder.create_from_server('http://dev2.ndexbio.org', 'scratch', 'scratch', '94766028-934d-11e7-9743-0660b7976219')
        nice_cx = ndex2.create_nice_cx_from_server(server='dev2.ndexbio.org', username='scratch', password='scratch', uuid='94766028-934d-11e7-9743-0660b7976219')
        print(nice_cx)
        #ndex = Ndex(server='http://dev2.ndexbio.org', username='scratch', password='scratch', uuid='94766028-934d-11e7-9743-0660b7976219')
        #cx = ndex.get_network_as_cx_stream(uuid).json()
        #if not cx:


    @unittest.skip("Temporary skipping")
    def test_nice_cx_model(self):

        niceCx = NiceCXNetwork()
        #main_map = NdexGraph(server='http://dev2.ndexbio.org', username='scratch', password='scratch', uuid='7246d8cf-c644-11e6-b48c-0660b7976219')

        uuid = '6b968fd2-02a4-11e6-b550-06603eb7f303'

        #====================
        # NETWORK QUERY
        #====================

        networkQuery = NetworkQuery()
        networkQuery.query_network('40f1def0-3aa4-11e7-b12f-0660b7976219', 'HSPA5,HSPA4')

        my_na = NodeAttributesElement(subnetwork=1, property_of=11, name=22, values=33, type=ATTRIBUTE_DATA_TYPE.convert_to_data_type('string'))

        #====================
        # NETWORK ATTRIBUTES
        #====================
        #objects = ijson.items(urlopen('http://dev2.ndexbio.org/v2/network/' + uuid + '/aspect/nodes'), 'item')
        objects = loadAspect('networkAttributes')
        obj_items = (o for o in objects)
        for network_item in obj_items:
            add_this_network_attribute = NetworkAttributesElement(cx_fragment=network_item)

            niceCx.add_network_attribute(add_this_network_attribute)

        #===================
        # NODES
        #===================
        #objects = ijson.items(urlopen('http://dev2.ndexbio.org/v2/network/' + uuid + '/aspect/nodes'), 'item')
        objects = loadAspect('nodes')
        obj_items = (o for o in objects)
        for node_item in obj_items:
            add_this_node = NodeElement(json_obj=node_item)

            niceCx.create_node(add_this_node)

        #===================
        # EDGES
        #===================
        #objects = ijson.items(urlopen('http://dev2.ndexbio.org/v2/network/' + uuid + '/aspect/edges'), 'item')

        objects = loadAspect('edges')
        obj_items = (o for o in objects)
        for edge_item in obj_items:
            add_this_edge = EdgeElement(json_obj=edge_item)

            niceCx.create_edge(add_this_edge)

        #===================
        # NODE ATTRIBUTES
        #===================
        #objects = ijson.items(urlopen('http://dev2.ndexbio.org/v2/network/' + uuid + '/aspect/nodeAttributes'), 'item')
        objects = loadAspect('nodeAttributes')
        obj_items = (o for o in objects)
        for att in obj_items:
            add_this_node_att = NodeAttributesElement(json_obj=att)

            niceCx.add_node_attribute(add_this_node_att)

        #===================
        # EDGE ATTRIBUTES
        #===================
        #objects = ijson.items(urlopen('http://dev2.ndexbio.org/v2/network/' + uuid + '/aspect/edgeAttributes'), 'item')
        objects = loadAspect('edgeAttributes')
        obj_items = (o for o in objects)
        for att in obj_items:
            add_this_edge_att = EdgeAttributesElement(json_obj=att)

            niceCx.add_edge_attribute(add_this_edge_att)

        #===================
        # CITATIONS
        #===================
        #objects = ijson.items(urlopen('http://dev2.ndexbio.org/v2/network/' + uuid + '/aspect/edgeAttributes'), 'item')
        objects = loadAspect('citations')
        obj_items = (o for o in objects)
        for cit in obj_items:
            add_this_citation = CitationElement(cx_fragment=cit)

            niceCx.add_citation(add_this_citation)

        #===================
        # SUPPORTS
        #===================
        objects = loadAspect('supports')
        obj_items = (o for o in objects)
        for sup in obj_items:
            add_this_supports = SupportElement(cx_fragment=sup)

            niceCx.add_support(add_this_supports)

        #===================
        # NODE CITATIONS
        #===================
        objects = loadAspect('nodeCitations')
        obj_items = (o for o in objects)
        for node_cit in obj_items:
            niceCx.add_node_citations_from_cx(node_cit)

        #===================
        # EDGE CITATIONS
        #===================
        objects = loadAspect('edgeCitations')
        obj_items = (o for o in objects)
        for edge_cit in obj_items:
            niceCx.add_edge_citations_from_cx(edge_cit)

        nice_cx_json = niceCx.to_cx()

#        serialized = pickle.dumps(niceCx, protocol=0)
#        print 'Serialized memory:', sys.getsizeof(serialized)


        print('starting to_pandas_dataframe')
        niceCx.to_pandas_dataframe()
        parser = ijson.parse(urlopen('http://dev2.ndexbio.org/v2/network/' + uuid + '/aspect/nodes'))

        node_id, node_n, node_r = '', '', ''
        edge_id, edge_s, edge_t, edge_i = '', '', '', ''
        node_matches = {}
        edge_matches = {}
        edge_connected = {}
        node_found = False
        edge_found = False
        count = 0
        done_searching = False

        start_time = time.time()

        for prefix, event, value in parser:
            if (prefix) == ('item.@id'):
                if count % 10000 == 0:
                    print(count)
                count += 1
                node_id = value
            elif (prefix) == ('item.n'):
                node_n = value
                node_found = True
            elif (prefix) == ('item.r'):
                node_r = value
                if node_found:
                    node_matches[node_id] = {'n': node_n, 'r': node_r}
                    add_this_node = NodeElement(id=node_id, node_name=node_n, node_represents=node_r)
                    niceCx.create_node(add_this_node)
                    node_found = False
            else:
                # No represents found
                if node_found:
                    node_matches[node_id] = {'n': node_n}
                    add_this_node = NodeElement(id=node_id, node_name=node_n)
                    niceCx.create_node(add_this_node)
                    node_found = False

        print('Response time (Node search): ' + str(time.time() - start_time))
        start_time = time.time()

        print(edge_matches)
        print(node_matches)

        parser = ijson.parse(urlopen('http://dev2.ndexbio.org/v2/network/' + uuid + '/aspect/edges'))

        for prefix, event, value in parser:
            if (prefix) == ('item.@id'):
                edge_id = value
            elif (prefix) == ('item.s'):
                edge_s = value
                edge_found = True
            elif (prefix) == ('item.t'):
                edge_t = value
                edge_found = True
            elif (prefix) == ('item.i'):
                edge_i = value
                if edge_found:
                    edge_matches[edge_id] = {'s': edge_s, 't': edge_t, 'i': edge_i}
                    add_this_edge = EdgeElement(id=edge_id, edge_source=edge_s, edge_target=edge_t, edge_interaction=edge_i)
                    niceCx.create_edge(add_this_edge)
                    edge_connected[edge_s] = 1
                    edge_connected[edge_t] = 1
                    edge_found = False
            else:
                # No interaction found
                if edge_found:
                    edge_matches[edge_id] = {'s': edge_s, 't': edge_t}
                    add_this_edge = EdgeElement(id=edge_id, edge_source=edge_s, edge_target=edge_t)
                    niceCx.create_edge(add_this_edge)
                    edge_connected[edge_s] = 1
                    edge_connected[edge_t] = 1
                    edge_found = False

        print('Response time (Edge search): ' + str(time.time() - start_time))
        start_time = time.time()

        print(edge_matches)
        print(node_matches)

        self.assertTrue(niceCx is not None)


