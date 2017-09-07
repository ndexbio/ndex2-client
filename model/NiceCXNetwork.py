__author__ = 'aarongary'

import json
import pandas as pd
import networkx as nx
from StringIO import StringIO
from model.metadata.MetaDataElement import MetaDataElement
from model.cx.aspects.NameSpaces import NameSpaces
from model.cx.aspects.NodesElement import NodesElement
from model.cx.aspects.EdgesElement import EdgesElement
from model.cx.aspects.NodeAttributesElement import NodeAttributesElement
from model.cx.aspects.EdgeAttributesElement import EdgeAttributesElement
from model.cx.aspects.NetworkAttributesElement import NetworkAttributesElement
from model.cx.aspects.SupportElement import SupportElement
from model.cx.aspects.CitationElement import CitationElement
from model.cx.aspects.AspectElement import AspectElement
from model.cx import CX_CONSTANTS

class NiceCXNetwork():
    def __init__(self, cx=None, server=None, username=None, password=None, uuid=None, networkx_G=None, data=None, **attr):
        self.metadata = {}
        self.namespaces = NameSpaces()
        self.nodes = {}
        self.edges = {}
        self.citations = {}
        self.nodeCitations = {}
        self.edgeCitations = {}
        self.edgeSupports = {}
        self.nodeSupports = {}
        self.supports = {}
        self.nodeAttributes = {}
        self.edgeAttributes = {}
        self.networkAttributes = []
        self.nodeAssociatedAspects = {}
        self.edgeAssociatedAspects = {}
        self.opaqueAspects = {}
        self.provenance = None
        self.missingNodes = {}

    def addNode(self, node):
        if type(node) is NodesElement:
            self.nodes[node.getId()] = node

            if self.missingNodes.get(node.getId()) is not None:
                self.missingNodes.pop(node.getId(), None)
        else:
            raise Exception('Provided input was not of type NodesElement.')

    def addEdge(self, edge):
        if type(edge) is EdgesElement:
            self.edges[edge.getId()] = edge

            if self.nodes.get(edge.getSource()) is None:
                self.missingNodes[edge.getSource()] = 1

            if self.nodes.get(edge.getTarget()) is None:
                self.missingNodes[edge.getTarget()] = 1
        else:
            raise Exception('Provided input was not of type EdgesElement.')

    def addNetworkAttribute(self, network_attribute):
        if type(network_attribute) is NetworkAttributesElement:
            self.networkAttributes.append(network_attribute)
        else:
            raise Exception('Provided input was not of type NetworkAttributesElement.')

    def addNodeAttribute(self, node_attribute, i=None):
        if type(node_attribute) is NodeAttributesElement:
            nodeAttrs = self.nodeAttributes.get(node_attribute.getPropertyOf())
            if nodeAttrs is None:
                nodeAttrs = []
                self.nodeAttributes[node_attribute.getPropertyOf()] = nodeAttrs

            nodeAttrs.append(node_attribute)
        else:
            raise Exception('Provided input was not of type NodeAttributesElement.')

    def addEdgeAttribute(self, edge_attribute, i=None):
        if type(edge_attribute) is EdgeAttributesElement:
            edgeAttrs = self.edgeAttributes.get(edge_attribute.getPropertyOf())
            if edgeAttrs is None:
                    edgeAttrs = []
                    self.edgeAttributes[edge_attribute.getPropertyOf()] = edgeAttrs

            edgeAttrs.append(edge_attribute)
        else:
            raise Exception('Provided input was not of type EdgeAttributesElement.')

    def addSupport(self, support_element):
        if type(support_element) is SupportElement:
            self.supports[support_element.getId()] = support_element
        else:
            raise Exception('Provided input was not of type SupportElement.')

    def addCitation(self, citation_element):
        if type(citation_element) is CitationElement:
            self.citations[citation_element.getId()] = citation_element
        else:
            raise Exception('Provided input was not of type CitationElement.')

    def addNodeCitationsFromCX(self, node_citation_cx):
        self.buildManyToManyRelation('nodeCitations', node_citation_cx, 'citations')

    def addNodeCitations(self, node_id, citation_id):
        node_citation_element = {CX_CONSTANTS.PROPERTY_OF: [node_id], CX_CONSTANTS.CITATIONS: [citation_id]}
        self.buildManyToManyRelation('nodeCitations', node_citation_element, 'citations')

    def addEdgeCitationsFromCX(self, edge_citation_cx):
        self.buildManyToManyRelation('edgeCitations', edge_citation_cx, 'citations')

    def addEdgeCitations(self, edge_id, citation_id):
        edge_citation_element = {CX_CONSTANTS.PROPERTY_OF: [edge_id], CX_CONSTANTS.CITATIONS: [citation_id]}
        self.buildManyToManyRelation('edgeCitations', edge_citation_element, 'citations')

    def addEdgeSupports(self, edge_supports_element):
        self.buildManyToManyRelation('edgeSupports', edge_supports_element, 'supports')

    def buildManyToManyRelation(self, aspect_name, element, relation_name):
        if aspect_name == 'nodeCitations':
            aspect = self.nodeCitations
        elif aspect_name == 'edgeCitations':
            aspect = self.edgeCitations
        elif aspect_name == 'edgeSupports':
            aspect = self.edgeSupports
        else:
            raise Exception('Only nodeCitations, edgeCitations and edgeSupports are supported. ' + aspect_name + ' was supplied')

        for po in element.get(CX_CONSTANTS.PROPERTY_OF):
            po_id = aspect.get(po)
            if po_id is None:
                aspect[po] = element.get(relation_name)
            else:
                aspect[po] += element.get(relation_name)

    def addOpapqueAspect(self, opaque_element):
        if type(opaque_element) is AspectElement:
            aspectElmts = self.opaqueAspects.get(opaque_element.getAspectName())
            if aspectElmts is None:
                aspectElmts = []
                self.opaqueAspects[opaque_element.getAspectName()] = aspectElmts

            aspectElmts.append(opaque_element.getAspectElement())
        else:
            raise Exception('Provided input was not of type AspectElement.')

    def addNodeAssociatedAspectElement(self, nodeId, elmt):
        self.addAssciatatedAspectElement(self.nodeAssociatedAspects, nodeId, elmt)

    def addEdgeAssociatedAspectElement(self, edgeId, elmt):
        self.addAssciatatedAspectElement(self.edgeAssociatedAspects, edgeId, elmt)


