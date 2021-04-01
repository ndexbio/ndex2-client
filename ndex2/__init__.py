# -*- coding: utf-8 -*-

from .version import __version__

import os
import logging
import logging.handlers
import json
import base64
import numpy as np
from ndex2cx.nice_cx_builder import NiceCXBuilder


def get_logger(name, level=logging.DEBUG):
    # TODO Creating a logs directory within the package installation of Python is bad
    root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    log_path = os.path.join(root, 'logs')
    if not os.path.exists(log_path):
        os.makedirs(log_path)
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


def load_matrix_to_ndex(x, x_cols, x_rows, server, username, password, name):
    """
    Testing 1
    :param X: param 1
    :type X:
    :param X_cols:
    :type X_cols:
    :param X_rows:
    :type X_rows:
    :param server:
    :type server:
    :param username:
    :type username:
    :param password:
    :type password:
    :param name:
    :type name:
    :return:
    :rtype:
    """
    if not isinstance(x, np.ndarray):
        raise Exception('Provided matrix is not of type numpy.ndarray')
    if not isinstance(x_cols, list):
        raise Exception('Provided column header is not in the correct format.  Please provide a list of strings')
    if not isinstance(x_rows, list):
        raise Exception('Provided row header is not in the correct format.  Please provide a list of strings')

    if not x.flags['C_CONTIGUOUS']:
        x = np.ascontiguousarray(x)

    serialized = base64.b64encode(x.tobytes())

    nice_cx_builder = NiceCXBuilder()
    nice_cx_builder.set_name(name)
    nice_cx_builder.add_node(name='Sim Matrix', represents='Sim Matrix')

    nice_cx_builder.add_opaque_aspect('matrix', [{'v': serialized}])
    nice_cx_builder.add_opaque_aspect('matrix_cols', [{'v': x_cols}])
    nice_cx_builder.add_opaque_aspect('matrix_rows', [{'v': x_rows}])
    nice_cx_builder.add_opaque_aspect('matrix_dtype', [{'v': x.dtype.name}])

    nice_cx = nice_cx_builder.get_nice_cx()

    ont_url = nice_cx.upload_to(server, username, password)

    return ont_url


def get_matrix_from_ndex(server, username, password, uuid):
    nice_cx = create_nice_cx_from_server(server=server, uuid=uuid, username=username, password=password)

    matrix = __get_v_from_aspect(nice_cx, 'matrix')

    matrix_cols = __get_v_from_aspect(nice_cx, 'matrix_cols')
    matrix_rows = __get_v_from_aspect(nice_cx, 'matrix_rows')
    matrix_dtype = __get_v_from_aspect(nice_cx, 'matrix_dtype')

    binary_data = base64.b64decode(matrix)

    dtype = np.dtype(matrix_dtype)
    dim = (len(matrix_rows), len(matrix_cols))

    # Create a NumPy array
    x = np.frombuffer(binary_data, dtype=dtype).reshape(dim)

    return x, matrix_cols, matrix_rows


def __get_v_from_aspect(niceCx, aspect):
    aspect_tmp = niceCx.get_opaque_aspect(aspect)
    if len(aspect_tmp) > 0:
        return aspect_tmp[0].get('v')


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
    'networkAttributes',
    'citations',
    'nodeCitations',
    'edgeCitations',
    'supports',
    '@context',
    'nodeSupports',
    'edgeSupports'
    ]


def create_empty_nice_cx():
    my_nicecx = NiceCXNetwork()
    return my_nicecx


def _create_cartesian_coordinates_aspect_from_networkx(G):
    return [
        {'node': n, 'x': float(G.pos[n][0]), 'y': float(G.pos[n][1])} for n in G.pos
    ]


