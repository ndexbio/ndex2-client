# -*- coding: utf-8 -*-

"""Tests for :py:func:`ndex2.create_nice_cx_from_raw_cx`"""

import os
import unittest
import json
import networkx
import ndex2


SKIP_REASON = 'NDEX2_TEST_USER environment variable detected, ' \
              'skipping for integration tests'


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestCreateNiceCXNetworkFromRawCX(unittest.TestCase):

    TEST_DIR = os.path.dirname(__file__)
    WNT_SIGNAL_FILE = os.path.join(TEST_DIR, 'data', 'wntsignaling.cx')
    DARKTHEME_FILE = os.path.join(TEST_DIR, 'data', 'darkthemefinal.cx')
    DARKTHEMENODE_FILE = os.path.join(TEST_DIR, 'data',
                                      'darkthemefinalwithnodevis.cx')
    GLYPICAN_FILE = os.path.join(TEST_DIR, 'data', 'glypican2.cx')

    def setUp(self):
        """Set up test fixtures, if any."""
        pass

    def tearDown(self):
        """Tear down test fixtures, if any."""
        pass

    def test_create_nice_cx_from_raw_cx_with_none(self):
        try:
            ndex2.create_nice_cx_from_raw_cx(None)
            self.fail('Expected Exception')
        except Exception as e:
            self.assertEqual('CX is empty', str(e))

    def test_create_nice_cx_from_raw_cx_with_emptystr(self):
        try:
            ndex2.create_nice_cx_from_raw_cx('')
            self.fail('Expected Exception')
        except Exception as e:
            self.assertEqual('CX is empty', str(e))

    def test_create_nice_cx_from_raw_cx_with_invalidstr(self):

        net_cx = ndex2.create_nice_cx_from_raw_cx('invalid')
        self.assertEqual(None, net_cx.get_name())
        self.assertEqual(0, len(list(net_cx.get_nodes())))
        self.assertEqual(0, len(list(net_cx.get_edges())))

    def test_create_nice_cx_from_raw_cx_with_wnt_signaling(self):

        with open(TestCreateNiceCXNetworkFromRawCX.
                          WNT_SIGNAL_FILE, 'r') as f:
            net_cx = ndex2.create_nice_cx_from_raw_cx(json.load(f))

        self.assertEqual('WNT Signaling', net_cx.get_name())
        self.assertEqual(32, len(list(net_cx.get_nodes())))
        self.assertEqual(74, len(list(net_cx.get_edges())))

        # test for issue #60 make sure node/edge counters are
        # properly set
        self.assertEqual(32, net_cx.node_int_id_generator)
        self.assertEqual(74, net_cx.edge_int_id_generator)

    def test_create_nice_cx_from_raw_cx_with_glypican(self):

        with open(TestCreateNiceCXNetworkFromRawCX.
                          GLYPICAN_FILE, 'r') as f:
            net_cx = ndex2.create_nice_cx_from_raw_cx(json.load(f))

        self.assertEqual('Glypican 2 network', net_cx.get_name())
        self.assertEqual(2, len(list(net_cx.get_nodes())))
        self.assertEqual(1, len(list(net_cx.get_edges())))

        # test for issue #60 make sure node/edge counters are
        # properly set
        self.assertEqual(2, net_cx.node_int_id_generator)
        self.assertEqual(1, net_cx.edge_int_id_generator)






