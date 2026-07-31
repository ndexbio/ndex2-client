# -*- coding: utf-8 -*-

"""Integration tests for ``client.users`` against a live server."""

import os
import unittest

from ndex2.exceptions import NDExError
from ndex2.exceptions import NDExInvalidParameterError

from tests.v3_integration_base import SKIP_REASON
from tests.v3_integration_base import V3IntegrationBase


@unittest.skipUnless(os.getenv('NDEX2_TEST_SERVER') is not None,
                     SKIP_REASON)
class TestUsersIntegration(V3IntegrationBase):

    def test_get_returns_the_authenticated_user(self):
        record = self.client.users.get(self.user)
        self.assertTrue(isinstance(record, dict))
        self.assertIn('externalId', record)

    def test_get_agrees_with_the_flat_lookup(self):
        """client.users.get is v3; get_user_by_username is v2."""
        v3 = self.client.users.get(self.user)['externalId']
        v2 = self.client.get_id_for_user(self.user)
        self.assertEqual(v2, v3)

    def test_get_unknown_user_raises(self):
        self.assertRaises(NDExError, self.client.users.get,
                          'zz-no-such-user-' + self.tag)

    def test_get_rejects_bad_input_before_sending(self):
        for bad in (None, '', '   '):
            self.assertRaises(NDExInvalidParameterError,
                              self.client.users.get, bad)

    def test_home_returns_a_list(self):
        items = self.client.users.home(self.user_id())
        self.assertTrue(isinstance(items, list))

    def test_home_shows_a_new_top_level_folder(self):
        folder = self.new_folder('home-visible')
        uuids = [i.get('uuid') for i in
                 self.client.users.home(self.user_id())]
        self.assertIn(folder, uuids)

    def test_home_items_always_carry_uuid_and_type(self):
        self.new_folder('shape-check')
        for item in self.client.users.home(self.user_id()):
            self.assertIn('uuid', item)
            self.assertIn('type', item)

    def test_home_works_anonymously(self):
        """Anonymous callers see public items only, but may call."""
        self.assertTrue(isinstance(self.anon.users.home(self.user_id()),
                                   list))


if __name__ == '__main__':
    unittest.main()
