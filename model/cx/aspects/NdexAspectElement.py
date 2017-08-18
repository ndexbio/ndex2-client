__author__ = 'aarongary'

from AbstractAspectElement import AbstractAspectElement

class NdexAspectElement(AbstractAspectElement):
    def __init__(self):
        self.ID = ''
'''
	@Override
	public void write(JsonWriter out) throws IOException {
		out.writeObject(this);
		out.flush();
	}
'''