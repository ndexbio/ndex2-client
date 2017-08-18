__author__ = 'aarongary'

from NdexAspectElement import NdexAspectElement
from . import CX_CONSTANTS

class SupportElement(NdexAspectElement):
    def __init__(self):
        self.ID = CX_CONSTANTS.get('ID')
        self.INTERACTION = 'i'
        self.SOURCE_NODE_ID = 's'
        self.TARGET_NODE_ID = 't'
        self.ASPECT_NAME = 'supports'
        self.text = None
        self.id = None
        self.citationId = 0
        self.props = []

        self.support_element = {}

'''
	public static final String ASPECT_NAME = "supports";

	private static final String tField = "text";


	@JsonProperty ( tField )
	private String text;

	@JsonProperty( "citation")
	private Long citationId;

	@JsonProperty( "@id")
	private long id;

	@JsonProperty( "attributes")
	private Collection<CXSimpleAttribute> props;

	public SupportElement() {
		props = new LinkedList<> ();
	}


	public String getText() {
		return text;
	}


	public void setText(String text) {
		this.text = text;
	}


	public Long getCitationId() {
		return citationId;
	}


	public void setCitationId(Long citationId) {
		this.citationId = citationId;
	}


	@Override
	@JsonIgnore
	public String getAspectName() {
		return ASPECT_NAME;
	}


	public long getId() {
		return id;
	}


	public void setId(long id) {
		this.id = id;
	}


	public Collection<CXSimpleAttribute> getProps() {
		return props;
	}


	public void setProps(Collection<CXSimpleAttribute> props) {
		this.props = props;
	}
'''
