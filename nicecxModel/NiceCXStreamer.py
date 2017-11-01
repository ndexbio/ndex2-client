__author__ = 'aarongary'

import codecs
import mimetypes
import sys
import uuid
import requests
import json
from requests_toolbelt import MultipartEncoder
try:
    import io
except ImportError:
    pass # io is requiered in python3 but not available in python2

class MultipartCXEncoder2(MultipartEncoder):
    def __init__(self, fields, nice_cx):
        #self.boundary = uuid.uuid4().hex
        #self.content_type = 'multipart/form-data; boundary={}'.format(self.boundary)
        super(MultipartCXEncoder2, self).__init__(fields=fields)
        self.nice_cx = nice_cx

    def read(self, size=-1):
        """Read data from the streaming encoder.

        :param int size: (optional), If provided, ``read`` will return exactly
            that many bytes. If it is not provided, it will return the
            remaining bytes.
        :returns: bytes
        """
        if self.finished:
            return self._buffer.read(size)

        bytes_to_load = size
        if bytes_to_load != -1 and bytes_to_load is not None:
            bytes_to_load = self._calculate_load_amount(int(size))

        self._load(bytes_to_load)
        return self._buffer.read(size)

class MultipartCXEncoder(object):
    def __init__(self, nice_cx):
        self.boundary = uuid.uuid4().hex
        self.content_type = 'multipart/form-data; boundary={}'.format(self.boundary)
        self.nice_cx = nice_cx

    @classmethod
    def u(cls, s):
        if sys.hexversion < 0x03000000 and isinstance(s, str):
            s = s.decode('utf-8')
        if sys.hexversion >= 0x03000000 and isinstance(s, bytes):
            s = s.decode('utf-8')
        return s

    def iter(self, fields, files):
        """
        fields is a sequence of (name, value) elements for regular form fields.
        files is a sequence of (name, filename, file-type) elements for data to be uploaded as files
        Yield body's chunk as bytes
        """

        encoder = codecs.getencoder('utf-8')
        yield encoder('--{}\r\n'.format(self.boundary))
        yield encoder(self.u('Content-Disposition: form-data; name="{}"\r\n').format('CXNetworkStream'))
        yield encoder('\r\n')
        #if isinstance(value, int) or isinstance(value, float):
        #    value = str(value)
        #yield encoder(self.u(value))

        if self.nice_cx.node_int_id_generator:
            self.nice_cx.node_id_lookup = list(self.nice_cx.node_int_id_generator)

        if self.nice_cx.metadata:
            yield encoder(self.u(json.dumps(self.nice_cx.generate_metadata_aspect())))
        '''
        if self.nice_cx.nodes:
            yield encoder(self.u(json.dumps(self.nice_cx.generate_aspect('nodes'))))
        if self.nice_cx.edges:
            yield encoder(self.u(json.dumps(self.nice_cx.generate_aspect('edges'))))
        if self.nice_cx.networkAttributes:
            yield encoder(self.u(json.dumps(self.nice_cx.generate_aspect('networkAttributes'))))
        if self.nice_cx.nodeAttributes:
            yield encoder(self.u(json.dumps(self.nice_cx.generate_aspect('nodeAttributes'))))
        if self.nice_cx.edgeAttributes:
            yield encoder(self.u(json.dumps(self.nice_cx.generate_aspect('edgeAttributes'))))
        if self.nice_cx.citations:
            yield encoder(self.u(json.dumps(self.nice_cx.generate_aspect('citations'))))
        if self.nice_cx.nodeCitations:
            yield encoder(self.u(json.dumps(self.nice_cx.generate_aspect('nodeCitations'))))
        if self.nice_cx.edgeCitations:
            yield encoder(self.u(json.dumps(self.nice_cx.generate_aspect('edgeCitations'))))
        if self.nice_cx.edgeSupports:
            yield encoder(self.u(json.dumps(self.nice_cx.generate_aspect('edgeSupports'))))
        if self.nice_cx.nodeSupports:
            yield encoder(self.u(json.dumps(self.nice_cx.generate_aspect('nodeSupports'))))
        if self.nice_cx.opaqueAspects:
            for oa in self.nice_cx.opaqueAspects:
                yield encoder(self.u(json.dumps({oa: self.nice_cx.opaqueAspects[oa]})))
        if self.nice_cx.metadata:
            #===========================
            # UPDATE CONSISTENCY GROUP
            #===========================
            yield encoder(self.u(json.dumps(self.nice_cx.generate_metadata_aspect())))
        '''

        yield encoder('\r\n')
        '''
        for (key, filename, fd) in files:
            key = self.u(key)
            filename = self.u(filename)
            yield encoder('--{}\r\n'.format(self.boundary))
            yield encoder(self.u('Content-Disposition: form-data; name="{}"; filename="{}"\r\n').format(key, filename))
            yield encoder('Content-Type: {}\r\n'.format('application/octet-stream'))#'application/json'))
            yield encoder('\r\n')
            with fd:
                buff = fd.read()
                yield (buff, len(buff))
            yield encoder('\r\n')
        '''
        yield encoder('--{}--\r\n'.format(self.boundary))

    def read(self, size=-1):
        """Read data from the streaming encoder.

        :param int size: (optional), If provided, ``read`` will return exactly
            that many bytes. If it is not provided, it will return the
            remaining bytes.
        :returns: bytes
        """
        if self.finished:
            return self._buffer.read(size)

        bytes_to_load = size
        if bytes_to_load != -1 and bytes_to_load is not None:
            bytes_to_load = self._calculate_load_amount(int(size))

        self._load(bytes_to_load)
        return self._buffer.read(size)

    def encode(self, fields, files):
        body = io.BytesIO()
        for chunk, chunk_len in self.iter(fields, files):
            body.write(chunk)
        return self.content_type, body.getvalue()

def postNiceCxStream(niceCx):
    url = 'http://dev2.ndexbio.org/v2/network'

    stream = io.BytesIO(json.dumps({'placeholder':''}))
    fields = {
        'CXNetworkStream': ('filename', stream, 'application/octet-stream')
    }

    multipart_data = MultipartCXEncoder2(fields, niceCx)

    headers = {
        'Content-Type': multipart_data.content_type,
        'User-Agent': 'NDEx-Python/3.0'
    }
    response = requests.post(url, data=multipart_data, headers=headers, auth=('scratch', 'scratch')) # .encode(None, None)

