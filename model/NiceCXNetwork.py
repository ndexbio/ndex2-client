__author__ = 'aarongary'
from model.metadata.MetaDataCollection import MetaDataCollection
from model.metadata.MetaDataCollection import MetaDataElement
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
    def __init__(self):
        self.metadata = MetaDataCollection()
        self.namespaces = NameSpaces()
        self.nodes = {}
        self.edges = {}
        self.citations = {}
        self.nodeCitations = {}
        self.edgeCitations = {}
        self.supports = {}
        self.nodeAttributes = {}
        self.edgeAttributes = {}
        self.networkAttributes = []
        self.nodeAssociatedAspects = {}
        self.edgeAssociatedAspects = {}
        self.opaqueAspects = {}
        self.provenance = None
        #self.niceCX = {}
        #self.niceCX['nodes'] = self.nodes
        #self.niceCX['edges'] = self.edges
        #self.niceCX['node'] = self.nodes
        #self.niceCX['edges'] = self.edges

    def handleCxElement(self, aspectName, element, niceCX):


    def addNode(self, node):
        if type(node) is NodesElement:
            self.nodes[node.getId()] = node
        else:
            raise Exception('Provided input was not of type NodesElement.')

    def addEdge(self, edge):
        if type(edge) is EdgesElement:
            self.edges[edge.getId()] = edge
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

    # aspect = {}
    # element = {
    #				"po": [
    #					2
    #				],
    #				"citations": [
    #					3
    #				]
    #			}

    def addNodeCitations(self, node_citation_element):
        self.buildManyToManyRelation('nodeCitations', node_citation_element, 'citations')

    def addEdgeCitations(self, edge_citation_element):
        self.buildManyToManyRelation('edgeCitations', edge_citation_element, 'citations')

    def buildManyToManyRelation(self, aspect_name, element, relation_name):
        if aspect_name == 'nodeCitations':
            aspect = self.nodeCitations
        elif aspect_name == 'edgeCitations':
            aspect = self.edgeCitations
        else:
            raise Exception('Only nodeCitations and edgeCitations are supported. ' + aspect_name + ' was supplied')

        for po in element.get(CX_CONSTANTS.PROPERTY_OF.value):
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

            aspectElmts.append(opaque_element)
        else:
            raise Exception('Provided input was not of type AspectElement.')

    def addNodeAssociatedAspectElement(self, nodeId, elmt):
        self.addAssciatatedAspectElement(self.nodeAssociatedAspects, nodeId, elmt)

    def addEdgeAssociatedAspectElement(self, edgeId, elmt):
        self.addAssciatatedAspectElement(self.edgeAssociatedAspects, edgeId, elmt)

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

    def setMetadata(self, metadata):
        self.metadata = metadata

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

    def setProvenance(self, provenance):
        self.provenance = provenance

    def __str__(self):
        return ''