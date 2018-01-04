__author__ = 'aarongary'

from ndex2.cx import CX_CONSTANTS

class CXSimpleAttribute():
    def __init__(self, p=None):
        self.ID = CX_CONSTANTS.ID
        self.INTERACTION = 'i'
        self.name = None
        self.value = None
        self.dataType = None

        if p is not None:
            self.name = p.getPredicateString()
            self.value = p.getValue()
            self.dataType = p.getDataType()

    def getName(self):
        return self.name

    def setName(self,name):
        self.name = name

    def getValue(self):
        return self.value

    def setValue(self, value):
        self.value = value

    def getDataType(self):
        return self.dataType

    def setDataType(self, dataType):
        self.dataType = dataType


'''
    @JsonProperty("n")
    private String name;

    @JsonProperty("v")
    private String value;

    @JsonProperty("t")
    private String dataType;

    public CXSimpleAttribute() {
    }

    public CXSimpleAttribute(NdexPropertyValuePair p ) {
        name = p.getPredicateString();
        value = p.getValue();
        dataType = p.getDataType();
    }

    public String get_name() {
        return name;
    }

    public void set_name(String name) {
        this.name = name;
    }

    public String getValue() {
        return value;
    }

    public void setValue(String value) {
        this.value = value;
    }

    public String getDataType() {
        return dataType;
    }

    public void setDataType(String dataType) {
        this.dataType = dataType

'''
