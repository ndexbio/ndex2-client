# -*- coding: utf-8 -*-

"""Integration tests for ``client.networks`` against a live server."""

import os
import unittest

from ndex2.constants import FileType
from ndex2.exceptions import NDExError
from ndex2.exceptions import NDExInvalidParameterError

from tests.v3_integration_base import SKIP_REASON
from tests.v3_integration_base import V3IntegrationBase


@unittest.skipUnless(os.getenv('NDEX2_TEST_SERVER') is not None,
                     SKIP_REASON)
class TestNetworkCreationInFolder(V3IntegrationBase):
    """The folder_id argument added to the flat CX2 creation methods."""

    def test_network_created_in_folder_reports_that_folder(self):
        folder = self.new_folder('net-home')
        net = self.new_network('placed', folder_id=folder)
        summary = self.client.networks.get_summary(net)
        self.assertEqual(str(folder), str(summary.get('folderId')),
                         'folder_id did not take effect')

    def test_network_created_in_folder_appears_in_its_listing(self):
        folder = self.new_folder('net-listing')
        net = self.new_network('listed', folder_id=folder)
        uuids = [i['uuid'] for i in
                 self.client.files.list_folder_items(folder)]
        self.assertIn(net, uuids)

    def test_network_without_folder_id_is_not_in_that_folder(self):
        folder = self.new_folder('empty-home')
        self.new_network('unplaced')
        self.assertEqual([], self.client.files.list_folder_items(folder))


@unittest.skipUnless(os.getenv('NDEX2_TEST_SERVER') is not None,
                     SKIP_REASON)
class TestNetworkSummaries(V3IntegrationBase):

    def test_get_summary_returns_a_dict(self):
        net = self.new_network('summary')
        summary = self.client.networks.get_summary(net)
        self.assertTrue(isinstance(summary, dict))

    def test_v3_summary_reports_folder_id(self):
        """The v2 summary also reports folderId on current servers, so this
        only asserts the v3 value is present and correct."""
        folder = self.new_folder('summary-folder')
        net = self.new_network('summary-diff', folder_id=folder)
        summary = self.client.networks.get_summary(net)
        self.assertIn('folderId', summary)
        self.assertEqual(str(folder), str(summary['folderId']))

    def test_get_summaries_batch(self):
        first = self.new_network('batch-one')
        second = self.new_network('batch-two')
        results = self.client.networks.get_summaries([first, second])
        self.assertEqual(2, len(results))

    def test_get_summaries_rejects_empty_locally(self):
        self.assertRaises(NDExInvalidParameterError,
                          self.client.networks.get_summaries, [])

    def test_list_aspects(self):
        net = self.new_network('aspects')
        aspects = self.client.networks.list_aspects(net)
        self.assertTrue(isinstance(aspects, list))
        self.assertTrue(len(aspects) > 0)

    def test_get_summary_of_unknown_network_raises(self):
        self.assertRaises(NDExError, self.client.networks.get_summary,
                          '00000000-0000-0000-0000-000000000000')


@unittest.skipUnless(os.getenv('NDEX2_TEST_SERVER') is not None,
                     SKIP_REASON)
class TestNetworkQueries(V3IntegrationBase):

    def test_query_returns_cx2(self):
        net = self.new_network('queryable')
        res = self.client.networks.query(net, 'ALPHA', search_depth=1)
        self.assertEqual(200, res.status_code)
        self.assertTrue(len(res.content) > 0)

    def test_interconnect_query_returns_cx2(self):
        net = self.new_network('interconnect')
        res = self.client.networks.interconnect_query(net, 'ALPHA BETA')
        self.assertEqual(200, res.status_code)

    def test_get_node_attributes(self):
        net = self.new_network('nodes')
        res = self.client.networks.get_node_attributes(
            net, attribute_names=['name'])
        self.assertEqual(200, res.status_code)

    def test_export_as_tsv(self):
        net = self.new_network('exportable')
        res = self.client.networks.export_as_tsv(net)
        self.assertEqual(200, res.status_code)

    def test_query_rejects_bad_id_locally(self):
        self.assertRaises(NDExInvalidParameterError,
                          self.client.networks.query, None, 'x')


@unittest.skipUnless(os.getenv('NDEX2_TEST_SERVER') is not None,
                     SKIP_REASON)
class TestNetworkMoveAndDelete(V3IntegrationBase):

    def test_move_to_folder(self):
        origin = self.new_folder('move-from')
        target = self.new_folder('move-to')
        net = self.new_network('movable', folder_id=origin)
        self.client.networks.move_to_folder(target, [net])
        self.assertEqual(str(target),
                         str(self.client.networks.get_summary(net)
                             .get('folderId')))

    def test_move_to_folder_rejects_empty_locally(self):
        folder = self.new_folder('move-empty')
        self.assertRaises(NDExInvalidParameterError,
                          self.client.networks.move_to_folder, folder, [])

    def test_delete_is_recoverable_by_default(self):
        net = self.new_network('soft-delete')
        self.client.networks.delete(net)
        trashed = [i.get('uuid') for i in self.client.files.list_trash()]
        self.assertIn(net, trashed)
        self.client.files.restore(networks=[net])
        self.assertTrue(isinstance(self.client.networks.get_summary(net),
                                   dict))

    def test_shortcut_can_point_at_a_network(self):
        folder = self.new_folder('sc-net-folder')
        net = self.new_network('sc-net')
        sid = self.client.files.create_shortcut(
            self.name('sc-to-net'), net, FileType.NETWORK, parent=folder)
        self._shortcuts.append(sid)
        self.assertEqual(str(net),
                         str(self.client.files.get_shortcut(sid)
                             .get('target')))


if __name__ == '__main__':
    unittest.main()
