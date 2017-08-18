__author__ = 'aarongary'
from model.metadata.MetaDataCollection import MetaDataCollection
from model.metadata.MetaDataCollection import MetaDataElement
from aspects.NameSpaces import NameSpaces
from model.cx.aspects.NodesElement import NodesElement
from model.cx.aspects.EdgesElement import EdgesElement
from model.cx.aspects.NodeAttributesElement import NodeAttributesElement
from model.cx.aspects.EdgeAttributesElement import EdgeAttributesElement
from aspects.NetworkAttributesElement import NetworkAttributesElement
from aspects.SupportElement import SupportElement
from aspects.CitationElement import CitationElement
from aspects.AspectElement import AspectElement

class NiceCXNetwork():
    def __init__(self):
        self.metadata = MetaDataCollection()
        self.namespaces = NameSpaces()
        self.nodes = {}
        self.edges = {}
        self.citations = {}
        self.supports = {}
        self.nodeAttributes = {}
        self.edgeAttributes = {}
        self.networkAttributes = []
        self.nodeAssociatedAspects = {}
        self.edgeAssociatedAspects = {}
        self.opaqueAspects = {}
        self.provenance = None

    def addNode(self, node):
        if type(node) is NodesElement:
    		self.nodes[node.getId()] = node
        else:
            raise Exception('Provided input was not of type NodesElement.')

    def addEdge(self, edge):
        if type(edge) is EdgesElement:
    		self.nodes[edge.getId()] = edge
        else:
            raise Exception('Provided input was not of type EdgesElement.')

    def addNetworkAttribute(self, networkAttribute):
        if type(networkAttribute) is NetworkAttributesElement:
            self.networkAttributes.append(networkAttribute)
        else:
            raise Exception('Provided input was not of type NetworkAttributesElement.')

    def addNodeAttribute(self, nodeAttribute, i=None):
        if type(nodeAttribute) is NodeAttributesElement:
            nodeAttrs = self.nodeAttributes.get(i)
            if nodeAttrs is None:
                    nodeAttrs = []
                    self.nodeAttributes[i] = nodeAttrs

            nodeAttrs.append(nodeAttribute)
        else:
            raise Exception('Provided input was not of type NodeAttributesElement.')

    def addEdgeAttribute(self, edgeAttribute, i=None):
        if type(edgeAttribute) is EdgeAttributesElement:
            edgeAttrs = self.edgeAttributes.get(i)
            if edgeAttrs is None:
                    edgeAttrs = []
                    self.edgeAttributes[i] = edgeAttrs

            edgeAttrs.append(edgeAttribute)
        else:
            raise Exception('Provided input was not of type EdgeAttributesElement.')

    def addSupport(self, e):
        if type(e) is SupportElement:
    		self.supports[e.getId()] = e
        else:
            raise Exception('Provided input was not of type SupportElement.')

    def addCitation(self, e):
        if type(e) is CitationElement:
    		self.citations[e.getId()] = e
        else:
            raise Exception('Provided input was not of type CitationElement.')

    def addOpapqueAspect(self, e):
        if type(e) is AspectElement:
            aspectElmts = self.opaqueAspects.get(e.getAspectName())
            if aspectElmts is None:
                aspectElmts = []
                self.opaqueAspects[e.getAspectName()] = aspectElmts

            aspectElmts.append(e)
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







