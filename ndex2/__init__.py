import os
import logging
import logging.handlers
import math
import json
from nicecxModel.metadata.MetaDataElement import MetaDataElement
from nicecxModel.cx.aspects.NameSpaces import NameSpaces
from nicecxModel.cx.aspects.NodesElement import NodesElement
from nicecxModel.cx.aspects.EdgesElement import EdgesElement
from nicecxModel.cx.aspects.NodeAttributesElement import NodeAttributesElement
from nicecxModel.cx.aspects.EdgeAttributesElement import EdgeAttributesElement
from nicecxModel.cx.aspects.NetworkAttributesElement import NetworkAttributesElement
from nicecxModel.cx.aspects.SupportElement import SupportElement
from nicecxModel.cx.aspects.CitationElement import CitationElement
from nicecxModel.cx.aspects.AspectElement import AspectElement
from nicecxModel.cx import CX_CONSTANTS
from nicecxModel.cx.aspects import ATTRIBUTE_DATA_TYPE
from nicecxModel.cx import known_aspects, known_aspects_min

root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
log_path = os.path.join(root, 'logs')
#solr_url = 'http://localhost:8983/solr/'
solr_url = 'http://dev2.ndexbio.org:8983/solr/'
deprecation_message = 'This function is now deprecated. use NiceCX'

