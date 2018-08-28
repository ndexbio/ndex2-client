import os
import logging
import logging.handlers
import math
import json
import sys
import pickle
import base64
import binascii
import numpy as np
from ndex2cx.NiceCXBuilder import NiceCXBuilder

#from ndex2.metadata.MetaDataElement import MetaDataElement
#from ndex2.cx.aspects.NodeAttributesElement import NodeAttributesElement
#from ndex2.cx.aspects.EdgeAttributesElement import EdgeAttributesElement
#from ndex2.cx.aspects.NetworkAttributesElement import NetworkAttributesElement
#from ndex2.cx.aspects.AspectElement import AspectElement
#from ndex2.cx import CX_CONSTANTS
#from ndex2.cx.aspects import ATTRIBUTE_DATA_TYPE
#from ndex2.cx import known_aspects_min

root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
log_path = os.path.join(root, 'logs')
if not os.path.exists(log_path):
    os.makedirs(log_path)
# solr_url = 'http://localhost:8983/solr/'
# solr_url = 'http://dev2.ndexbio.org:8983/solr/'
# deprecation_message = 'This function is now deprecated. use NiceCX'
node_id_lookup = {}
edge_id_counter = 0


def get_logger(name, level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    logger.handlers = []

    formatter = logging.Formatter('%(asctime)s.%(msecs)d ' + 
                                  name + ' %(levelname)s: %(message)s', '%Y-%m-%d %H:%M:%S')

    handler = logging.handlers.TimedRotatingFileHandler(os.path.join(log_path, 'app.log'), 
                                                        when='midnight', backupCount=28)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def load_matrix_to_ndex(X, X_cols, X_rows, server, username, password, name):
    if not isinstance(X, np.ndarray):
        raise Exception('Provided matrix is not of type numpy.ndarray')
    if not isinstance(X_cols, list):
        raise Exception('Provided column header is not in the correct format.  Please provide a list of strings')
    if not isinstance(X_rows, list):
        raise Exception('Provided row header is not in the correct format.  Please provide a list of strings')

    if not X.flags['C_CONTIGUOUS']:
        X = np.ascontiguousarray(X)

    serialized = pickle.dumps(X, protocol=0) #base64.b64encode(X)

    niceCxBuilder = NiceCXBuilder()
    niceCxBuilder.set_name(name)
    node_id = niceCxBuilder.add_node(name='Sim Matrix', represents='Sim Matrix')

    niceCxBuilder.add_opaque_aspect('matrix', [{'v': serialized}])
    niceCxBuilder.add_opaque_aspect('matrix_cols', [{'v': X_cols}])
    niceCxBuilder.add_opaque_aspect('matrix_rows', [{'v': X_rows}])
    niceCxBuilder.add_opaque_aspect('matrix_dtype', [{'v': X.dtype.name}])

    niceCx = niceCxBuilder.get_nice_cx()

    print(X)
    ont_url = niceCx.upload_to(server, username, password)

    return ont_url


def get_matrix_from_ndex(server, username, password, uuid):
    print('place holder')
    X = None
    X_cols = None
    X_rows = None

    niceCx = create_nice_cx_from_server(server=server, uuid=uuid, username=username, password=password)

    matrix = __get_v_from_aspect(niceCx, 'matrix')

    matrix_cols = __get_v_from_aspect(niceCx, 'matrix_cols')
    matrix_rows = __get_v_from_aspect(niceCx, 'matrix_rows')
    matrix_dtype = __get_v_from_aspect(niceCx, 'matrix_dtype')

    missing_padding = len(matrix) % 4
    correct_pading = ''
    for i in range(0, (4 - missing_padding)):
        correct_pading += '='
    if missing_padding != 0:
        matrix += correct_pading
    bimary_data = binascii.a2b_base64(matrix)
    binary_data = base64.b64encode(bimary_data)

    #base64.decodestring(s)

    dtype = np.dtype(matrix_dtype)
    rows = matrix_rows
    cols = matrix_cols
    dim = (len(rows), len(cols))

    # Create a NumPy array, which is nothing but a glorified
    # pointer in C to the binary data in RAM
    X = np.frombuffer(binary_data, dtype=dtype)#.reshape(dim)

    return X, X_cols, X_rows


def __get_v_from_aspect(niceCx, aspect):
    aspect_tmp = niceCx.get_opaque_aspect(aspect)
    if len(aspect_tmp) > 0:
        return aspect_tmp[0].get('v')

def __string2bits(s=''):
    return [bin(ord(x))[2:].zfill(8) for x in s]

from enum import Enum

known_aspects = [
    'nodes',
    'edges',
    'nodeAttributes',
    'edgeAttributes',
    'networkAttributes',
    'provenanceHistory',
    'citations',
    'nodeCitations',
    'edgeCitations',
    'supports',
    'nodeSupports',
    'edgeSupports',
    'cartesianLayout',
    '@context',
    'cyVisualProperties',
    'visualProperties'
    ]

known_aspects_min = [
    'nodes',
    'edges',
    'nodeAttributes',
    'edgeAttributes',
    'networkAttributes'
    ]




def add_node(nice_cx, name=None, represents=None):
    if node_id_lookup.get(name) is None:
        source_id = nice_cx.get_next_node_id()
        node_id_lookup[name] = source_id

        nice_cx.add_node(id=node_id_lookup.get(name), name=name, represents=represents)

    return node_id_lookup.get(name)


def create_empty_nice_cx(user_agent=''):
    my_nicecx = NiceCXNetwork(user_agent)
    return my_nicecx


def _create_cartesian_coordinates_aspect_from_networkx(G):
    return [
        {'node': n, 'x': float(G.pos[n][0]), 'y': float(G.pos[n][1])} for n in G.pos
    ]


def create_nice_cx_from_networkx(G, user_agent=''):
    """
    Create a NiceCXNetwork based on a networkx graph. The resulting NiceCXNetwork
    contains the nodes edges and their attributes from the networkx graph and also
    preserves the graph 'pos' attribute as a CX cartesian coordinates aspect.

    :param G: networkx graph
    :type G: networkx graph
    :return: NiceCXNetwork
    :rtype: NiceCXNetwork
    """

    niceCxBuilder = NiceCXBuilder()

    if G is None:
        raise Exception('Networkx input is empty')

    my_nicecx = NiceCXNetwork(user_agent)

    if G.graph.get('name'):
        my_nicecx.set_name(G.graph.get('name'))
    else:
        my_nicecx.set_name('created from networkx')

    my_nicecx.add_metadata_stub('networkAttributes')
    for n, d in G.nodes_iter(data=True):
        # =============
        # ADD NODES
        # =============
        if d and d.get('name'):
            if isinstance(n, int):
                node_id = niceCxBuilder.add_node(name=d.get('name'),represents=d.get('name'), id=n)
            else:
                node_id = niceCxBuilder.add_node(name=d.get('name'),represents=d.get('name'))
        else:
            if isinstance(n, int):
                node_id = niceCxBuilder.add_node(name=n,represents=n, id=n)
            else:
                node_id = niceCxBuilder.add_node(name=n, represents=n)

        # ======================
        # ADD NODE ATTRIBUTES
        # ======================
        for k, v in d.items():
            node_attr_valid = True
            attr_type = None
            if isinstance(v, float):
                if math.isnan(v):
                    node_attr_valid = False
                attr_type = 'float'
            elif isinstance(v, int):
                attr_type = 'integer'
            elif isinstance(v, list):
                attr_type = 'list_of_string'
            if node_attr_valid:
                niceCxBuilder.add_node_attribute(node_id, k, v, type=attr_type)

    index = 0
    for u, v, d in G.edges_iter(data=True):
        # =============
        # ADD EDGES
        # =============
        if d.get('interaction') is None:
            interaction = 'neighbor-of'
        else:
            interaction = d.get('interaction')

        if isinstance(u, int):
            niceCxBuilder.add_edge(source=u, target=v, interaction=interaction, id=index)
        else:
            niceCxBuilder.add_edge(source=niceCxBuilder.node_id_lookup.get(u), target=niceCxBuilder.node_id_lookup.get(v),
                               interaction=interaction, id=index)

        # ==============================
        # ADD EDGE ATTRIBUTES
        # ==============================
        for k, val in d.items():
            edge_valid = True
            if k != 'interaction':
                attr_type = None
                if isinstance(val, float):
                    if math.isnan(val):
                        edge_valid = False
                        val = ''
                    elif math.isinf(val):
                        val = 'INFINITY'
                    attr_type = 'float'
                elif isinstance(val, int):
                    attr_type = 'integer'

                if edge_valid:
                    niceCxBuilder.add_edge_attribute(property_of=index, name=k, values=val, type=attr_type)

        index += 1

    if hasattr(G, 'pos'):
        aspect = _create_cartesian_coordinates_aspect_from_networkx(G)
        niceCxBuilder.add_opaque_aspect('cartesianLayout', aspect)

    return niceCxBuilder.get_nice_cx()


def create_nice_cx_from_cx(cx, user_agent=''):
    """
    Create a NiceCXNetwork from a CX list.

    :param cx: a list in CX format
    :return: NiceCXNetwork
    """

    niceCxBuilder = NiceCXBuilder()

    my_nicecx = NiceCXNetwork()

    if cx:
        # ===================
        # METADATA
        # ===================
        available_aspects = []
        for ae in (o for o in niceCxBuilder.get_frag_from_list_by_key(cx, 'metaData')):
            available_aspects.append(ae.get('name'))

        opaque_aspects = set(available_aspects).difference(known_aspects_min)

        # ====================
        # NETWORK ATTRIBUTES
        # ====================
        if 'networkAttributes' in available_aspects:
            objects = niceCxBuilder.get_frag_from_list_by_key(cx, 'networkAttributes')
            for network_item in objects:
                niceCxBuilder.nice_cx.networkAttributes.append(network_item)

        # ===================
        # NODES
        # ===================
        if 'nodes' in available_aspects:
            objects = niceCxBuilder.get_frag_from_list_by_key(cx, 'nodes')
            for node_item in objects:
                niceCxBuilder.nice_cx.nodes[node_item.get('@id')] = node_item

        # ===================
        # EDGES
        # ===================
        if 'edges' in available_aspects:
            objects = niceCxBuilder.get_frag_from_list_by_key(cx, 'edges')
            for edge_item in objects:
                niceCxBuilder.nice_cx.edges[edge_item.get('@id')] = edge_item

        # ===================
        # NODE ATTRIBUTES
        # ===================
        if 'nodeAttributes' in available_aspects:
            objects = niceCxBuilder.get_frag_from_list_by_key(cx, 'nodeAttributes')
            for att in objects:
                if niceCxBuilder.nice_cx.nodeAttributes.get(att.get('po')) is None:
                    niceCxBuilder.nice_cx.nodeAttributes[att.get('po')] = []

                niceCxBuilder.nice_cx.nodeAttributes[att.get('po')].append(att)

        # ===================
        # EDGE ATTRIBUTES
        # ===================
        if 'edgeAttributes' in available_aspects:
            objects = niceCxBuilder.get_frag_from_list_by_key(cx, 'edgeAttributes')
            for att in objects:
                if niceCxBuilder.nice_cx.edgeAttributes.get(att.get('po')) is None:
                    niceCxBuilder.nice_cx.edgeAttributes[att.get('po')] = []

                    niceCxBuilder.nice_cx.edgeAttributes[att.get('po')].append(att)

        # ===================
        # CITATIONS
        # ===================
        if 'citations' in available_aspects:
            objects = niceCxBuilder.get_frag_from_list_by_key(cx, 'citations')
            for cit in objects:
                my_nicecx.citations[cit.get('@id')] = cit

            my_nicecx.add_metadata_stub('citations')

        # ===================
        # SUPPORTS
        # ===================
        if 'supports' in available_aspects:
            objects = niceCxBuilder.get_frag_from_list_by_key(cx, 'supports')
            for sup in objects:
                my_nicecx.supports[sup.get('@id')] = sup

            my_nicecx.add_metadata_stub('supports')

        # ===================
        # EDGE SUPPORTS
        # ===================
        if 'edgeSupports' in available_aspects:
            objects = niceCxBuilder.get_frag_from_list_by_key(cx, 'edgeSupports')
            for add_this_edge_sup in objects:
                for po_id in add_this_edge_sup.get('po'):
                    my_nicecx.edgeSupports[po_id] = add_this_edge_sup.get('supports')

            my_nicecx.add_metadata_stub('edgeSupports')

        # ===================
        # NODE CITATIONS
        # ===================
        if 'nodeCitations' in available_aspects:
            objects = niceCxBuilder.get_frag_from_list_by_key(cx, 'nodeCitations')
            for node_cit in objects:
                for po_id in node_cit.get('po'):
                    my_nicecx.nodeCitations[po_id] = node_cit.get('citations')

            my_nicecx.add_metadata_stub('nodeCitations')

        # ===================
        # EDGE CITATIONS
        # ===================
        if 'edgeCitations' in available_aspects:
            objects = niceCxBuilder.get_frag_from_list_by_key(cx, 'edgeCitations')
            for edge_cit in objects:
                for po_id in edge_cit.get('po'):
                    my_nicecx.nodeCitations[po_id] = edge_cit.get('citations')

            my_nicecx.add_metadata_stub('edgeCitations')

        # ===================
        # OPAQUE ASPECTS
        # ===================
        for oa in opaque_aspects:
            #TODO - Add context to builder
            if oa == '@context':
                objects = niceCxBuilder.get_frag_from_list_by_key(cx, oa)
                niceCxBuilder.nice_cx.set_namespaces(objects)
            else:
                objects = niceCxBuilder.get_frag_from_list_by_key(cx, oa)
                niceCxBuilder.nice_cx.opaqueAspects[oa] = objects

        return niceCxBuilder.get_nice_cx()
    else:
        raise Exception('CX is empty')


def create_nice_cx_from_pandas(df, source_field=None, target_field=None,
                               source_node_attr=[], target_node_attr=[],
                               edge_attr=[], edge_interaction=None, user_agent=''):
    """
    Create a NiceCXNetwork from a pandas dataframe in which each row
    specifies one edge in the network.

    If only the df argument is provided the dataframe is treated as 'SIF' format,
    where the first two columns specify the source and target node ids of the edge
    and all other columns are ignored. The edge interaction is defaulted to "interacts-with"

    If both the source_field and target_field arguments are provided, the those and any other
    arguments refer to headers in the dataframe, controlling the mapping of columns to
    the attributes of nodes, and edges in the resulting NiceCXNetwork. If a header is not
    mapped the corresponding column is ignored. If the edge_interaction is not specified it
    defaults to "interacts-with"

    :param df: pandas dataframe to process
    :param source_field: header name specifying the name of the source node.
    :param target_field: header name specifying the name of the target node.
    :param source_node_attr: list of header names specifying attributes of the source node.
    :param target_node_attr: list of header names specifying attributes of the target node.
    :param edge_attr: list of header names specifying attributes of the edge.
    :param edge_interaction: the relationship between the source node and the target node, defaulting to "interacts-with"
    :return: NiceCXNetwork
    """

    my_nicecx = NiceCXNetwork(user_agent)

    # ====================================================
    # IF NODE FIELD NAME (SOURCE AND TARGET) IS PROVIDED
    # THEN USE THOSE FIELDS OTHERWISE USE INDEX 0 & 1
    # ====================================================
    my_nicecx.set_name('Pandas Upload')
    #my_nicecx.add_metadata_stub('networkAttributes')
    count = 0
    source_predicate = ''
    target_predicate = ''

    niceCxBuilder = NiceCXBuilder()

    if source_field and target_field:
        for index, row in df.iterrows():
            if count % 1000 == 0:
                print(count)
            count += 1
            # =============
            # ADD NODES
            # =============
            source_node_id = niceCxBuilder.add_node(name=source_predicate + str(row[source_field]), represents=source_predicate + str(row[source_field]))
            target_node_id = niceCxBuilder.add_node(name=target_predicate + str(row[target_field]), represents=target_predicate + str(row[target_field]))

            # =============
            # ADD EDGES
            # =============
            if edge_interaction:
                if row.get(edge_interaction):
                    use_this_interaction = row[edge_interaction]
                else:
                    use_this_interaction = edge_interaction
            else:
                use_this_interaction = 'interacts-with'

            niceCxBuilder.add_edge(id=index, source=source_node_id, target=target_node_id, interaction=use_this_interaction)

            # ==============================
            # ADD SOURCE NODE ATTRIBUTES
            # ==============================
            for sp in source_node_attr:
                attr_type = None
                if type(row[sp]) is float and math.isnan(row[sp]):
                    row[sp] = ''
                    attr_type = 'float'
                elif type(row[sp]) is float and math.isinf(row[sp]):
                    row[sp] = 'Inf'
                    attr_type = 'float'
                elif type(row[sp]) is float:
                    attr_type = 'float'
                elif isinstance(row[sp], int):
                    attr_type = 'integer'

                niceCxBuilder.add_node_attribute(source_node_id, sp, str(row[sp]), type=attr_type)

            # ==============================
            # ADD TARGET NODE ATTRIBUTES
            # ==============================
            for tp in target_node_attr:
                attr_type = None
                if type(row[tp]) is float and math.isnan(row[tp]):
                    row[tp] = ''
                    attr_type = 'float'
                elif type(row[tp]) is float and math.isinf(row[tp]):
                    row[tp] = 'Inf'
                    attr_type = 'float'
                elif type(row[tp]) is float:
                    attr_type = 'float'
                elif isinstance(row[tp], int):
                    attr_type = 'integer'

                niceCxBuilder.add_node_attribute(target_node_id, tp, str(row[tp]), type=attr_type)

            # ==============================
            # ADD EDGE ATTRIBUTES
            # ==============================
            for ep in edge_attr:
                attr_type = None
                if type(row[ep]) is float and math.isnan(row[ep]):
                    row[ep] = ''
                    attr_type = 'float'
                elif type(row[ep]) is float and math.isinf(row[ep]):
                    row[ep] = 'INFINITY'
                    attr_type = 'float'

                niceCxBuilder.add_edge_attribute(property_of=index, name=ep, values=row[ep], type=attr_type)

    else:
        for index, row in df.iterrows():
            # =============
            # ADD NODES
            # =============
            source_node_id = niceCxBuilder.add_node(name=str(row[0]), represents=str(row[0]))

            target_node_id = niceCxBuilder.add_node(name=str(row[1]), represents=str(row[1]))

            # =============
            # ADD EDGES
            # =============
            if len(row) > 2:
                niceCxBuilder.add_edge(id=index, source=source_node_id, target=target_node_id, interaction=row[2])
            else:
                niceCxBuilder.add_edge(id=index, source=source_node_id, target=target_node_id, interaction='interacts-with')

    return niceCxBuilder.get_nice_cx()  #my_nicecx


def create_nice_cx_from_server(server=None, username=None, password=None, uuid=None, user_agent=''):
    """
    Create a NiceCXNetwork based on a network retrieved from NDEx, specified by its UUID.
    If the network is not public, then username and password arguments for an account on
    the server with permission to access the network must be supplied.

    :param server: the URL of the NDEx server hosting the network.
    :param username: the user name of an account with permission to access the network.
    :param password: the password of an account with permission to access the network.
    :param uuid: the UUID of the network.
    :return: NiceCXNetwork
    """

    niceCxBuilder = NiceCXBuilder()

    if server and uuid:
        my_nicecx = NiceCXNetwork(user_agent)

        # ===================
        # METADATA
        # ===================
        available_aspects = []
        md_aspect_iter = my_nicecx.get_aspect(uuid, 'metaData', server, username, password)
        if md_aspect_iter:
            for ae in (o for o in md_aspect_iter):
                available_aspects.append(ae.get('name'))
        else:
            if not username or not password:
                raise Exception('Network is not available.  Username and/or password not supplied')
            else:
                raise Exception('Network not available')

        opaque_aspects = set(available_aspects).difference(known_aspects_min)

        # ====================
        # NETWORK ATTRIBUTES
        # ====================
        if 'networkAttributes' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'networkAttributes', server, username, password)
            for network_item in objects:
                niceCxBuilder.add_network_attribute(network_item.get('n'), network_item.get('v'), network_item.get('d'))

        # ===================
        # @CONTEXT
        # ===================
        if '@context' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, '@context', server, username, password)
            niceCxBuilder.set_context(objects)

        # ===================
        # NODES
        # ===================
        if 'nodes' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'nodes', server, username, password)
            for node_item in objects:
                niceCxBuilder.add_node(node_item.get('n'), node_item.get('r'), id=node_item.get('@id'))

        # ===================
        # EDGES
        # ===================
        if 'edges' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'edges', server, username, password)
            for edge_item in objects:
                niceCxBuilder.add_edge(source=edge_item.get('s'), target=edge_item.get('t'),
                                       interaction=edge_item.get('i'), id=edge_item.get('@id'))

        # ===================
        # NODE ATTRIBUTES
        # ===================
        if 'nodeAttributes' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'nodeAttributes', server, username, password)
            for att in objects:
                niceCxBuilder.add_node_attribute(att.get('po'), att.get('n'), att.get('v'), type=att.get('d'))

        # ===================
        # EDGE ATTRIBUTES
        # ===================
        if 'edgeAttributes' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'edgeAttributes', server, username, password)
            for att in objects:
                niceCxBuilder.add_edge_attribute(property_of=att.get('po'), name=att.get('n'),
                                                 values=att.get('v'), type=att.get('d'))

        # ===================
        # CITATIONS
        # ===================
        if 'citations' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'citations', server, username, password)
            for cit in objects:
                my_nicecx.citations[cit.get('@id')] = cit

            my_nicecx.add_metadata_stub('citations')

        # ===================
        # SUPPORTS
        # ===================
        if 'supports' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'supports', server, username, password)
            for sup in objects:
                my_nicecx.supports[sup.get('@id')] = sup

            my_nicecx.add_metadata_stub('supports')

        # ===================
        # EDGE SUPPORTS
        # ===================
        if 'edgeSupports' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'edgeSupports', server, username, password)
            for add_this_edge_sup in objects:
                for po_id in add_this_edge_sup.get('po'):
                    my_nicecx.edgeSupports[po_id] = add_this_edge_sup.get('supports')

            my_nicecx.add_metadata_stub('edgeSupports')

        # ===================
        # NODE CITATIONS
        # ===================
        if 'nodeCitations' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'nodeCitations', server, username, password)
            for node_cit in objects:
                for po_id in node_cit.get('po'):
                    my_nicecx.nodeCitations[po_id] = node_cit.get('citations')

            my_nicecx.add_metadata_stub('nodeCitations')

        # ===================
        # EDGE CITATIONS
        # ===================
        if 'edgeCitations' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'edgeCitations', server, username, password)
            for edge_cit in objects:
                for po_id in edge_cit.get('po'):
                    my_nicecx.nodeCitations[po_id] = edge_cit.get('citations')

            my_nicecx.add_metadata_stub('edgeCitations')

        # ===================
        # OPAQUE ASPECTS
        # ===================
        for oa in opaque_aspects:
            objects = my_nicecx.get_aspect(uuid, oa, server, username, password)
            niceCxBuilder.add_opaque_aspect(oa, objects)

    else:
        raise Exception('Server and uuid not specified')

    return niceCxBuilder.get_nice_cx()


def create_nice_cx_from_file(path, user_agent=''):
    """
    Create a NiceCXNetwork based on CX JSON from a file.

    :param path: the path from which the CX will be loaded
    :return: NiceCXNetwork
    """
    if os.path.isfile(path):
        with open(path, 'rU') as file_cx:
            # ====================================
            # BUILD NICECX FROM FILE
            # ====================================
            my_nicecx = create_nice_cx_from_cx(json.load(file_cx))
            #my_nicecx.create_from_cx()
            return my_nicecx
    else:
        raise Exception('The file ' + path + '  does not exist.')


from ndex2.NiceCXNetwork import NiceCXNetwork
from ndex2.client import Ndex2