def create_nice_cx_from_networkx(G):
    """
    Creates a :py:class:`~ndex2.nice_cx_network.NiceCXNetwork` based on a
    networkx graph.

    The resulting :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
    contains the nodes, edges and their attributes from the networkx graph and also
    preserves the graph 'pos' attribute as a CX cartesian coordinates aspect.

    The node name is taken from the networkx node id. Node 'represents' is
    taken from the networkx node attribute 'represents'

    :param G: networkx graph
    :type G: networkx graph
    :return: NiceCXNetwork
    :rtype: :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
    """

    niceCxBuilder = NiceCXBuilder()
    if G is None:
        raise Exception('Networkx input is empty')

    my_nicecx = NiceCXNetwork()

    if G.graph.get('name'):
        my_nicecx.set_name(G.graph.get('name'))
    else:
        my_nicecx.set_name('created from networkx')

    my_nicecx.add_metadata_stub('networkAttributes')


    #=========================================
    # Check to see if the node label is same
    # (case insensitive) as 'name' attribute
    #=========================================
    #use_node_label = False
    #for n, d in G.nodes_iter(data=True):
    #    if not isinstance(n, int) and d and d.get('name'):
    #        if n.lower() == d.get('name').lower():
    #            use_node_label = True

    #    break

    for n, d in G.nodes(data=True):
        # =============
        # ADD NODES
        # =============
        #if d and d.get('name'):
        #    if isinstance(n, int):
        #        node_id = niceCxBuilder.add_node(name=d.get('name'),represents=d.get('name'), id=n, map_node_ids=True)
        #    else:
        #        # If networkx node is of type string then maybe the 'name' atribute is no longer accurate
        #        if use_node_label:
        #            node_id = niceCxBuilder.add_node(name=n,represents=n, map_node_ids=True)
        #        else:
        #            node_id = niceCxBuilder.add_node(name=d.get('name'),represents=d.get('name'), map_node_ids=True)
        #else:
        if isinstance(n, int):
            node_id = niceCxBuilder.add_node(name=n,represents=d.get('represents'), id=n, map_node_ids=True)
        else:
            node_id = niceCxBuilder.add_node(name=n, represents=d.get('represents'), map_node_ids=True)

        # ======================
        # ADD NODE ATTRIBUTES
        # ======================
        for k, v in d.items():
            use_this_value, attr_type = niceCxBuilder._infer_data_type(v, split_string=True)

            if k == 'citation' and not isinstance(use_this_value, list):
                use_this_value = [use_this_value]
                attr_type = 'list_of_string'
            if use_this_value is not None:
                niceCxBuilder.add_node_attribute(node_id, k, use_this_value, type=attr_type)

    index = 0
    for u, v, d in G.edges(data=True):
        # =============
        # ADD EDGES
        # =============
        if d.get('interaction') is None or d.get('interaction') == 'null':
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
            if k != 'interaction':
                use_this_value, attr_type = niceCxBuilder._infer_data_type(val, split_string=True)

                if k == 'citation' and not isinstance(use_this_value, list):
                    use_this_value = [use_this_value]
                    attr_type = 'list_of_string'

                if use_this_value is not None:
                    niceCxBuilder.add_edge_attribute(property_of=index, name=k, values=use_this_value, type=attr_type)

        index += 1

    if hasattr(G, 'pos'):
        aspect = _create_cartesian_coordinates_aspect_from_networkx(G)
        niceCxBuilder.add_opaque_aspect('cartesianLayout', aspect)

    return niceCxBuilder.get_nice_cx()