def get_logger(name, level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    logger.handlers = []

    formatter = logging.Formatter('%(asctime)s.%(msecs)d ' + name + ' %(levelname)s: %(message)s', '%Y-%m-%d %H:%M:%S')

    handler = logging.handlers.TimedRotatingFileHandler(os.path.join(log_path, 'app.log'), when='midnight', backupCount=28)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

def create_empty_nice_cx():
    my_nicecx = NiceCXNetwork()

    return my_nicecx

def create_nice_cx_from_networkx(G):
    """
    Constructor that uses a networkx graph to build niceCX
    :param G: networkx graph
    :type G: networkx graph
    :return: none
    :rtype: none
    """
    my_nicecx = NiceCXNetwork()

    if G.graph.get('name'):
        my_nicecx.setName(G.graph.get('name'))
    else:
        my_nicecx.setName('created from networkx')

    my_nicecx.add_metadata_stub('networkAttributes')
    for n, d in G.nodes_iter(data=True):
        #=============
        # ADD NODES
        #=============
        my_nicecx.addNode(id=n, node_name=n, node_represents=n)

        #======================
        # ADD NODE ATTRIBUTES
        #======================
        for k,v in d.items():
            my_nicecx.addNodeAttribute(property_of=n, name=k, values=v)

    index = 0
    for u, v, d in G.edges_iter(data=True):
        #=============
        # ADD EDGES
        #=============
        my_nicecx.addEdge(id=index, edge_source=u, edge_target=v, edge_interaction=d.get('interaction'))

        #==============================
        # ADD EDGE ATTRIBUTES
        #==============================
        for k,v in d.items():
            my_nicecx.addEdgeAttribute(property_of=index, name=k, values=v)

        index += 1

    #Cartesian aspect
    cartesian_aspect = []
    #for

    my_nicecx.add_metadata_stub('nodes')
    my_nicecx.add_metadata_stub('edges')
    if my_nicecx.nodeAttributes:
        my_nicecx.add_metadata_stub('nodeAttributes')
    if my_nicecx.edgeAttributes:
        my_nicecx.add_metadata_stub('edgeAttributes')

    return my_nicecx

def create_nice_cx_from_cx(cx):
    my_nicecx = NiceCXNetwork()

    if cx:
        #===================
        # METADATA
        #===================
        available_aspects = []
        for ae in (o for o in my_nicecx.get_frag_from_list_by_key(cx, 'metaData')):
            available_aspects.append(ae.get(CX_CONSTANTS.METADATA_NAME))
            mde = MetaDataElement(json_obj=ae)
            my_nicecx.addMetadata(mde)

        opaque_aspects = set(available_aspects).difference(known_aspects_min)

        #====================
        # NETWORK ATTRIBUTES
        #====================
        if 'networkAttributes' in available_aspects:
            objects = my_nicecx.get_frag_from_list_by_key(cx, 'networkAttributes')
            obj_items = (o for o in objects)
            for network_item in obj_items:
                add_this_network_attribute = NetworkAttributesElement(json_obj=network_item)

                my_nicecx.addNetworkAttribute(network_attribute_element=add_this_network_attribute)
            my_nicecx.add_metadata_stub('networkAttributes')

        #===================
        # NODES
        #===================
        if 'nodes' in available_aspects:
            objects = my_nicecx.get_frag_from_list_by_key(cx, 'nodes')
            obj_items = (o for o in objects)
            for node_item in obj_items:
                #add_this_node = NodesElement(json_obj=node_item)

                my_nicecx.addNode(json_obj=node_item)
            my_nicecx.add_metadata_stub('nodes')

        #===================
        # EDGES
        #===================
        if 'edges' in available_aspects:
            objects = my_nicecx.get_frag_from_list_by_key(cx, 'edges')
            obj_items = (o for o in objects)
            for edge_item in obj_items:
                #add_this_edge = EdgesElement(json_obj=edge_item)

                my_nicecx.addEdge(json_obj=edge_item)
            my_nicecx.add_metadata_stub('edges')

        #===================
        # NODE ATTRIBUTES
        #===================
        if 'nodeAttributes' in available_aspects:
            objects = my_nicecx.get_frag_from_list_by_key(cx, 'nodeAttributes')
            obj_items = (o for o in objects)
            for att in obj_items:
                #add_this_node_att = NodeAttributesElement(json_obj=att)

                my_nicecx.addNodeAttribute(json_obj=att)
            my_nicecx.add_metadata_stub('nodeAttributes')

        #===================
        # EDGE ATTRIBUTES
        #===================
        if 'edgeAttributes' in available_aspects:
            objects = my_nicecx.get_frag_from_list_by_key(cx, 'edgeAttributes')
            obj_items = (o for o in objects)
            for att in obj_items:
                #add_this_edge_att = EdgeAttributesElement(json_obj=att)

                my_nicecx.addEdgeAttribute(json_obj=att)
            my_nicecx.add_metadata_stub('edgeAttributes')

        #===================
        # CITATIONS
        #===================
        if 'citations' in available_aspects:
            objects = my_nicecx.get_frag_from_list_by_key(cx, 'citations')
            obj_items = (o for o in objects)
            for cit in obj_items:
                add_this_citation = CitationElement(json_obj=cit)

                my_nicecx.addCitation(add_this_citation)
            my_nicecx.add_metadata_stub('citations')

        #===================
        # SUPPORTS
        #===================
        if 'supports' in available_aspects:
            objects = my_nicecx.get_frag_from_list_by_key(cx, 'supports')
            obj_items = (o for o in objects)
            for sup in obj_items:
                add_this_supports = SupportElement(json_obj=sup)

                my_nicecx.addSupport(add_this_supports)
            my_nicecx.add_metadata_stub('supports')

        #===================
        # EDGE SUPPORTS
        #===================
        if 'edgeSupports' in available_aspects:
            objects = my_nicecx.get_frag_from_list_by_key(cx, 'edgeSupports')
            obj_items = (o for o in objects)
            for add_this_edge_sup in obj_items:
                my_nicecx.addEdgeSupports(add_this_edge_sup)

            my_nicecx.add_metadata_stub('edgeSupports')

        #===================
        # NODE CITATIONS
        #===================
        if 'nodeCitations' in available_aspects:
            objects = my_nicecx.get_frag_from_list_by_key(cx, 'nodeCitations')
            obj_items = (o for o in objects)
            for node_cit in obj_items:
                my_nicecx.addNodeCitationsFromCX(node_cit)
            my_nicecx.add_metadata_stub('nodeCitations')

        #===================
        # EDGE CITATIONS
        #===================
        if 'edgeCitations' in available_aspects:
            objects = my_nicecx.get_frag_from_list_by_key(cx, 'edgeCitations')
            obj_items = (o for o in objects)
            for edge_cit in obj_items:
                my_nicecx.addEdgeCitationsFromCX(edge_cit)
            my_nicecx.add_metadata_stub('edgeCitations')

        #===================
        # OPAQUE ASPECTS
        #===================
        for oa in opaque_aspects:
            objects = my_nicecx.get_frag_from_list_by_key(cx, oa)
            obj_items = (o for o in objects)
            for oa_item in obj_items:
                aspect_element = AspectElement(oa_item, oa)
                my_nicecx.addOpaqueAspect(aspect_element)
                my_nicecx.add_metadata_stub(oa)

        return my_nicecx
    else:
        raise Exception('CX is empty')

def create_nice_cx_from_pandas(df, source_field=None, target_field=None, source_node_attr=[], target_node_attr=[], edge_attr=[], edge_interaction=None):
    """
    Constructor that uses a pandas dataframe to build niceCX
    :param df: dataframe
    :type df: Pandas Dataframe
    :param headers:
    :type headers:
    :return: none
    :rtype: n/a
    """

    my_nicecx = NiceCXNetwork()

    #====================================================
    # IF NODE FIELD NAME (SOURCE AND TARGET) IS PROVIDED
    # THEN USE THOSE FIELDS OTHERWISE USE INDEX 0 & 1
    #====================================================
    my_nicecx.setName('Pandas Upload')
    my_nicecx.add_metadata_stub('networkAttributes')
    count = 0
    if source_field and target_field:
        for index, row in df.iterrows():
            if count % 10000 == 0:
                print(count)
            count += 1
            #=============
            # ADD NODES
            #=============
            my_nicecx.addNode(id=row[source_field], node_name=row[source_field], node_represents=row[source_field])
            my_nicecx.addNode(id=row[target_field], node_name=row[target_field], node_represents=row[target_field])

            #=============
            # ADD EDGES
            #=============
            if edge_interaction:
                if row.get(edge_interaction):
                    my_nicecx.addEdge(id=index, edge_source=row[source_field], edge_target=row[target_field], edge_interaction=row[edge_interaction])
                else:
                    my_nicecx.addEdge(id=index, edge_source=row[source_field], edge_target=row[target_field], edge_interaction=edge_interaction)
            else:
                my_nicecx.addEdge(id=index, edge_source=row[source_field], edge_target=row[target_field], edge_interaction='neighbor-of')

            #==============================
            # ADD SOURCE NODE ATTRIBUTES
            #==============================
            for sp in source_node_attr:
                attr_type = None
                if type(row[sp]) is float and math.isnan(row[sp]):
                    row[sp] = ''
                    attr_type = ATTRIBUTE_DATA_TYPE.FLOAT
                elif type(row[sp]) is float and math.isinf(row[sp]):
                    row[sp] = 'Inf'
                    attr_type = ATTRIBUTE_DATA_TYPE.FLOAT
                my_nicecx.addNodeAttribute(property_of=row[source_field], name=sp, values=row[sp], type=attr_type)

            #==============================
            # ADD TARGET NODE ATTRIBUTES
            #==============================
            for tp in target_node_attr:
                attr_type = None
                if type(row[tp]) is float and math.isnan(row[tp]):
                    row[tp] = ''
                    attr_type = ATTRIBUTE_DATA_TYPE.FLOAT
                elif type(row[tp]) is float and math.isinf(row[tp]):
                    row[tp] = 'Inf'
                    attr_type = ATTRIBUTE_DATA_TYPE.FLOAT
                my_nicecx.addNodeAttribute(property_of=row[target_field], name=tp, values=row[tp], type=attr_type)

            #==============================
            # ADD EDGE ATTRIBUTES
            #==============================
            for ep in edge_attr:
                attr_type = None
                if type(row[ep]) is float and math.isnan(row[ep]):
                    row[ep] = ''
                    attr_type = ATTRIBUTE_DATA_TYPE.FLOAT
                elif type(row[ep]) is float and math.isinf(row[ep]):
                    row[ep] = 'INFINITY'
                    attr_type = ATTRIBUTE_DATA_TYPE.FLOAT

                my_nicecx.addEdgeAttribute(property_of=index, name=ep, values=row[ep], type=attr_type)

    else:
        for index, row in df.iterrows():
            #=============
            # ADD NODES
            #=============
            my_nicecx.addNode(id=row[0], node_name=row[0], node_represents=row[0])
            my_nicecx.addNode(id=row[1], node_name=row[1], node_represents=row[1])

            #=============
            # ADD EDGES
            #=============
            if len(row) > 2:
                my_nicecx.addEdge(id=index, edge_source=row[0], edge_target=row[1], edge_interaction=row[2])
            else:
                my_nicecx.addEdge(id=index, edge_source=row[0], edge_target=row[1], edge_interaction='interacts-with')

    my_nicecx.add_metadata_stub('nodes')
    my_nicecx.add_metadata_stub('edges')
    if source_node_attr or target_node_attr:
        my_nicecx.add_metadata_stub('nodeAttributes')
    if edge_attr:
        my_nicecx.add_metadata_stub('edgeAttributes')

    return my_nicecx

def create_nice_cx_from_server(server=None, username=None, password=None, uuid=None):
    if server and uuid:
        my_nicecx = NiceCXNetwork()

        #===================
        # METADATA
        #===================
        available_aspects = []
        for ae in (o for o in my_nicecx.streamAspect(uuid, 'metaData', server, username, password)):
            available_aspects.append(ae.get(CX_CONSTANTS.METADATA_NAME))
            mde = MetaDataElement(json_obj=ae)
            my_nicecx.addMetadata(mde)

        opaque_aspects = set(available_aspects).difference(known_aspects_min)

        #====================
        # NETWORK ATTRIBUTES
        #====================
        if 'networkAttributes' in available_aspects:
            objects = my_nicecx.streamAspect(uuid, 'networkAttributes', server, username, password)
            obj_items = (o for o in objects)
            for network_item in obj_items:
                #add_this_network_attribute = NetworkAttributesElement(json_obj=network_item)

                my_nicecx.addNetworkAttribute(json_obj=network_item)
            my_nicecx.add_metadata_stub('networkAttributes')

        #===================
        # NODES
        #===================
        if 'nodes' in available_aspects:
            objects = my_nicecx.streamAspect(uuid, 'nodes', server, username, password)
            obj_items = (o for o in objects)
            for node_item in obj_items:
                #add_this_node = NodesElement(json_obj=node_item)

                my_nicecx.addNode(json_obj=node_item)
            my_nicecx.add_metadata_stub('nodes')

        #===================
        # EDGES
        #===================
        if 'edges' in available_aspects:
            objects = my_nicecx.streamAspect(uuid, 'edges', server, username, password)
            obj_items = (o for o in objects)
            for edge_item in obj_items:
                #add_this_edge = EdgesElement(json_obj=edge_item)

                my_nicecx.addEdge(json_obj=edge_item)
            my_nicecx.add_metadata_stub('edges')

        #===================
        # NODE ATTRIBUTES
        #===================
        if 'nodeAttributes' in available_aspects:
            objects = my_nicecx.streamAspect(uuid, 'nodeAttributes', server, username, password)
            obj_items = (o for o in objects)
            for att in obj_items:
                #add_this_node_att = NodeAttributesElement(json_obj=att)

                my_nicecx.addNodeAttribute(json_obj=att)
            my_nicecx.add_metadata_stub('nodeAttributes')

        #===================
        # EDGE ATTRIBUTES
        #===================
        if 'edgeAttributes' in available_aspects:
            objects = my_nicecx.streamAspect(uuid, 'edgeAttributes', server, username, password)
            obj_items = (o for o in objects)
            for att in obj_items:
                #add_this_edge_att = EdgeAttributesElement(json_obj=att)

                my_nicecx.addEdgeAttribute(json_obj=att)
            my_nicecx.add_metadata_stub('edgeAttributes')

        #===================
        # CITATIONS
        #===================
        if 'citations' in available_aspects:
            objects = my_nicecx.streamAspect(uuid, 'citations', server, username, password)
            obj_items = (o for o in objects)
            for cit in obj_items:
                add_this_citation = CitationElement(json_obj=cit)

                my_nicecx.addCitation(add_this_citation)
            my_nicecx.add_metadata_stub('citations')

        #===================
        # SUPPORTS
        #===================
        if 'supports' in available_aspects:
            objects = my_nicecx.streamAspect(uuid, 'supports', server, username, password)
            obj_items = (o for o in objects)
            for sup in obj_items:
                add_this_supports = SupportElement(json_obj=sup)

                my_nicecx.addSupport(add_this_supports)
            my_nicecx.add_metadata_stub('supports')

        #===================
        # EDGE SUPPORTS
        #===================
        if 'edgeSupports' in available_aspects:
            objects = my_nicecx.streamAspect(uuid, 'edgeSupports', server, username, password)
            obj_items = (o for o in objects)
            for add_this_edge_sup in obj_items:
                my_nicecx.addEdgeSupports(add_this_edge_sup)

            my_nicecx.add_metadata_stub('edgeSupports')

        #===================
        # NODE CITATIONS
        #===================
        if 'nodeCitations' in available_aspects:
            objects = my_nicecx.streamAspect(uuid, 'nodeCitations', server, username, password)
            obj_items = (o for o in objects)
            for node_cit in obj_items:
                my_nicecx.addNodeCitationsFromCX(node_cit)
            my_nicecx.add_metadata_stub('nodeCitations')

        #===================
        # EDGE CITATIONS
        #===================
        if 'edgeCitations' in available_aspects:
            objects = my_nicecx.streamAspect(uuid, 'edgeCitations', server, username, password)
            obj_items = (o for o in objects)
            for edge_cit in obj_items:
                my_nicecx.addEdgeCitationsFromCX(edge_cit)
            my_nicecx.add_metadata_stub('edgeCitations')

        #===================
        # OPAQUE ASPECTS
        #===================
        for oa in opaque_aspects:
            objects = my_nicecx.streamAspect(uuid, oa, server, username, password)
            obj_items = (o for o in objects)
            for oa_item in obj_items:
                aspect_element = AspectElement(oa_item, oa)
                my_nicecx.addOpaqueAspect(aspect_element)
                my_nicecx.add_metadata_stub(oa)
    else:
        raise Exception('Server and uuid not specified')

    return my_nicecx

def create_nice_cx_from_filename(filename):
    if os.path.isfile(filename):
        my_nicecx = NiceCXNetwork()
        with open(filename, 'rU') as file_cx:
            #====================================
            # BUILD NICECX FROM FILE
            #====================================
            my_nicecx.create_from_cx(json.load(file_cx))
            return my_nicecx
    else:
        raise Exception('The file provided does not exist.')

from nicecxModel.NiceCXNetwork import NiceCXNetwork
