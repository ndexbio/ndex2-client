# -*- coding: utf-8 -*-

"""Integration tests for ``client.admin`` against a live server."""

import os
import unittest

from tests.v3_integration_base import SKIP_REASON
from tests.v3_integration_base import V3IntegrationBase


@unittest.skipUnless(os.getenv('NDEX2_TEST_SERVER') is not None,
                     SKIP_REASON)
class TestAdminIntegration(V3IntegrationBase):

    def test_status_returns_an_object(self):
        status = self.client.admin.status()
        self.assertTrue(isinstance(status, dict),
                        'expected a dict, got ' + str(type(status)))

    def test_status_works_without_credentials(self):
        self.assertTrue(isinstance(self.anon.admin.status(), dict))

    def test_status_does_not_populate_the_v2_cache(self):
        """The flat update_status caches on self.status; this must not."""
        before = dict(self.client.status)
        self.client.admin.status()
        self.assertEqual(before, dict(self.client.status))

    def test_compact_format_accepted(self):
        self.assertTrue(isinstance(self.client.admin.status(format='standard'),
                                   dict))


if __name__ == '__main__':
    unittest.main()
