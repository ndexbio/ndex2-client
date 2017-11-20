import os
import logging
import logging.handlers
import math
import json
from nicecxModel.metadata.MetaDataElement import MetaDataElement
from nicecxModel.cx.aspects.NameSpace import NameSpace
from nicecxModel.cx.aspects.NodeElement import NodeElement
from nicecxModel.cx.aspects.EdgeElement import EdgeElement
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
        my_nicecx.set_name(G.graph.get('name'))
    else:
        my_nicecx.set_name('created from networkx')

    my_nicecx.add_metadata_stub('networkAttributes')
    for n, d in G.nodes_iter(data=True):
        #=============
        # ADD NODES
        #=============
        if d and d.get('name'):
            my_nicecx.create_node(id=n, node_name=d.get('name'), node_represents=d.get('name'))
        else:
            my_nicecx.create_node(id=n, node_name=n, node_represents=n)

        #======================
        # ADD NODE ATTRIBUTES
        #======================
        for k,v in d.items():
            my_nicecx.set_node_attribute(n, k, v)

    index = 0
    for u, v, d in G.edges_iter(data=True):
        #=============
        # ADD EDGES
        #=============
        my_nicecx.create_edge(id=index, edge_source=u, edge_target=v, edge_interaction=d.get('interaction'))

        #==============================
        # ADD EDGE ATTRIBUTES
        #==============================
        for k,v in d.items():
            if k != 'interaction':
                my_nicecx.set_edge_attribute(index, k, v)

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

    if hasattr(G, 'pos'):
        G_pos = create_cartesian_coordinates_aspect_from_networkx(G)

        my_nicecx.set_opaque_aspect('cartesianLayout', G_pos.get('cartesianLayout'))
        my_nicecx.add_metadata_stub('cartesianLayout')

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
            mde = MetaDataElement(cx_fragment=ae)
            my_nicecx.add_metadata(mde)

        opaque_aspects = set(available_aspects).difference(known_aspects_min)

        #====================
        # NETWORK ATTRIBUTES
        #====================
        if 'networkAttributes' in available_aspects:
            objects = my_nicecx.get_frag_from_list_by_key(cx, 'networkAttributes')
            for network_item in objects:
                add_this_network_attribute = NetworkAttributesElement(cx_fragment=network_item)

                my_nicecx.add_network_attribute(network_attribute_element=add_this_network_attribute)
            my_nicecx.add_metadata_stub('networkAttributes')

        #===================
        # NODES
        #===================
        if 'nodes' in available_aspects:
            objects = my_nicecx.get_frag_from_list_by_key(cx, 'nodes')
            for node_item in objects:
                my_nicecx.create_node(cx_fragment=node_item)
            my_nicecx.add_metadata_stub('nodes')

        #===================
        # EDGES
        #===================
        if 'edges' in available_aspects:
            objects = my_nicecx.get_frag_from_list_by_key(cx, 'edges')
            for edge_item in objects:
                my_nicecx.create_edge(cx_fragment=edge_item)
            my_nicecx.add_metadata_stub('edges')

        #===================
        # NODE ATTRIBUTES
        #===================
        if 'nodeAttributes' in available_aspects:
            objects = my_nicecx.get_frag_from_list_by_key(cx, 'nodeAttributes')
            for att in objects:
                #my_nicecx.set_node_attribute(None, None, None, cx_fragment=att)
                node_attribute_element = NodeAttributesElement(cx_fragment=att)
                my_nicecx.nodeAttributeHeader.add(node_attribute_element.get_name())
                nodeAttrs = my_nicecx.nodeAttributes.get(node_attribute_element.get_property_of())
                if nodeAttrs is None:
                    nodeAttrs = []
                    my_nicecx.nodeAttributes[node_attribute_element.get_property_of()] = nodeAttrs

                nodeAttrs.append(node_attribute_element)
            my_nicecx.add_metadata_stub('nodeAttributes')

        #===================
        # EDGE ATTRIBUTES
        #===================
        if 'edgeAttributes' in available_aspects:
            objects = my_nicecx.get_frag_from_list_by_key(cx, 'edgeAttributes')
            for att in objects:
                #my_nicecx.set_edge_attribute(None, None, None, cx_fragment=att)
                edge_attribute_element = EdgeAttributesElement(cx_fragment=att)

                my_nicecx.edgeAttributeHeader.add(edge_attribute_element.get_name())
                edge_attrs = my_nicecx.edgeAttributes.get(att.get('po'))
                if edge_attrs is None:
                    edge_attrs = []
                    my_nicecx.edgeAttributes[edge_attribute_element.get_property_of()] = edge_attrs

                edge_attrs.append(edge_attribute_element)

            my_nicecx.add_metadata_stub('edgeAttributes')

        #===================
        # CITATIONS
        #===================
        if 'citations' in available_aspects:
            objects = my_nicecx.get_frag_from_list_by_key(cx, 'citations')
            for cit in objects:
                aspect_element = AspectElement(cit, 'citations')
                my_nicecx.add_opaque_aspect(aspect_element)

            my_nicecx.add_metadata_stub('citations')

        #===================
        # SUPPORTS
        #===================
        if 'supports' in available_aspects:
            objects = my_nicecx.get_frag_from_list_by_key(cx, 'supports')
            for sup in objects:
                aspect_element = AspectElement(sup, 'supports')
                my_nicecx.add_opaque_aspect(aspect_element)

            my_nicecx.add_metadata_stub('supports')

        #===================
        # EDGE SUPPORTS
        #===================
        if 'edgeSupports' in available_aspects:
            objects = my_nicecx.get_frag_from_list_by_key(cx, 'edgeSupports')
            for add_this_edge_sup in objects:
                aspect_element = AspectElement(add_this_edge_sup, 'edgeSupports')
                my_nicecx.add_opaque_aspect(aspect_element)

            my_nicecx.add_metadata_stub('edgeSupports')

        #===================
        # NODE CITATIONS
        #===================
        if 'nodeCitations' in available_aspects:
            objects = my_nicecx.get_frag_from_list_by_key(cx, 'nodeCitations')
            for node_cit in objects:
                aspect_element = AspectElement(node_cit, 'nodeCitations')
                my_nicecx.add_opaque_aspect(aspect_element)

            my_nicecx.add_metadata_stub('nodeCitations')

        #===================
        # EDGE CITATIONS
        #===================
        if 'edgeCitations' in available_aspects:
            objects = my_nicecx.get_frag_from_list_by_key(cx, 'edgeCitations')
            for edge_cit in objects:
                aspect_element = AspectElement(edge_cit, 'edgeCitations')
                my_nicecx.add_opaque_aspect(aspect_element)

            my_nicecx.add_metadata_stub('edgeCitations')

        #===================
        # OPAQUE ASPECTS
        #===================
        for oa in opaque_aspects:
            objects = my_nicecx.get_frag_from_list_by_key(cx, oa)
            for oa_item in objects:
                aspect_element = AspectElement(oa_item, oa)
                my_nicecx.add_opaque_aspect(aspect_element)
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
    my_nicecx.set_name('Pandas Upload')
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
            my_nicecx.create_node(id=row[source_field], node_name=row[source_field], node_represents=row[source_field])
            my_nicecx.create_node(id=row[target_field], node_name=row[target_field], node_represents=row[target_field])

            #=============
            # ADD EDGES
            #=============
            if edge_interaction:
                if row.get(edge_interaction):
                    my_nicecx.create_edge(id=index, edge_source=row[source_field], edge_target=row[target_field], edge_interaction=row[edge_interaction])
                else:
                    my_nicecx.create_edge(id=index, edge_source=row[source_field], edge_target=row[target_field], edge_interaction=edge_interaction)
            else:
                my_nicecx.create_edge(id=index, edge_source=row[source_field], edge_target=row[target_field], edge_interaction='neighbor-of')

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
                my_nicecx.set_node_attribute(row[source_field], sp, row[sp], type=attr_type)

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
                my_nicecx.set_node_attribute(row[target_field], tp, row[tp], type=attr_type)

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

                my_nicecx.set_edge_attribute(index, ep, row[ep], type=attr_type)

    else:
        for index, row in df.iterrows():
            #=============
            # ADD NODES
            #=============
            my_nicecx.create_node(id=row[0], node_name=row[0], node_represents=row[0])
            my_nicecx.create_node(id=row[1], node_name=row[1], node_represents=row[1])

            #=============
            # ADD EDGES
            #=============
            if len(row) > 2:
                my_nicecx.create_edge(id=index, edge_source=row[0], edge_target=row[1], edge_interaction=row[2])
            else:
                my_nicecx.create_edge(id=index, edge_source=row[0], edge_target=row[1], edge_interaction='interacts-with')

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
        for ae in (o for o in my_nicecx.get_aspect(uuid, 'metaData', server, username, password)):
            available_aspects.append(ae.get(CX_CONSTANTS.METADATA_NAME))
            mde = MetaDataElement(cx_fragment=ae)
            my_nicecx.add_metadata(mde)

        opaque_aspects = set(available_aspects).difference(known_aspects_min)

        #====================
        # NETWORK ATTRIBUTES
        #====================
        if 'networkAttributes' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'networkAttributes', server, username, password)
            for network_item in objects:
                my_nicecx.add_network_attribute(json_obj=network_item)
            my_nicecx.add_metadata_stub('networkAttributes')

        #===================
        # NODES
        #===================
        if 'nodes' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'nodes', server, username, password)
            for node_item in objects:
                my_nicecx.create_node(cx_fragment=node_item)
            my_nicecx.add_metadata_stub('nodes')

        #===================
        # EDGES
        #===================
        if 'edges' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'edges', server, username, password)
            for edge_item in objects:
                my_nicecx.create_edge(cx_fragment=edge_item)
            my_nicecx.add_metadata_stub('edges')

        #===================
        # NODE ATTRIBUTES
        #===================
        if 'nodeAttributes' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'nodeAttributes', server, username, password)
            for att in objects:
                #my_nicecx.set_node_attribute(att.get('po'), att.get('n'), att.get('v'), type=att.get('d'))

                node_attribute_element = NodeAttributesElement(cx_fragment=att)
                my_nicecx.nodeAttributeHeader.add(node_attribute_element.get_name())
                nodeAttrs = my_nicecx.nodeAttributes.get(node_attribute_element.get_property_of())
                if nodeAttrs is None:
                    nodeAttrs = []
                    my_nicecx.nodeAttributes[node_attribute_element.get_property_of()] = nodeAttrs

                nodeAttrs.append(node_attribute_element)

            my_nicecx.add_metadata_stub('nodeAttributes')

        #===================
        # EDGE ATTRIBUTES
        #===================
        if 'edgeAttributes' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'edgeAttributes', server, username, password)
            for att in objects:
                edge_attribute_element = EdgeAttributesElement(cx_fragment=att)

                my_nicecx.edgeAttributeHeader.add(edge_attribute_element.get_name())
                edge_attrs = my_nicecx.edgeAttributes.get(att.get('po'))
                if edge_attrs is None:
                    edge_attrs = []
                    my_nicecx.edgeAttributes[edge_attribute_element.get_property_of()] = edge_attrs

                edge_attrs.append(edge_attribute_element)

            my_nicecx.add_metadata_stub('edgeAttributes')

        #===================
        # CITATIONS
        #===================
        if 'citations' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'citations', server, username, password)
            for cit in objects:
                aspect_element = AspectElement(cit, 'citations')
                my_nicecx.add_opaque_aspect(aspect_element)

            my_nicecx.add_metadata_stub('citations')

        #===================
        # SUPPORTS
        #===================
        if 'supports' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'supports', server, username, password)
            for sup in objects:
                aspect_element = AspectElement(sup, 'supports')
                my_nicecx.add_opaque_aspect(aspect_element)

            my_nicecx.add_metadata_stub('supports')

        #===================
        # EDGE SUPPORTS
        #===================
        if 'edgeSupports' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'edgeSupports', server, username, password)
            for add_this_edge_sup in objects:
                aspect_element = AspectElement(add_this_edge_sup, 'edgeSupports')
                my_nicecx.add_opaque_aspect(aspect_element)

            my_nicecx.add_metadata_stub('edgeSupports')

        #===================
        # NODE CITATIONS
        #===================
        if 'nodeCitations' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'nodeCitations', server, username, password)
            for node_cit in objects:
                aspect_element = AspectElement(node_cit, 'nodeCitations')
                my_nicecx.add_opaque_aspect(aspect_element)

            my_nicecx.add_metadata_stub('nodeCitations')

        #===================
        # EDGE CITATIONS
        #===================
        if 'edgeCitations' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'edgeCitations', server, username, password)
            for edge_cit in objects:
                aspect_element = AspectElement(edge_cit, 'edgeCitations')
                my_nicecx.add_opaque_aspect(aspect_element)

            my_nicecx.add_metadata_stub('edgeCitations')

        #===================
        # OPAQUE ASPECTS
        #===================
        for oa in opaque_aspects:
            objects = my_nicecx.get_aspect(uuid, oa, server, username, password)
            for oa_item in objects:
                aspect_element = AspectElement(oa_item, oa)
                my_nicecx.add_opaque_aspect(aspect_element)
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

def create_cartesian_coordinates_aspect_from_networkx(G):
    return {'cartesianLayout': [
        {'node': n, 'x': float(G.pos[n][0]), 'y': float(G.pos[n][1])} for n in G.pos
    ]}

from nicecxModel.NiceCXNetwork import NiceCXNetwork
