__author__ = 'aarongary'

import json
import ijson
import requests
import base64
import sys
#from urllib import urlopen
from ndex2.niceCXNetwork import NiceCXNetwork
from nicecxModel.cx.aspects.NodeElement import NodeElement
from nicecxModel.cx.aspects.EdgeElement import EdgeElement
from nicecxModel.cx.aspects.NetworkAttributesElement import NetworkAttributesElement
from nicecxModel.cx.aspects.NodeAttributesElement import NodeAttributesElement
from nicecxModel.cx.aspects.EdgeAttributesElement import EdgeAttributesElement
from nicecxModel.cx.aspects.CitationElement import CitationElement
from nicecxModel.cx.aspects.SupportElement import SupportElement
from nicecxModel.cx.aspects.AspectElement import AspectElement
from nicecxModel.metadata.MetaDataElement import MetaDataElement
from nicecxModel.cx import CX_CONSTANTS
from nicecxModel.cx import known_aspects, known_aspects_min

if sys.version_info.major == 3:
    from urllib.request import urlopen, Request, HTTPError, URLError
else:
    from urllib2 import urlopen, Request, HTTPError, URLError


class NiceCXBuilder():
    def __init__(self, cx=None, server=None, username='scratch', password='scratch', uuid=None, networkx_G=None, data=None, **attr):
        self.user_base64 = None
        self.username = None
        self.password = None
        if username and password:
            self.username = username
            self.password = password
            if sys.version_info.major == 3:
                encode_string = '%s:%s' % (username, password)
                byte_string = encode_string.encode()
                self.user_base64 = base64.b64encode(byte_string)#.replace('\n', '')
            else:
                self.user_base64 = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')

    def create_from_server(self, server, username, password, uuid):
        if server and uuid:
            niceCx = NiceCXNetwork()

            #===================
            # METADATA
            #===================
            available_aspects = []
            for ae in (o for o in self.stream_aspect(uuid, 'metaData')):
                available_aspects.append(ae.get(CX_CONSTANTS.METADATA_NAME))
                mde = MetaDataElement(json_obj=ae)
                niceCx.add_metadata(mde)

            #available_aspects = ['edges', 'nodes'] # TODO - remove this
            opaque_aspects = set(available_aspects).difference(known_aspects_min)

            print(opaque_aspects)

            #====================
            # NETWORK ATTRIBUTES
            #====================
            objects = self.stream_aspect(uuid, 'networkAttributes')
            obj_items = (o for o in objects)
            for network_item in obj_items:
                add_this_network_attribute = NetworkAttributesElement(cx_fragment=network_item)

                niceCx.add_network_attribute(add_this_network_attribute)

            #===================
            # NODES
            #===================
            objects = self.stream_aspect(uuid, 'nodes')
            obj_items = (o for o in objects)
            for node_item in obj_items:
                add_this_node = NodeElement(cx_fragment=node_item)

                niceCx.create_node(add_this_node)

            #===================
            # EDGES
            #===================
            objects = self.stream_aspect(uuid, 'edges')
            obj_items = (o for o in objects)
            for edge_item in obj_items:
                add_this_edge = EdgeElement(cx_fragment=edge_item)

                niceCx.create_edge(add_this_edge)

            #===================
            # NODE ATTRIBUTES
            #===================
            objects = self.stream_aspect(uuid, 'nodeAttributes')
            obj_items = (o for o in objects)
            for att in obj_items:
                add_this_node_att = NodeAttributesElement(json_obj=att)

                niceCx.add_node_attribute(add_this_node_att)

            #===================
            # EDGE ATTRIBUTES
            #===================
            objects = self.stream_aspect(uuid, 'edgeAttributes')
            obj_items = (o for o in objects)
            for att in obj_items:
                add_this_edge_att = EdgeAttributesElement(json_obj=att)

                niceCx.add_edge_attribute(add_this_edge_att)

            #===================
            # CITATIONS
            #===================
            objects = self.stream_aspect(uuid, 'citations')
            obj_items = (o for o in objects)
            for cit in obj_items:
                add_this_citation = CitationElement(cx_fragment=cit)

                niceCx.add_citation(add_this_citation)

            #===================
            # SUPPORTS
            #===================
            objects = self.stream_aspect(uuid, 'supports')
            obj_items = (o for o in objects)
            for sup in obj_items:
                add_this_supports = SupportElement(cx_fragment=sup)

                niceCx.add_support(add_this_supports)

            #===================
            # NODE CITATIONS
            #===================
            objects = self.stream_aspect(uuid, 'nodeCitations')
            obj_items = (o for o in objects)
            for node_cit in obj_items:
                niceCx.add_node_citations_from_cx(node_cit)

            #===================
            # EDGE CITATIONS
            #===================
            objects = self.stream_aspect(uuid, 'edgeCitations')
            obj_items = (o for o in objects)
            for edge_cit in obj_items:
                niceCx.add_edge_citations_from_cx(edge_cit)

            #===================
            # OPAQUE ASPECTS
            #===================
            for oa in opaque_aspects:
                objects = self.stream_aspect(uuid, oa)
                obj_items = (o for o in objects)
                for oa_item in obj_items:
                    aspect_element = AspectElement(oa_item, oa)
                    niceCx.add_opaque_aspect_element(aspect_element)

            return niceCx
        else:
            raise Exception('Server and uuid not specified')

    def create_from_cx(self, cx):
        niceCx = NiceCXNetwork()
        for aspect in cx:
            if 'status' in aspect :
                if aspect['status'][0]['success']:
                    continue
                else:
                    raise RuntimeError("Error in CX status aspect: " + aspect['status'][0]['error'])
            if "numberVerification" in aspect:
                # new status and numberVerification will be added when the network is output to_cx
                continue
            if 'subNetworks' in aspect:
                for subnetwork in aspect.get('subNetworks'):
                    id = subnetwork.get('@id')
                    if self.subnetwork_id != None:
                        raise ValueError("niceCX does not support collections!")
                    self.subnetwork_id = id
            elif 'cyViews' in aspect:
                for cyViews in aspect.get('cyViews'):
                    id = cyViews.get('@id')
                    if self.view_id != None:
                        raise ValueError("niceCX does not support more than one view!")
                    self.view_id = id
            elif 'metaData' in aspect:
                available_aspects = []
                for ae in (o for o in aspect.get('metaData')):
                    available_aspects.append(ae.get(CX_CONSTANTS.METADATA_NAME))
                    mde = MetaDataElement(json_obj=ae)
                    niceCx.add_metadata(mde)
                opaque_aspects = set(available_aspects).difference(known_aspects)

                continue
            elif 'provenanceHistory' in aspect:
                elements = aspect['provenanceHistory']
                if len(elements) > 0:
                    if len(elements)>1 or self.provenance :
                        raise RuntimeError('profenanceHistory aspect can only have one element.')
                    else :
                        self.provenance = elements[0]
            elif '@context' in aspect :
                elements = aspect['@context']
                if len(elements) > 0:
                    if  len(elements) > 1 or self.namespaces:
                        raise RuntimeError('@context aspect can only have one element')
                    else :
                        self.namespaces = elements[0]
            # TODO elif if it's an aspect we want to keep out we put an elif for that aspect
            else:
                self.unclassified_cx.append(aspect)

            cx = self.unclassified_cx

    def load_aspect(self, aspect_name):
        #with open('Signal1.cx', mode='r') as cx_f:
        with open('network1.cx', mode='r') as cx_f:
            aspect_json = json.loads(cx_f.read())
            for aspect in aspect_json:
                if aspect.get(aspect_name) is not None:
                    return aspect.get(aspect_name)

    def stream_all_aspects(self, uuid):
        return ijson.items(urlopen('http://dev2.ndexbio.org/v2/network/' + uuid), 'item')

    def stream_aspect(self, uuid, aspect_name):
        if aspect_name == 'metaData':
            print('http://dev2.ndexbio.org/v2/network/' + uuid + '/aspect')
            md_response = requests.get('http://dev2.ndexbio.org/v2/network/' + uuid + '/aspect')
            json_respone = md_response.json()
            return json_respone.get('metaData')
        else:
            #password_mgr = HTTPPasswordMgrWithDefaultRealm()

            #top_level_url = 'http://dev2.ndexbio.org'
            #password_mgr.add_password(None, top_level_url, self.username, self.password)
            #handler = HTTPBasicAuthHandler(password_mgr)
            #opener = build_opener(handler)
            #install_opener(opener)





            # Create an OpenerDirector with support for Basic HTTP Authentication...
            #auth_handler = HTTPBasicAuthHandler()
            #auth_handler.add_password(None, 'http://dev2.ndexbio.org', 'scratch', 'scratch')
            #opener = build_opener(auth_handler)
            # ...and install it globally so it can be used with urlopen.
            #install_opener(opener)


            request = Request('http://dev2.ndexbio.org/v2/network/' + uuid + '/aspect/' + aspect_name)
            base64string = base64.b64encode('%s:%s' % ('scratch', 'scratch'))
            request.add_header("Authorization", "Basic %s" % base64string)
            #result = urllib2.urlopen(request)


            urlopen_result = None
            try:
                urlopen_result = urlopen(request) #'http://dev2.ndexbio.org/v2/network/' + uuid + '/aspect/' + aspect_name)
            except HTTPError as e:
                print(e.code)
                return []
            except URLError as e:
                print('Other error')
                print('URL Error %s' % e.message())
                return []

            return ijson.items(urlopen_result, 'item')

    def stream_aspect_raw(self, uuid, aspect_name):
        return ijson.parse(urlopen('http://dev2.ndexbio.org/v2/network/' + uuid + '/aspect/' + aspect_name))