def create_nice_cx_from_raw_cx(cx):
    """
    Create a :py:func:`~ndex2.nice_cx_network.NiceCXNetwork` from a
    as a `list` of `dict` objects in
    `CX format <https://www.home.ndexbio.org/data-model/>`__

    Example:

    .. code-block:: python

        import json
        import ndex2

        # cx_as_str is a str containing JSON in CX format above
        net_cx = ndex2.create_nice_cx_from_raw_cx(json.loads(cx_as_str))



    :param cx: CX as a `list` of `dict` objects
    :type cx: list
    :return: NiceCXNetwork
    :rtype: :py:func:`~ndex2.nice_cx_network.NiceCXNetwork`
    """
    if not cx:
        raise Exception('CX is empty')

    niceCxBuilder = NiceCXBuilder()

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
            niceCxBuilder._add_network_attributes_from_fragment(network_item)

    # ===================
    # NODES
    # ===================
    if 'nodes' in available_aspects:
        objects = niceCxBuilder.get_frag_from_list_by_key(cx, 'nodes')
        for node_item in objects:
            niceCxBuilder._add_node_from_fragment(node_item)

    # ===================
    # EDGES
    # ===================
    if 'edges' in available_aspects:
        objects = niceCxBuilder.get_frag_from_list_by_key(cx, 'edges')
        for edge_item in objects:
            niceCxBuilder._add_edge_from_fragment(edge_item)

    # ===================
    # NODE ATTRIBUTES
    # ===================
    if 'nodeAttributes' in available_aspects:
        objects = niceCxBuilder.get_frag_from_list_by_key(cx, 'nodeAttributes')
        for att in objects:
            niceCxBuilder._add_node_attribute_from_fragment(att)

    # ===================
    # EDGE ATTRIBUTES
    # ===================
    if 'edgeAttributes' in available_aspects:
        objects = niceCxBuilder.get_frag_from_list_by_key(cx, 'edgeAttributes')
        for att in objects:
            niceCxBuilder._add_edge_attribute_from_fragment(att)

    # ===================
    # CITATIONS
    # ===================
    if 'citations' in available_aspects:
        objects = niceCxBuilder.get_frag_from_list_by_key(cx, 'citations')
        for cit in objects:
            niceCxBuilder._add_citation_from_fragment(cit)

    # ===================
    # SUPPORTS
    # ===================
    if 'supports' in available_aspects:
        objects = niceCxBuilder.get_frag_from_list_by_key(cx, 'supports')
        for sup in objects:
            niceCxBuilder._add_supports_from_fragment(sup)

    # ===================
    # EDGE SUPPORTS
    # ===================
    if 'edgeSupports' in available_aspects:
        objects = niceCxBuilder.get_frag_from_list_by_key(cx, 'edgeSupports')
        for add_this_edge_sup in objects:
            niceCxBuilder._add_edge_supports_from_fragment(add_this_edge_sup)

    # ===================
    # NODE CITATIONS
    # ===================
    if 'nodeCitations' in available_aspects:
        objects = niceCxBuilder.get_frag_from_list_by_key(cx, 'nodeCitations')
        for node_cit in objects:
            niceCxBuilder._add_node_citations_from_fragment(node_cit)

    # ===================
    # EDGE CITATIONS
    # ===================
    if 'edgeCitations' in available_aspects:
        objects = niceCxBuilder.get_frag_from_list_by_key(cx, 'edgeCitations')
        for edge_cit in objects:
            niceCxBuilder._add_edge_citations_from_fragment(edge_cit)

    # ===================
    # OPAQUE ASPECTS
    # ===================
    for oa in opaque_aspects:
        #TODO - Add context to builder
        if oa == '@context':
            objects = niceCxBuilder.get_frag_from_list_by_key(cx, oa)
            niceCxBuilder.set_context(objects) #nice_cx.set_namespaces(objects)
        else:
            objects = niceCxBuilder.get_frag_from_list_by_key(cx, oa)
            niceCxBuilder.add_opaque_aspect(oa, objects)

    return niceCxBuilder.get_nice_cx()