#    self.edgeAssociatedAspects = {
#        "cartesianLayout":
#            {
#                '1':
#                  {
#                    "node": 1,
#                    "x": 415.535802925717,
#                    "y": 257.93015713560766
#                  }
#            }
#    }

    def addAssciatatedAspectElement(self, table, id, elmt):
        aspectElements = table.get(elmt.getAspectName())
        if aspectElements is None:
            aspectElements = {}
            table.put(elmt.getAspectName(), aspectElements)

        elmts = aspectElements.get(id)

        if (elmts is None):
            elmts = []
            aspectElements.put(id, elmts)

        elmts.append(elmt)

    def getMetadata(self):
        return self.metadata

    def setMetadata(self, metadata_obj):
        if type(metadata_obj) is dict:
            self.metadata = metadata_obj
        else:
            raise Exception('Set metadata input was not of type <dict>')

    def addMetadata(self, md):
        if type(md) is MetaDataElement:
            #  TODO - alter metadata to match the element counts
            self.metadata[md.getName()] = md
        else:
            raise Exception('Provided input was not of type <MetaDataElement>')

    def addNameSpace(self, prefix, uri):
        self.namespaces[prefix] = uri

    def setNamespaces(self,ns ):
        self.namespaces = ns

    def getNamespaces(self,):
        return self.namespaces

    def getEdges (self):
        return self.edges

    def getNodes(self):
        return self.nodes

    def getOpaqueAspectTable(self):
        return self.opaqueAspects

    def getNetworkAttributes(self):
        return self.networkAttributes

    def getNodeAttributes(self):
        return self.nodeAttributes

    def getEdgeAttributes(self):
        return self.edgeAttributes

    def getNodeAssociatedAspects(self):
        return self.nodeAssociatedAspects

    def getEdgeAssociatedAspects(self):
        return self.edgeAssociatedAspects

    def getNodeAssociatedAspect(self, aspectName):
        return self.nodeAssociatedAspects.get(aspectName)

    def getEdgeAssociatedAspect(self, aspectName):
        return self.edgeAssociatedAspects.get(aspectName)

    def getProvenance(self):
        return self.provenance

    def getMissingNodes(self):
        return self.missingNodes

    def setProvenance(self, provenance):
        self.provenance = provenance

    def getEdgeCitations(self):
        return self.edgeCitations

    def getNodeCitations(self):
        return self.nodeCitations

    def to_pandas(self):

        #===================================================
        # there are only a few possible keys in attributes.
        #===================================================
        my_list = ['po','n','d','v','s']

        rows = [dict(it.to_json(), source=v.getSource(), target=v.getTarget())
                            for k, v in self.edges.iteritems() if self.edgeAttributes.get(k) is not None
                            for it in self.edgeAttributes.get(k)]

        df_columns = ['source', 'target'] + my_list

        return_df = pd.DataFrame(rows, columns=df_columns)

        #output = StringIO()
        #return_df.to_csv(output)
        #output.seek(0)
        #print output.read()
        return return_df

    def to_networkx(self):
        G = nx.Graph()
        '''
        node_id = 0
        node_dict = {}
        G.max_edge_id = 0
        for node_name, node_attr in G_nx.nodes_iter(data=True):
            if discard_null:
                node_attr = {k:v for k,v in node_attr.items() if not pd.isnull(v)}

            if node_attr.has_key('name'):
                G.add_node(node_id, node_attr)
            else:
                G.add_node(node_id, node_attr, name=node_name)
            node_dict[node_name] = node_id
            node_id += 1
        for s, t, edge_attr in G_nx.edges_iter(data=True):
            if discard_null:
                edge_attr = {k:v for k,v in edge_attr.items() if not pd.isnull(v)}
            G.add_edge(node_dict[s], node_dict[t], G.max_edge_id, edge_attr)
            G.max_edge_id += 1

        if hasattr(G_nx, 'pos'):
            G.pos = {node_dict[a] : b for a, b in G_nx.pos.items()}
            # G.subnetwork_id = 1
            # G.view_id = 1
        '''

        return G

    def __str__(self):
        return json.dumps(self.to_json())

    def to_json(self):
        output_cx = []

        if self.metadata:
            output_cx.append(self.generateAspect('metaData'))
        if self.nodes:
            output_cx.append(self.generateAspect('nodes'))
        if self.edges:
            output_cx.append(self.generateAspect('edges'))
        if self.networkAttributes:
            output_cx.append(self.generateAspect('networkAttributes'))
        if self.nodeAttributes:
            output_cx.append(self.generateAspect('nodeAttributes'))
        if self.edgeAttributes:
            output_cx.append(self.generateAspect('edgeAttributes'))
        if self.citations:
            output_cx.append(self.generateAspect('citations'))
        if self.nodeCitations:
            output_cx.append(self.generateAspect('nodeCitations'))
        if self.edgeCitations:
            output_cx.append(self.generateAspect('edgeCitations'))
        if self.edgeSupports:
            output_cx.append(self.generateAspect('edgeSupports'))
        if self.nodeSupports:
            output_cx.append(self.generateAspect('nodeSupports'))
        if self.metadata:
            output_cx.append(self.generateAspect('metaData'))

        return output_cx

    def generateAspect(self, aspect_name):
        core_aspect = ['nodes', 'edges','networkAttributes', 'nodeAttributes', 'edgeAttributes', 'citations', 'metaData']
        aspect_element_array = []
        element_count = 0
        element_id_max = 0

        use_this_aspect = None
        #=============================
        # PROCESS CORE ASPECTS FIRST
        #=============================
        if aspect_name in core_aspect:
            use_this_aspect = self.string_to_aspect_object(aspect_name)

        if use_this_aspect is not None:
            if type(use_this_aspect) is list:
                for item in use_this_aspect:
                    add_this_element = item.to_json()
                    id = add_this_element.get(CX_CONSTANTS.ID)
                    if id > element_id_max:
                        element_id_max = id
                    aspect_element_array.append(add_this_element)
                    element_count +=1
            else:
                for k, v in use_this_aspect.iteritems():
                    if type(v) is list:
                        for v_item in v:
                            add_this_element = v_item.to_json()
                            id = add_this_element.get(CX_CONSTANTS.ID)
                            if id > element_id_max:
                                element_id_max = id
                            aspect_element_array.append(add_this_element)
                            element_count +=1
                    else:
                        add_this_element = v.to_json()
                        id = add_this_element.get(CX_CONSTANTS.ID)
                        if id > element_id_max:
                            element_id_max = id
                        aspect_element_array.append(add_this_element)
                        element_count +=1
        else:
            #===========================
            # PROCESS NON-CORE ASPECTS
            #===========================
            use_this_aspect = self.string_to_aspect_object(aspect_name)

            if use_this_aspect is not None:
                if type(use_this_aspect) is dict:
                    for k, v in use_this_aspect.iteritems():
                        if type(v) is list:
                            aspect_element_array.append({CX_CONSTANTS.PROPERTY_OF: [k], CX_CONSTANTS.CITATIONS: v})
                        else:
                            aspect_element_array.append({CX_CONSTANTS.PROPERTY_OF: [k], CX_CONSTANTS.CITATIONS: [v]})
                        element_count +=1
                else:
                    raise Exception('Citation was not in json format')
            else:
                return None

        aspect = {aspect_name: aspect_element_array}
        #============================================
        # UPDATE METADATA ELEMENT COUNTS/ID COUNTER
        #============================================
        md = self.metadata.get(aspect_name)
        if md is not None:
            md.setElementCount(element_count)
            md.setIdCounter(element_id_max)
            md.incrementConsistencyGroup()
        else:
            mde = MetaDataElement(elementCount=element_count, properties=[], version='1.0', consistencyGroup=0, name=aspect_name)

            if element_id_max != 0:
                mde.setIdCounter(element_id_max)

            self.addMetadata(mde)

        print '%s ELEMENT COUNT: %s, MAX ID: %s' % (aspect_name, str(element_count), str(element_id_max))
        return aspect

    def handleMetadataUpdate(self, aspect_name):
        aspect = self.string_to_aspect_object(aspect_name)


        return_metadata = {
            CX_CONSTANTS.CONSISTENCY_GROUP: consistency_group,
            CX_CONSTANTS.ELEMENT_COUNT: 1,
            CX_CONSTANTS.METADATA_NAME: "@context",
            CX_CONSTANTS.PROPERTIES: [],
            CX_CONSTANTS.VERSION: "1.0"
        }


    def generate_metadata(self, G, unclassified_cx):
        #if self.metadata:
        #    for k, v in self.metadata.iteritems():


        return_metadata = []
        consistency_group = 1
        if(self.metadata_original is not None):
            for mi in self.metadata_original:
                if(mi.get("consistencyGroup") is not None):
                    if(mi.get("consistencyGroup") > consistency_group):
                        consistency_group = mi.get("consistencyGroup")

            consistency_group += 1 # bump the consistency group up by one

            print("consistency group max: " + str(consistency_group))

        # ========================
        # @context metadata
        # ========================
        if  self.namespaces:
            return_metadata.append(
                {
                    "consistencyGroup": consistency_group,
                    "elementCount": 1,
                    "name": "@context",
                    "properties": [],
                    "version": "1.0"
                }
            )

        #========================
        # Nodes metadata
        #========================
        node_ids = [n[0] for n in G.nodes_iter(data=True)]
        if(len(node_ids) < 1):
            node_ids = [0]
        return_metadata.append(
            {
                "consistencyGroup" : consistency_group,
                "elementCount" : len(node_ids),
                "idCounter": max(node_ids),
                "name" : "nodes",
                "properties" : [ ],
                "version" : "1.0"
            }
        )

        #========================
        # Edges metadata
        #========================
        edge_ids = [e[2]for e in G.edges_iter(data=True, keys=True)]
        if(len(edge_ids) < 1):
            edge_ids = [0]
        return_metadata.append(
            {
                "consistencyGroup" : consistency_group,
                "elementCount" : len(edge_ids),
                "idCounter": max(edge_ids),
                "name" : "edges",
                "properties" : [ ],
                "version" : "1.0"
            }
        )

        #=============================
        # Network Attributes metadata
        #=============================
        if(len(G.graph) > 0):
            return_metadata.append(
                {
                    "consistencyGroup" : consistency_group,
                    "elementCount" : len(G.graph),
                    "name" : "networkAttributes",
                    "properties" : [ ],
                    "version" : "1.0"
                }
            )

        #===========================
        # Node Attributes metadata
        #===========================
        #id_max = 0
        attr_count = 0
        for node_id , attributes in G.nodes_iter(data=True):
            for attribute_name in attributes:
                if attribute_name != "name" and attribute_name != "represents":
                    attr_count += 1



        #
        # for n, nattr in G.nodes(data=True):
        #     if(bool(nattr)):
        #         attr_count += len(nattr.keys())
        #
        #     if(n > id_max):
        #         id_max = n

        if(attr_count > 0):
            return_metadata.append(
                {
                    "consistencyGroup" : consistency_group,
                    "elementCount" : attr_count,
                    #"idCounter": id_max,
                    "name" : "nodeAttributes",
                    "properties" : [ ],
                    "version" : "1.0"
                }
            )

        #===========================
        # Edge Attributes metadata
        #===========================
        #id_max = 0
        attr_count = 0
        for s, t, id, a in G.edges(data=True, keys=True):
            if(bool(a)):
                for attribute_name in a:
                    if attribute_name != "interaction":
                        attr_count += 1
                #attr_count += len(a.keys())

            # if(id > id_max):
            #     id_max = id

        if(attr_count > 0):
            return_metadata.append(
                {
                    "consistencyGroup" : consistency_group,
                    "elementCount" : attr_count,
                    #"idCounter": id_max,
                    "name" : "edgeAttributes",
                    "properties" : [ ],
                    "version" : "1.0"
                }
            )

        #===========================
        # cyViews metadata
        #===========================
        if self.view_id != None:
            return_metadata.append(
                {
                    "elementCount": 1,
                    "name": "cyViews",
                    "properties": [],
                    "consistencyGroup" : consistency_group
                }
            )

        #===========================
        # subNetworks metadata
        #===========================
        if self.subnetwork_id != None:
            return_metadata.append(
                {
                    "elementCount": 1,
                    "name": "subNetworks",
                    "properties": [],
                    "consistencyGroup" : consistency_group
                }
            )

        #===========================
        # networkRelations metadata
        #===========================
        if self.subnetwork_id != None and self.view_id != None:
            return_metadata.append(
                {
                    "elementCount": 2,
                    "name": "networkRelations",
                    "properties": [],
                    "consistencyGroup" : consistency_group
                }
            )

        #===========================
        # citations and supports metadata
        #===========================
        if len(self.support_map) > 0:
            return_metadata.append(
                {
                    "elementCount": len(self.support_map),
                    "name": "supports",
                    "properties": [],
                    "idCounter": max(self.support_map.keys()),
                    "consistencyGroup" : consistency_group
                }
            )

        if len(self.node_support_map) > 0:
            return_metadata.append(
                {
                    "elementCount": len(self.node_support_map),
                    "name": "nodeSupports",
                    "properties": [],
                    "consistencyGroup" : consistency_group
                }
            )
        if len(self.edge_support_map) > 0:
            return_metadata.append(
                {
                    "elementCount": len(self.edge_support_map),
                    "name": "edgeSupports",
                    "properties": [],
                    "consistencyGroup" : consistency_group
                }
            )

        if len(self.citation_map) > 0:
            return_metadata.append(
                {
                    "elementCount": len(self.citation_map),
                    "name": "citations",
                    "properties": [],
                    "idCounter": max(self.citation_map.keys()),
                    "consistencyGroup" : consistency_group
                }
            )

        if len(self.node_citation_map) > 0:
            return_metadata.append(
                {
                    "elementCount": len(self.node_citation_map),
                    "name": "nodeCitations",
                    "properties": [],
                    "consistencyGroup" : consistency_group
                }
            )

        if len(self.edge_citation_map) > 0:
            return_metadata.append(
                {
                    "elementCount": len(self.edge_citation_map),
                    "name": "edgeCitations",
                    "properties": [],
                    "consistencyGroup" : consistency_group
                }
            )

        if len(self.function_term_map) > 0:
            return_metadata.append(
                {
                    "elementCount": len(self.function_term_map),
                    "name": "functionTerms",
                    "properties": [],
                    "consistencyGroup" : consistency_group
                }
            )

        if len(self.reified_edges) > 0:
            return_metadata.append(
                {
                    "elementCount": len(self.reified_edges),
                    "name": "reifiedEdges",
                    "properties": [],
                    "consistencyGroup" : consistency_group
                }
            )

        #===========================
        # ndexStatus metadata
        #===========================
        return_metadata.append(
            {
                "consistencyGroup": consistency_group,
                "elementCount": 1,
                "name": "ndexStatus",
                "properties": [],
                "version": "1.0"
            }
        )

        #===========================
        # cartesianLayout metadata
        #===========================
        if self.pos and len(self.pos) > 0:
            return_metadata.append(
                {
                    "consistencyGroup": consistency_group,
                    "elementCount": len(self.pos),
                    "name": "cartesianLayout",
                    "properties": [],
                    "version": "1.0"
                }
            )

        #===========================
        # OTHER metadata
        #===========================
        for asp in self.unclassified_cx:
            try:
                aspect_type = asp.iterkeys().next()
                if(aspect_type == "visualProperties"
                   or aspect_type == "cyVisualProperties"
                   or aspect_type == "@context"):
                    return_metadata.append(
                        {
                            "consistencyGroup" : consistency_group,
                            "elementCount":len(asp[aspect_type]),
                            "name":aspect_type,
                            "properties":[]
                         }
                    )
            except Exception as e:
                print(e.message)


        #print {'metaData': return_metadata}

        return [{'metaData': return_metadata}]

    def string_to_aspect_object(self, aspect_name):
        if aspect_name == 'metaData':
            return self.metadata
        elif aspect_name == 'nodes':
            return self.nodes
        elif aspect_name == 'edges':
            return self.edges
        elif aspect_name == 'networkAttributes':
            return self.networkAttributes
        elif aspect_name == 'nodeAttributes':
            return self.nodeAttributes
        elif aspect_name == 'edgeAttributes':
            return self.edgeAttributes
        elif aspect_name == 'citations':
            return self.citations
        elif aspect_name == 'nodeCitations':
            return self.nodeCitations
        elif aspect_name == 'edgeCitations':
            return self.edgeCitations
        elif aspect_name == 'edgeSupports':
            return self.edgeSupports

