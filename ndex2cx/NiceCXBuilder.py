__author__ = 'aarongary'

import json
import ijson
import requests
import base64
import sys
#from urllib import urlopen
from ndex2.client import Ndex2
from ndex2.NiceCXNetwork import NiceCXNetwork
#from nicecxModel.cx.aspects.NodeElement import NodeElement
#from nicecxModel.cx.aspects.EdgeElement import EdgeElement
#from nicecxModel.cx.aspects.NetworkAttributesElement import NetworkAttributesElement
#from nicecxModel.cx.aspects.NodeAttributesElement import NodeAttributesElement
#from nicecxModel.cx.aspects.EdgeAttributesElement import EdgeAttributesElement
#from nicecxModel.cx.aspects.CitationElement import CitationElement
#from nicecxModel.cx.aspects.SupportElement import SupportElement
#from nicecxModel.cx.aspects.AspectElement import AspectElement
#from nicecxModel.metadata.MetaDataElement import MetaDataElement
#from nicecxModel.cx.aspects import ATTRIBUTE_DATA_TYPE
#from nicecxModel.cx.aspects.SimpleNode import SimpleNode
#from nicecxModel.cx import CX_CONSTANTS
#from nicecxModel.cx import known_aspects, known_aspects_min

if sys.version_info.major == 3:
    from urllib.request import urlopen, Request, HTTPBasicAuthHandler, HTTPPasswordMgrWithDefaultRealm, \
        build_opener, install_opener, HTTPError, URLError
else:
    from urllib2 import urlopen, Request, HTTPBasicAuthHandler, HTTPPasswordMgrWithDefaultRealm, \
        build_opener, install_opener, HTTPError, URLError

class NiceCXBuilder(object):
    def __init__(self, cx=None, server=None, username='scratch', password='scratch', uuid=None, networkx_G=None, data=None, **attr):
        self.nice_cx = NiceCXNetwork(user_agent='niceCx Builder')
        self.node_id_lookup = {}
        self.node_id_counter = 0
        self.edge_id_counter = 0

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

    def set_context(self, context):
        self.nice_cx.set_context(context)

    def set_name(self, network_name):

        self.nice_cx.add_network_attribute(name='name', values=network_name, type='string')

    def add_network_attribute(self, name=None, values=None, type=None, cx_element=None):
        self.nice_cx.add_network_attribute(name=name, values=values, type=type)

    def add_node(self, name=None, represents=None, id=None):
        if id is not None:
            node_id = id
            self.node_id_lookup[name] = node_id
        elif self.node_id_lookup.get(name) is not None:
            node_id = self.nice_cx.get_next_node_id()
        else:
            node_id = self.node_id_counter
            self.node_id_counter += 1
            self.node_id_lookup[name] = node_id

        self.nice_cx.add_node(id=self.node_id_lookup.get(name), name=name, represents=represents)

        return self.node_id_lookup.get(name)

    def add_edge(self, source=None, target=None, interaction=None, id=None):
        if id is not None:
            this_edge_id = id
            self.edge_id_counter = id
            self.edge_id_counter += 1
        else:
            this_edge_id = self.edge_id_counter
            self.edge_id_counter += 1

        self.nice_cx.add_edge(id=this_edge_id, source=source, target=target, interaction=interaction)

        return this_edge_id

    def add_node_attribute(self, property_of, name, value, type=None):

        self.nice_cx.add_node_attribute(property_of=property_of, name=name, values=value, type=type)

    def add_edge_attribute(self, property_of=None, name=None, values=None, type=None):

        self.nice_cx.add_edge_attribute(property_of=property_of, name=name, values=values, type=type)

    def add_opaque_aspect(self, oa_name, oa_list):
        self.nice_cx.opaqueAspects[oa_name] = oa_list

    def get_nice_cx(self):
        return self.nice_cx

    def get_frag_from_list_by_key(self, cx, key):
        for aspect in cx:
            if key in aspect:
                return aspect[key]

        return []

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