def create_nice_cx_from_pandas(df, source_field=None, target_field=None,
                               source_node_attr=[], target_node_attr=[],
                               edge_attr=[], edge_interaction=None, source_represents=None, target_represents=None):
    """
    Create a :py:func:`~ndex2.nice_cx_network.NiceCXNetwork` from a pandas dataframe in which each row
    specifies one edge in the network.

    If only the df argument is provided the dataframe is treated as 'SIF' format,
    where the first two columns specify the source and target node ids of the edge
    and all other columns are ignored. The edge interaction is defaulted to "interacts-with"

    If both the source_field and target_field arguments are provided, the those and any other
    arguments refer to headers in the dataframe, controlling the mapping of columns to
    the attributes of nodes, and edges in the resulting
    :py:func:`~ndex2.nice_cx_network.NiceCXNetwork`. If a header is not
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
    :rtype: :py:func:`~ndex2.nice_cx_network.NiceCXNetwork`
    """

    my_nicecx = NiceCXNetwork()

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

            if source_represents is not None:
                source_node_id = niceCxBuilder.add_node(name=source_predicate + str(row[source_field]), represents=source_predicate + str(row[source_represents]))
            else:
                source_node_id = niceCxBuilder.add_node(name=source_predicate + str(row[source_field]), represents=source_predicate + str(row[source_field]))

            if target_represents is not None:
                target_node_id = niceCxBuilder.add_node(name=target_predicate + str(row[target_field]), represents=target_predicate + str(row[target_represents]))
            else:
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

                #TODO - need to be smarter about how data type is inferred
                #row[sp], attr_type = _infer_data_type(row[sp])

                attr_type = None

                #attr_type = None
                #if type(row[sp]) is float and math.isnan(row[sp]):
                #    row[sp] = ''
                #    attr_type = 'float'
                #elif type(row[sp]) is float and math.isinf(row[sp]):
                #    row[sp] = 'Inf'
                #    attr_type = 'float'
                #elif type(row[sp]) is float:
                #    attr_type = 'float'
                #elif isinstance(row[sp], int):
                #    attr_type = 'integer'
                if sp == 'citation' and not isinstance(row[sp], list):
                    row[sp] = [row[sp]]
                    attr_type = 'list_of_string'
                niceCxBuilder.add_node_attribute(source_node_id, sp, str(row[sp]), type=attr_type)

            # ==============================
            # ADD TARGET NODE ATTRIBUTES
            # ==============================
            for tp in target_node_attr:
                #TODO - need to be smarter about how data type is inferred
                #row[tp], attr_type = _infer_data_type(row[tp])

                attr_type = None

                #attr_type = None
                #if type(row[tp]) is float and math.isnan(row[tp]):
                #    row[tp] = ''
                #    attr_type = 'float'
                #elif type(row[tp]) is float and math.isinf(row[tp]):
                #    row[tp] = 'Inf'
                #    attr_type = 'float'
                #elif type(row[tp]) is float:
                #    attr_type = 'float'
                #elif isinstance(row[tp], int):
                #    attr_type = 'integer'

                if tp == 'citation' and not isinstance(row[tp], list):
                    row[tp] = [row[tp]]
                    attr_type = 'list_of_string'
                niceCxBuilder.add_node_attribute(target_node_id, tp, str(row[tp]), type=attr_type)

            # ==============================
            # ADD EDGE ATTRIBUTES
            # ==============================
            for ep in edge_attr:
                #TODO - need to be smarter about how data type is inferred
                #row[ep], attr_type = _infer_data_type(row[ep])

                attr_type = None

                #attr_type = None
                #if type(row[ep]) is float and math.isnan(row[ep]):
                #    row[ep] = ''
                #    attr_type = 'float'
                #elif type(row[ep]) is float and math.isinf(row[ep]):
                #    row[ep] = 'INFINITY'
                #    attr_type = 'float'

                if ep == 'citation' and not isinstance(row[ep], list):
                    row[ep] = [row[ep]]
                    attr_type = 'list_of_string'

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

    return niceCxBuilder.get_nice_cx()  # my_nicecx


