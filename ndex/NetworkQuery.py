__author__ = 'aarongary'

import ndex
import ijson
from urllib import urlopen
import pysolr
from pysolr import SolrError
from ndex import solr_url
from model.NiceCXNetwork import NiceCXNetwork
from model.cx.aspects.NodesElement import NodesElement
from model.cx.aspects.EdgesElement import EdgesElement
from model.cx.aspects.NetworkAttributesElement import NetworkAttributesElement
from model.cx.aspects.NodeAttributesElement import NodeAttributesElement
from model.cx.aspects.EdgeAttributesElement import EdgeAttributesElement
from model.cx.aspects.CitationElement import CitationElement
from model.cx.aspects.SupportElement import SupportElement
from model.cx.aspects import ATTRIBUTE_DATA_TYPE
from model.cx.aspects.SimpleNode import SimpleNode
from model.cx import CX_CONSTANTS

class NetworkQuery():
    def __init__(self):
        self.query = ''

    def query_network(self, uuid, search_string):

        niceCx = NiceCXNetwork()
        #uuid = '7246d8cf-c644-11e6-b48c-0660b7976219'
        search_terms_dict = {k:1 for k in search_string.split(',')}

        solr = pysolr.Solr(solr_url + uuid + '/', timeout=10)

        try:
            results = solr.search(search_string, rows=10000)
            #search_terms_array = [int(n['id']) for n in results.docs]
            search_terms_array = {int(n['id']):1 for n in results.docs}
            if(not search_terms_array):
                return {'message': 'No nodes found'}

            print 'starting nodes 1'
            #===================
            # NODES
            #===================
            objects = self.streamAspect(uuid, 'nodes')
            obj_items = (o for o in objects)
            for node_item in obj_items:
                if search_terms_array.get(node_item.get(CX_CONSTANTS.ID.value)):
                    add_this_node = NodesElement(json_obj=node_item)

                    niceCx.addNode(add_this_node)

            print 'starting edges 1'
            #===================
            # EDGES
            #===================
            edge_count = 0
            objects = self.streamAspect(uuid, 'edges')
            obj_items = (o for o in objects)
            for edge_item in obj_items:
                if niceCx.nodes.get(edge_item.get(CX_CONSTANTS.EDGE_SOURCE_NODE_ID.value)) is not None or niceCx.nodes.get(edge_item.get(CX_CONSTANTS.EDGE_TARGET_NODE_ID.value)) is not None:
                    add_this_edge = EdgesElement(json_obj=edge_item)

                    niceCx.addEdge(add_this_edge)
                if edge_count % 1000 == 0:
                    print edge_count
                edge_count += 1

            print 'starting nodes 2'
            #===================
            # NODES
            #===================
            objects = self.streamAspect(uuid, 'nodes')
            obj_items = (o for o in objects)
            for node_item in obj_items:
                if niceCx.getMissingNodes().get(node_item.get(CX_CONSTANTS.ID.value)):
                    add_this_node = NodesElement(json_obj=node_item)

                    niceCx.addNode(add_this_node)

        except SolrError as se:
            if('404' in se.message):
                ndex.get_logger('SOLR').warning('Network not found ' + self.uuid + ' on ' + solr_url + ' server.')
                raise Exception("Network not found (SOLR)")
            else:
                ndex.get_logger('SOLR').warning('Network error ' + self.uuid + ' on ' + solr_url + ' server. ' + se.message)
                raise Exception(se.message)
            #raise SolrError(se)
        except StopIteration as si:
                ndex.get_logger('QUERY').warning("Found more than max edges.  Raising exception")
                raise StopIteration(si.message)


        nice_cx_json = niceCx.to_json()

    def streamAspect(self, uuid, aspect_name):
        return ijson.items(urlopen('http://dev2.ndexbio.org/v2/network/' + uuid + '/aspect/' + aspect_name), 'item')
