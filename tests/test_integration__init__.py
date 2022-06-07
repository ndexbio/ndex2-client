# -*- coding: utf-8 -*-

"""Integration/acceptance tests for `ndex2.nice_cx_network` package."""

import os
import re
import sys
import io
import time
import unittest
import json
import uuid
from datetime import datetime

from requests.exceptions import HTTPError
from ndex2.exceptions import NDExError
from ndex2.exceptions import NDExNotFoundError
from ndex2.exceptions import NDExUnauthorizedError
from ndex2.client import Ndex2
from ndex2.nice_cx_network import NiceCXNetwork
from ndex2.client import DecimalEncoder
import ndex2

SKIP_REASON = 'NDEX2_TEST_SERVER, NDEX2_TEST_USER, NDEX2_TEST_PASS ' \
              'environment variables not set, cannot run integration' \
              ' tests with server'


@unittest.skipUnless(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestInitTestCalls(unittest.TestCase):

    TEST_DIR = os.path.dirname(__file__)
    WNT_SIGNAL_FILE = os.path.join(TEST_DIR, 'data', 'wntsignaling.cx')
    GLYPICAN2_FILE = os.path.join(TEST_DIR, 'data', 'glypican2.cx')

    def get_ndex_credentials_as_tuple(self):
        """
        Gets ndex user credentials as tuple

        :return: {'server': SERVER, 'user': USER,
                  'password': PASS, 'user_agent': USER_AGENT}
        :rtype: dict
        """
        return {'server': os.getenv('NDEX2_TEST_SERVER'),
                'user': os.getenv('NDEX2_TEST_USER'),
                'password': os.getenv('NDEX2_TEST_PASS'),
                'user_agent': 'ndex2-client integration test'}

    def get_ndex2_client(self):
        creds = self.get_ndex_credentials_as_tuple()
        return Ndex2(creds['server'],
                     creds['user'],
                     creds['password'],
                     debug=True,
                     user_agent=creds['user_agent'])

    def wait_for_network_to_be_ready(self, client, netid,
                                     num_retries=3, retry_weight=0.5):
        retrycount = 1
        while retrycount < num_retries:
            netsum = client.get_network_summary(network_id=netid)
            if netsum['completed'] is True:
                return netsum
            retrycount += 1
            time.sleep(retry_weight)
        return None

    def test_create_nice_cx_from_server_cocanet2_network(self):
        net = ndex2.create_nice_cx_from_server('public.ndexbio.org',
                                               uuid='f1dd6cc3-0007-11e6-b550-06603eb7f303')

        self.assertEqual('CoCaNet2', net.get_name(), "Probably failing due to this error: "
                                                     "https://ndexbio.atlassian.net/browse/UD-2222")