def create_nice_cx_from_server(server, username=None, password=None, uuid=None):
    """
    Create a :py:func:`~ndex2.nice_cx_network.NiceCXNetwork` based on a network
    retrieved from NDEx, specified by its UUID.
    If the network is not public, then username and password arguments for an account on
    the server with permission to access the network must be supplied.

    :param server: the URL of the NDEx server hosting the network.
    :param username: the user name of an account with permission to access the network.
    :param password: the password of an account with permission to access the network.
    :param uuid: the UUID of the network.
    :return: NiceCXNetwork
    :rtype: :py:func:`~ndex2.nice_cx_network.NiceCXNetwork`
    """

    niceCxBuilder = NiceCXBuilder()

    if server and uuid:
        my_nicecx = NiceCXNetwork()

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
                niceCxBuilder._add_network_attributes_from_fragment(network_item)
                #niceCxBuilder.add_network_attribute(network_item.get('n'), network_item.get('v'), network_item.get('d'))

        # ===================
        # @CONTEXT
        # ===================
        if '@context' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, '@context', server, username, password)

            niceCxBuilder.set_context(objects) #nice_cx.set_namespaces(objects)
            #niceCxBuilder.set_context(objects)

        # ===================
        # NODES
        # ===================
        if 'nodes' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'nodes', server, username, password)
            for node_item in objects:
                niceCxBuilder._add_node_from_fragment(node_item)
                #niceCxBuilder.add_node(node_item.get('n'), node_item.get('r'), id=node_item.get('@id'))

        # ===================
        # EDGES
        # ===================
        if 'edges' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'edges', server, username, password)
            for edge_item in objects:
                niceCxBuilder._add_edge_from_fragment(edge_item)

                #niceCxBuilder.add_edge(source=edge_item.get('s'), target=edge_item.get('t'),
                #                       interaction=edge_item.get('i'), id=edge_item.get('@id'))

        # ===================
        # NODE ATTRIBUTES
        # ===================
        if 'nodeAttributes' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'nodeAttributes', server, username, password)
            for att in objects:
                niceCxBuilder._add_node_attribute_from_fragment(att)

                #niceCxBuilder.add_node_attribute(att.get('po'), att.get('n'), att.get('v'), type=att.get('d'))

        # ===================
        # EDGE ATTRIBUTES
        # ===================
        if 'edgeAttributes' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'edgeAttributes', server, username, password)
            for att in objects:
                niceCxBuilder._add_edge_attribute_from_fragment(att)

                #niceCxBuilder.add_edge_attribute(property_of=att.get('po'), name=att.get('n'),
                #                                 values=att.get('v'), type=att.get('d'))

        # ===================
        # CITATIONS
        # ===================
        if 'citations' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'citations', server, username, password)
            for cit in objects:
                niceCxBuilder._add_citation_from_fragment(cit)
                #my_nicecx.citations[cit.get('@id')] = cit

            #my_nicecx.add_metadata_stub('citations')

        # ===================
        # SUPPORTS
        # ===================
        if 'supports' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'supports', server, username, password)
            for sup in objects:
                niceCxBuilder._add_supports_from_fragment(sup)

                #my_nicecx.supports[sup.get('@id')] = sup

            #my_nicecx.add_metadata_stub('supports')

        # ===================
        # EDGE SUPPORTS
        # ===================
        if 'edgeSupports' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'edgeSupports', server, username, password)
            for add_this_edge_sup in objects:
                niceCxBuilder._add_edge_supports_from_fragment(add_this_edge_sup)

                #for po_id in add_this_edge_sup.get('po'):
                #    my_nicecx.edgeSupports[po_id] = add_this_edge_sup.get('supports')

            #my_nicecx.add_metadata_stub('edgeSupports')

        # ===================
        # NODE CITATIONS
        # ===================
        if 'nodeCitations' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'nodeCitations', server, username, password)
            for node_cit in objects:
                niceCxBuilder._add_node_citations_from_fragment(node_cit)

                #for po_id in node_cit.get('po'):
                #    my_nicecx.nodeCitations[po_id] = node_cit.get('citations')

            #my_nicecx.add_metadata_stub('nodeCitations')

        # ===================
        # EDGE CITATIONS
        # ===================
        if 'edgeCitations' in available_aspects:
            objects = my_nicecx.get_aspect(uuid, 'edgeCitations', server, username, password)
            for edge_cit in objects:
                niceCxBuilder._add_edge_citations_from_fragment(edge_cit)
                #for po_id in edge_cit.get('po'):
                #    my_nicecx.nodeCitations[po_id] = edge_cit.get('citations')

            #my_nicecx.add_metadata_stub('edgeCitations')

        # ===================
        # OPAQUE ASPECTS
        # ===================
        for oa in opaque_aspects:
            objects = my_nicecx.get_aspect(uuid, oa, server, username, password)
            niceCxBuilder.add_opaque_aspect(oa, objects)

    else:
        raise Exception('Server and uuid not specified')

    return niceCxBuilder.get_nice_cx()


def create_nice_cx_from_file(path):
    """
    Create a :py:func:`~ndex2.nice_cx_network.NiceCXNetwork` from a file
    that is in the `CX format <https://home.ndexbio.org/data-model/>`__

    :param path: the path of the CX file
    :type path: str
    :raises Exception: if `path` is not a file
    :raises OSError: if there is an error opening the `path` file
    :raises JSONDecodeError: if there is an error parsing the `path` file with
                             `json.load() <https://docs.python.org/3/library/json.html#json.load>`__
    :return: NiceCXNetwork
    :rtype: :py:func:`~ndex2.nice_cx_network.NiceCXNetwork`
    """
    if os.path.isfile(path):
        with open(path, 'r') as file_cx:
            # ====================================
            # BUILD NICECX FROM FILE
            # ====================================
            my_nicecx = create_nice_cx_from_raw_cx(json.load(file_cx))

            return my_nicecx
    else:
        raise Exception('The file ' + path + '  does not exist.')


from ndex2.nice_cx_network import NiceCXNetwork
from ndex2.client import Ndex2