'''
		Collection<AspectElement> aspectElmts = opaqueAspects.get(e.getAspectName());
		if ( aspectElmts == null) {
			aspectElmts = new LinkedList<> ();
			opaqueAspects.put(e.getAspectName(), aspectElmts);
		}
		aspectElmts.add(e);
'''
'''
	private MetaDataCollection metadata;

	private NamespacesElement namespaces;
	private Map<Long, NodesElement> nodes;
	private Map<Long, EdgesElement> edges;
	private Map<Long, CitationElement> citations;
	private Map<Long, SupportElement> supports;

	private Map<Long, Collection<NodeAttributesElement>> nodeAttributes;
	private Map<Long, Collection<EdgeAttributesElement>> edgeAttributes;

	private Collection <NetworkAttributesElement> networkAttributes;

	//function term, node/edge citation and supports might use these 2 tables.
	private Map<String,Map<Long,Collection<AspectElement>>> nodeAssociatedAspects;
	private Map<String,Map<Long, Collection<AspectElement>>> edgeAssociatedAspects;

	private Map<String, Collection<AspectElement>> opaqueAspects;

	private Provenance provenance;

	public NiceCXNetwork() {
		setMetadata(new MetaDataCollection());
		namespaces = new NamespacesElement();
		nodes = new HashMap<>();
		edges = new HashMap<>();
		citations = new HashMap<>();
		supports = new HashMap<>();

		nodeAttributes = new HashMap<> ();
		edgeAttributes = new HashMap<> ();

		networkAttributes = new ArrayList<> ();

		nodeAssociatedAspects = new HashMap<>();
		edgeAssociatedAspects = new HashMap<>();

		opaqueAspects = new HashMap<>();

	}

	public void addNode(NodesElement node) {
		nodes.put(node.getId(), node);
	}

	public void addEdge(EdgesElement edge) {
		edges.put(edge.getId(), edge);
	}

	public void addNetworkAttribute ( NetworkAttributesElement networkAttribute) {
		networkAttributes.add(networkAttribute);
	}

	public void addNodeAttribute( NodeAttributesElement nodeAttribute) {
			addNodeAttribute(nodeAttribute.getPropertyOf(),nodeAttribute);
	}

	public void addNodeAttribute( Long i, NodeAttributesElement nodeAttribute) {

		Collection<NodeAttributesElement> nodeAttrs = nodeAttributes.get(i);
		if ( nodeAttrs == null) {
				nodeAttrs = new LinkedList<>();
				nodeAttributes.put(i,nodeAttrs);
		}
		nodeAttrs.add(nodeAttribute);
	}

	public void addEdgeAttribute(EdgeAttributesElement edgeAttribute) {
			addEdgeAttribute(edgeAttribute.getPropertyOf(),edgeAttribute);

	}


	public void addEdgeAttribute(Long i , EdgeAttributesElement edgeAttribute) {
			Collection<EdgeAttributesElement> edgeAttrs = edgeAttributes.get(i);
			if ( edgeAttrs == null) {
				edgeAttrs = new LinkedList<>();
				edgeAttributes.put(i, edgeAttrs);
			}
			edgeAttrs.add(edgeAttribute);
	}

	public void addSupport(SupportElement e) {
		supports.put(e.getId(), e);
	}

	public void addCitation(CitationElement e) {
		citations.put(e.getId(),e);
	}

	public void addOpapqueAspect(AspectElement e) {
		Collection<AspectElement> aspectElmts = opaqueAspects.get(e.getAspectName());
		if ( aspectElmts == null) {
			aspectElmts = new LinkedList<> ();
			opaqueAspects.put(e.getAspectName(), aspectElmts);
		}
		aspectElmts.add(e);

	}

	public void addNodeAssociatedAspectElement(Long nodeId, AspectElement elmt) {
		addAssciatatedAspectElement(nodeAssociatedAspects, nodeId, elmt);
	}

	public void addEdgeAssociatedAspectElement(Long edgeId, AspectElement elmt) {
		addAssciatatedAspectElement(edgeAssociatedAspects, edgeId, elmt);
	}

	private static void addAssciatatedAspectElement(Map<String,Map<Long,Collection<AspectElement>>> table, Long id, AspectElement elmt) {
		Map<Long,Collection<AspectElement>> aspectElements = table.get(elmt.getAspectName());
		if ( aspectElements == null) {
			aspectElements = new TreeMap<> ();
			table.put(elmt.getAspectName(), aspectElements);
		}
		Collection<AspectElement> elmts = aspectElements.get(id);

		if (elmts == null) {
			elmts = new ArrayList<>();
			aspectElements.put(id, elmts);
		}
		elmts.add(elmt);
	}


	public MetaDataCollection getMetadata() {
		return metadata;
	}

	public void setMetadata(MetaDataCollection metadata) {
		this.metadata = metadata;
	}

	public void addNameSpace(String prefix, String uri) {
		namespaces.put(prefix, uri);
	}

	public void setNamespaces(NamespacesElement ns ) {
		this.namespaces = ns;
	}

	public NamespacesElement getNamespaces() {
		return this.namespaces;
	}

	public Map<Long, EdgesElement> getEdges () {
		return this.edges;
	}

	public Map<Long,NodesElement> getNodes() {
		return this.nodes;
	}

	public Map<String,Collection<AspectElement>> getOpaqueAspectTable() {
		return this.opaqueAspects;
	}

	public Collection <NetworkAttributesElement> getNetworkAttributes() {
		return this.networkAttributes;
	}

	public Map<Long, Collection<NodeAttributesElement>> getNodeAttributes() {
		return this.nodeAttributes;
	}

	public Map<Long, Collection<EdgeAttributesElement>> getEdgeAttributes() {
		return this.edgeAttributes;
	}

	public Map<String,Map<Long,Collection<AspectElement>>> getNodeAssociatedAspects() {
		return this.nodeAssociatedAspects;
	}

	public Map<String,Map<Long,Collection<AspectElement>>> getEdgeAssociatedAspects() {
		return this.edgeAssociatedAspects;
	}

	public Map<Long,Collection<AspectElement>> getNodeAssociatedAspect(String aspectName) {
		return this.nodeAssociatedAspects.get(aspectName);
	}

	public Map<Long,Collection<AspectElement>> getEdgeAssociatedAspect(String aspectName) {
		return this.edgeAssociatedAspects.get(aspectName);
	}

	public Provenance getProvenance() {
		return provenance;
	}

	public void setProvenance(Provenance provenance) {
		this.provenance = provenance;
	}
	'''
