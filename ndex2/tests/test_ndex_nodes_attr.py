__author__ = 'aarongary'


import os
import unittest
import ndex2
import time

from ndex2.nice_cx_network import NiceCXNetwork


upload_server = 'dev.ndexbio.org'
upload_username = 'scratch'
upload_password = 'scratch'

path_this = os.path.dirname(os.path.abspath(__file__))

class TestNodes(unittest.TestCase):
    #@unittest.skip("Temporary skipping")
    def test_add_int_attr(self):
        niceCx = NiceCXNetwork()
        int_node = niceCx.create_node(node_name="testint")
        niceCx.add_node_attribute(property_of=int_node, name='Size', values=1, type="integer")

        upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
        UUID = upload_message.split('/')[-1]
        time.sleep(1)
        imported_cx = ndex2.create_nice_cx_from_server(server='dev.ndexbio.org', uuid=UUID, username=upload_username, password=upload_password)
        for i in imported_cx.get_node_attributes(0):
            self.assertEqual(i.get('d'), "integer")


    #@unittest.skip("Temporary skipping")
    def test_add_flt(self):
        niceCx = NiceCXNetwork()
        float_node = niceCx.create_node(node_name="testflt")
        niceCx.add_node_attribute(property_of=float_node, name='Score', values=1.0, type="float")

        upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
        UUID = upload_message.split('/')[-1]
        time.sleep(1)
        imported_cx = ndex2.create_nice_cx_from_server(server='dev.ndexbio.org', uuid=UUID, username=upload_username,
                                                       password=upload_password)
        for i in imported_cx.get_node_attributes(0):
            self.assertEqual(i.get('d'), "double")

    #@unittest.skip("Temporary skipping")
    def test_add_lst_int(self):
        niceCx = NiceCXNetwork()
        list_int_node = niceCx.create_node(node_name="testlstint")
        niceCx.add_node_attribute(property_of=list_int_node, name='Too many sizes', values=[1,2,3,4,5], type="list_of_integer")

        upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
        UUID = upload_message.split('/')[-1]
        time.sleep(1)
        imported_cx = ndex2.create_nice_cx_from_server(server='dev.ndexbio.org', uuid=UUID, username=upload_username,
                                                       password=upload_password)
        for i in imported_cx.get_node_attributes(0):
            self.assertEqual(i.get('d'), "list_of_integer")

    #@unittest.skip("Temporary skipping")
    def test_add_lst_flt(self):
        niceCx = NiceCXNetwork()
        list_float_node = niceCx.create_node(node_name="testlstflt")

        niceCx.add_node_attribute(property_of=list_float_node, name='Too many scores', values=[15.3,43.6,-34.0,43.3], type="list_of_float")

        upload_message = niceCx.upload_to(upload_server, upload_username, upload_password)
        UUID = upload_message.split('/')[-1]
        time.sleep(1)
        imported_cx = ndex2.create_nice_cx_from_server(server='dev.ndexbio.org', uuid=UUID, username=upload_username,
                                                       password=upload_password)
        for i in imported_cx.get_node_attributes(0):
            self.assertEqual(i.get('d'), "list_of_double")