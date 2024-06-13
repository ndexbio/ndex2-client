# -*- coding: utf-8 -*-

from .version import __version__

import os
import logging
import logging.handlers
import json
import base64
import numpy as np
from ndex2cx.nice_cx_builder import NiceCXBuilder
from ndex2.nice_cx_network import NetworkXFactory
from ndex2.exceptions import NDExNotFoundError
from ndex2.exceptions import NDExError
from ndex2.nice_cx_network import NiceCXNetwork
from ndex2.client import Ndex2
from ndex2 import constants


def get_logger(name, level=logging.DEBUG):  # pragma: no cover
    """
    Do **NOT** use. This function writes log messages to a `logs`
    directory under the ndex2 installed package which is very
    bad form

    .. deprecated:: 3.5.0
        This will eventually go away

    :param name:
    :param level:
    :return:
    """
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


def load_matrix_to_ndex(x, x_cols, x_rows, server, username, password, name):  # pragma: no cover
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


def get_matrix_from_ndex(server, username, password, uuid):  # pragma: no cover
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


def __get_v_from_aspect(niceCx, aspect):  # pragma: no cover
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
    'nodeSupports',
    'edgeSupports'
    ]


def create_empty_nice_cx():
    my_nicecx = NiceCXNetwork()
    return my_nicecx


def _create_cartesian_coordinates_aspect_from_networkx(G):
    """
    Converts networkx graph position coordinates to cartesianLayout

    .. note::

        The ``-`` on `y` is because `cartesianLayout` isn't actually
        cartesian. The `y` is inverted so lower values go higher on graph
        instead of lower

    :param G:
    :return:
    """
    return [
        {'node': n, 'x': float(G.pos[n][0]),
         'y': -float(G.pos[n][1])} for n in G.pos
    ]


def create_nice_cx_from_networkx(G):
    """
    Creates a :py:class:`~ndex2.nice_cx_network.NiceCXNetwork` based on a
    :class:`networkx.Graph` graph.

    .. versionchanged:: 3.5.0
       Major refactor to fix multiple bugs #83, #84, #90

    .. code-block:: python

        import ndex2
        import networkx as nx

        G = nx.Graph()
        G.add_node(1, someval=1.5, name='node 1')
        G.add_node(2, someval=2.5, name='node 2')
        G.add_edge(1, 2, weight=5)

        print(ndex2.create_nice_cx_from_networkx(G).to_cx())

    The resulting :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
    contains the nodes, edges and their attributes from the
    :class:`networkx.Graph`
    graph and also preserves the graph 'pos' attribute as a CX
    cartesian coordinates aspect
    :py:const:`~ndex2.constants.CARTESIAN_LAYOUT_ASPECT`
    with the values of `Y` inverted

    Description of how conversion is performed:

    **Network:**

    * Network name is set value of ``G.graph.get('name')`` or to
      ``created from networkx by ndex2.create_nice_cx_networkx()`` if
      `name` is ``None`` or not present

    **Nodes:**

    * Node id is value of ``n`` from this for loop:
      ``for n, d G.nodes(data=True):`` if ``n`` is **NOT** an
      :py:class:`int`, new ids starting from ``0`` are used

    * Node name is value of `name` attribute on the node or is
      set to id of node if `name` is not present.

    * Node `represents` is value of `represents` attribute on the
      node or set is to node `name` if ``None`` or not present

    **Edges:**

    * Interaction is value of `interaction` attribute on the edge
      or is set to ``neighbor-of`` if ``None`` or not present

    .. note::

        Data types are inferred by using :py:func:`isinstance` and
        converted to corresponding CX data types. For list items,
        only the 1st item is examined to determine type

    :param G: Graph to convert
    :type G: :class:`networkx.Graph`
    :raises Exception: if **G** parameter is ``None`` or there is another error
                       in conversion
    :return: Converted network
    :rtype: :py:class:`~ndex2.nice_cx_network.NiceCXNetwork`
    """
    cx_builder = NiceCXBuilder()
    if G is None:
        raise Exception('Networkx input is empty')

    network_name = G.graph.get('name')
    if network_name is not None:
        cx_builder.set_name(network_name)
    else:
        cx_builder.set_name('created from networkx by '
                            'ndex2.create_nice_cx_networkx()')

    for n, d in G.nodes(data=True):
        if isinstance(n, int):
            n_name = d.get('name')
            if n_name is None:
                n_name = str(n)
            node_id = cx_builder.add_node(name=n_name, represents=d.get('represents'), id=n, map_node_ids=True)
        else:
            node_id = cx_builder.add_node(name=n, represents=d.get('represents'), map_node_ids=True)

        # ======================
        # ADD NODE ATTRIBUTES
        # ======================
        for k, v in d.items():

            # if node attribute is 'name' skip it cause that will be used
            # for name of node, also skip 'represents'
            # fix for https://github.com/ndexbio/ndex2-client/issues/84
            if k == 'name' or k == 'represents':
                continue

            use_this_value, attr_type = cx_builder._infer_data_type(v, split_string=False)

            # This might go away, waiting on response to
            # https://ndexbio.atlassian.net/browse/UD-2181
            if k == 'citation' and not isinstance(use_this_value, list):
                use_this_value = [str(use_this_value)]
                attr_type = constants.LIST_OF_STRING
            if use_this_value is not None:
                cx_builder.add_node_attribute(node_id, k, use_this_value, type=attr_type)

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
            cx_builder.add_edge(source=u, target=v, interaction=interaction, id=index)
        else:
            cx_builder.add_edge(source=cx_builder.node_id_lookup.get(u), target=cx_builder.node_id_lookup.get(v),
                                interaction=interaction, id=index)

        # ==============================
        # ADD EDGE ATTRIBUTES
        # ==============================
        for k, val in d.items():
            if k == 'interaction':
                continue
            use_this_value, attr_type = cx_builder._infer_data_type(val, split_string=False)

            # This might go away, waiting on response to
            # https://ndexbio.atlassian.net/browse/UD-2181
            if k == 'citation' and not isinstance(use_this_value, list):
                use_this_value = [str(use_this_value)]
                attr_type = constants.LIST_OF_STRING

            if use_this_value is not None:
                cx_builder.add_edge_attribute(property_of=index, name=k, values=use_this_value, type=attr_type)

        index += 1

    if hasattr(G, 'pos'):
        aspect = _create_cartesian_coordinates_aspect_from_networkx(G)
        cx_builder.add_opaque_aspect(constants.CARTESIAN_LAYOUT_ASPECT,
                                     aspect)

    return cx_builder.get_nice_cx()


