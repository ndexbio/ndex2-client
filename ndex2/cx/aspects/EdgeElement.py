__author__ = 'aarongary'


class EdgeElement(object):
    def __init__(self, edge_id, edge_source, edge_target, edge_interaction=None):
        if edge_id is None:
            raise Exception("edge id can not be None.")

        if edge_source is None:
            raise Exception("edge source can not be None.")

        if edge_target is None:
            raise Exception("edge target can not be None.")

        self._id = edge_id
        self._source = edge_source
        self._target = edge_target
        self._interaction = edge_interaction

    @staticmethod
    def get_aspect_name():
        return 'edges'

    def get_id(self):
        return self._id

    def set_id(self, edge_id):
        self._id = edge_id

    def get_source(self):
        return self._source

    def set_source(self, source):
        self._source = source

    def get_target(self):
        return self._target

    def set_target(self, target):
        self._target = target

    def get_interaction(self):
        return self._interaction

    def set_interaction(self, interaction):
        self._interaction = interaction

    def __eq__(self, other):
        return self == other or self._id == other.get_id()

#    def __str__(self):
#        return json.dumps(self.to_cx(), cls=DecimalEncoder)

    def to_cx_str(self):
        return '{"@id":'+str(self._id) + ',"s":' + str(self._source) + ',"t":' + str(self._target) + \
               (',"i":' + self._interaction if self._interaction is not None else "") + "}"
