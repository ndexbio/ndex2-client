__author__ = 'aarongary'

import unittest
import json
import ijson
from urllib import urlopen
from ndex.networkn import NdexGraph
import time
from model.cx.NiceCXNetwork import NiceCXNetwork
from model.cx.aspects.NodesElement import NodesElement

class MyTestCase(unittest.TestCase):
    def test_provenance_and_profile(self):
        main_map = NdexGraph(server='http://dev2.ndexbio.org', username='scratch', password='scratch', uuid='7246d8cf-c644-11e6-b48c-0660b7976219')



        uuid = '7246d8cf-c644-11e6-b48c-0660b7976219'

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
        niceCx = NiceCXNetwork()

        start_time = time.time()

        for prefix, event, value in parser:
            if (prefix) == ('item.@id'):
                if count % 10000 == 0:
                    print count
                count += 1
                node_id = value
                #print value
            elif (prefix) == ('item.n'):
                node_n = value
                node_found = True
                #print value
            elif (prefix) == ('item.r'):
                node_r = value
                if node_found:
                    node_matches[node_id] = {'n': node_n, 'r': node_r}
                    add_this_node = NodesElement(id=node_id, node_name=node_n, node_represents=node_r)
                    niceCx.addNode(add_this_node)
                    node_found = False
                #print value
            else:
                # No represents found
                if node_found:
                    node_matches[node_id] = {'n': node_n}
                    add_this_node = NodesElement(id=node_id, node_name=node_n)
                    niceCx.addNode(add_this_node)
                    node_found = False

        print 'Response time (Node search): ' + str(time.time() - start_time)
        start_time = time.time()

        print edge_matches
        print node_matches


        parser = ijson.parse(urlopen('http://dev2.ndexbio.org/v2/network/' + uuid + '/aspect/edges'))

        for prefix, event, value in parser:
            if (prefix) == ('item.@id'):
                #if count % 10000 == 0:
                #    print count
                #count += 1
                edge_id = value
                #print value
            elif (prefix) == ('item.s'):
                edge_s = value
                edge_found = True
                #print value
            elif (prefix) == ('item.t'):
                edge_t = value
                if node_matches.get(edge_t) is not None:
                    edge_found = True
                #print value
            elif (prefix) == ('item.i'):
                edge_i = value
                if edge_found:
                    edge_matches[edge_id] = {'s': edge_s, 't': edge_t, 'i': edge_i}
                    edge_connected[edge_s] = 1
                    edge_connected[edge_t] = 1
                    edge_found = False
            else:
                # No interaction found
                if edge_found:
                    edge_matches[edge_id] = {'s': edge_s, 't': edge_t}
                    edge_connected[edge_s] = 1
                    edge_connected[edge_t] = 1
                    edge_found = False

        print 'Response time (Edge search): ' + str(time.time() - start_time)
        start_time = time.time()

        print edge_matches
        print node_matches

        self.assertTrue(niceCx is not None)