def create_nice_cx_from_raw_cx(cx):
    """
    Create a :py:func:`~ndex2.nice_cx_network.NiceCXNetwork` from a
    as a `list` of `dict` objects in
    `CX format <https://home.ndexbio.org/data-model/>`__

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
                               edge_attr=[], edge_interaction=None,
                               source_represents=None,
                               target_represents=None):
    """
    Create a :py:func:`~ndex2.nice_cx_network.NiceCXNetwork` from a :py:class:`pandas.DataFrame`
    in which each row specifies one edge in the network.

    .. versionchanged:: 3.5.0
        Removed print statements showing progress and network name is
        now being set

    If only the **df** argument is provided the :py:class:`pandas.DataFrame` is treated
    as 'SIF' format, where the first two columns specify the source and target node ids
    of the edge and all other columns are ignored. The edge interaction is
    defaulted to "interacts-with"

    If both the source_field and target_field arguments are provided, then those and any other
    arguments refer to headers in the :py:class:`pandas.DataFrame`, controlling the
    mapping of columns to the attributes of nodes, and edges in the resulting
    :py:func:`~ndex2.nice_cx_network.NiceCXNetwork`.

    If a header is not mapped, the corresponding column is ignored.

    If the edge_interaction is not specified, interaction is set to "interacts-with"

    .. code-block:: python

        import ndex2
        import pandas as pd

        data = {'source': ['Node 1','Node 2'],
                'target': ['Node 2','Node 3'],
                'interaction': ['helps', 'hurts']}
        df = pd.DataFrame.from_dict(data)

        net = ndex2.create_nice_cx_from_pandas(df, source_field='source',
                                               target_field='target',
                                               edge_interaction='interaction')

        print(net.get_nodes())
        print(net.get_edges())

    .. note::
        The datatype for everything added to the network is the CX string type

    .. warning::
        This method does not handle multi-edges, use PandasDataFrameToCX2NetworkFactory from ndex2.cx2
        to handle multi-edges.


    :param df: Pandas dataframe to process
    :type df: :py:class:`pandas.DataFrame`
    :param source_field: header name specifying the name of the source node.
    :type source_field: str
    :param target_field: header name specifying the name of the target node.
    :type target_field: str
    :param source_node_attr: list of header names specifying attributes of the source node.
    :type source_node_attr: list
    :param target_node_attr: list of header names specifying attributes of the target node.
    :type target_node_attr: list
    :param edge_attr: list of header names specifying attributes of the edge.
    :type edge_attr: list
    :param edge_interaction: the relationship between the source node and the
                             target node, defaulting to "interacts-with"
    :type edge_interaction: str
    :param source_represents:
    :type source_represents: str
    :param target_represents:
    :type target_represents: str
    :return: NiceCXNetwork
    :rtype: :py:func:`~ndex2.nice_cx_network.NiceCXNetwork`
    """
    # ====================================================
    # IF NODE FIELD NAME (SOURCE AND TARGET) IS PROVIDED
    # THEN USE THOSE FIELDS OTHERWISE USE INDEX 0 & 1
    # ====================================================
    source_predicate = ''
    target_predicate = ''

    cx_builder = NiceCXBuilder()
    cx_builder.set_name('created from pandas by '
                        'ndex2.create_nice_cx_from_pandas()')

    if source_field and target_field:
        for index, row in df.iterrows():

            # =============
            # ADD NODES
            # =============

            if source_represents is not None:
                source_node_id = cx_builder.add_node(name=source_predicate + str(row[source_field]),
                                                     represents=source_predicate +
                                                                   str(row[source_represents]))
            else:
                source_node_id = cx_builder.add_node(name=source_predicate + str(row[source_field]),
                                                     represents=source_predicate +
                                                                   str(row[source_field]))

            if target_represents is not None:
                target_node_id = cx_builder.add_node(name=target_predicate + str(row[target_field]),
                                                     represents=target_predicate +
                                                                   str(row[target_represents]))
            else:
                target_node_id = cx_builder.add_node(name=target_predicate + str(row[target_field]),
                                                     represents=target_predicate +
                                                                   str(row[target_field]))

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

            cx_builder.add_edge(id=index, source=source_node_id,
                                target=target_node_id,
                                interaction=use_this_interaction)

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
                cx_builder.add_node_attribute(source_node_id, sp, str(row[sp]), type=attr_type)

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
                cx_builder.add_node_attribute(target_node_id, tp, str(row[tp]), type=attr_type)

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

                cx_builder.add_edge_attribute(property_of=index,
                                              name=ep, values=row[ep],
                                              type=attr_type)

    else:
        for index, row in df.iterrows():
            # =============
            # ADD NODES
            # =============
            source_node_id = cx_builder.add_node(name=str(row[0]),
                                                 represents=str(row[0]))

            target_node_id = cx_builder.add_node(name=str(row[1]),
                                                 represents=str(row[1]))

            # =============
            # ADD EDGES
            # =============
            if len(row) > 2:
                cx_builder.add_edge(id=index,
                                    source=source_node_id,
                                    target=target_node_id,
                                    interaction=row[2])
            else:
                cx_builder.add_edge(id=index,
                                    source=source_node_id,
                                    target=target_node_id,
                                    interaction='interacts-with')

    return cx_builder.get_nice_cx()  # my_nicecx


def create_nice_cx_from_server(server, username=None, password=None, uuid=None,
                               ndex_client=None):
    """
    Create a :py:func:`~ndex2.nice_cx_network.NiceCXNetwork` based on a network
    retrieved from NDEx, specified by its UUID.

    .. versionchanged:: 3.5.0
        Code refactor and **ndex_client** parameter has been added


    If the network is not public, then **username** and **password** arguments
    (or **ndex_client** with username and password set) for an account on
    the server with permission to access the network must be supplied.

    Example usage:

    .. code-block:: python

        import ndex2

        # Download BioGRID: Protein-Protein Interactions (SARS-CoV) from NDEx
        # https://www.ndexbio.org/viewer/networks/669f30a3-cee6-11ea-aaef-0ac135e8bacf
        net_cx = ndex2.create_nice_cx_from_server(None, uuid='669f30a3-cee6-11ea-aaef-0ac135e8bacf')

    .. note::

        If **ndex_client** is not passed in, this function internally creates
        :py:class:`~ndex2.client.Ndex2` using values from parameters passed into
        this function.

    :param server: the URL of the NDEx server hosting the network
    :type server: str
    :param username: the user name of an account with permission to access the network
    :type username: str
    :param password: the password of an account with permission to access the network
    :type password: str
    :param uuid: the UUID of the network
    :type uuid: str
    :param ndex_client: Used as NDEx REST client overriding **server**, **username** and
                        **password** parameters if set
    :type ndex_client: :py:class:`~ndex2.client.Ndex2`
    :raises NDExError: If uuid is not specified
    :return: NiceCXNetwork
    :rtype: :py:func:`~ndex2.nice_cx_network.NiceCXNetwork`
    """
    if uuid is None:
        raise NDExError('uuid not specified')
    if ndex_client is None:
        ndex_client = Ndex2(server, username=username,
                            password=password, skip_version_check=True)
    client_resp = ndex_client.get_network_as_cx_stream(uuid)
    return create_nice_cx_from_raw_cx(json.loads(client_resp.content))


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

