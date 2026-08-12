# -*- coding: utf-8 -*-

"""Integration tests for ``client.files`` against a live server."""

import os
import time
import unittest

from ndex2.constants import FileType
from ndex2.constants import Visibility
from ndex2.exceptions import NDExError
from ndex2.exceptions import NDExInvalidParameterError

from tests.v3_integration_base import SKIP_REASON
from tests.v3_integration_base import V3IntegrationBase


@unittest.skipUnless(os.getenv('NDEX2_TEST_SERVER') is not None,
                     SKIP_REASON)
class TestFoldersIntegration(V3IntegrationBase):

    def test_create_and_get_folder(self):
        folder = self.new_folder('basic')
        record = self.client.files.get_folder(folder)
        self.assertEqual(self.name('basic'), record.get('name'))

    def test_nested_folder_reports_its_parent(self):
        parent = self.new_folder('parent')
        child = self.new_folder('child', parent=parent)
        self.assertEqual(str(parent),
                         str(self.client.files.get_folder(child)
                             .get('parent')))

    def test_update_folder_description(self):
        folder = self.new_folder('updatable')
        self.client.files.update_folder(folder, description='changed')
        self.assertEqual('changed',
                         self.client.files.get_folder(folder)
                         .get('description'))

    def test_new_folder_appears_in_user_home(self):
        """A top level folder shows up in the user's home listing. The
        former list_folders() wrapper is gone: GET /v3/files/folders is
        being retired from the server."""
        folder = self.new_folder('listed')
        uuids = [i.get('uuid') for i in
                 self.client.users.home(self.user_id())]
        self.assertIn(folder, uuids)

    def test_child_count_reflects_contents(self):
        parent = self.new_folder('counted')
        self.assertEqual(0,
                         self.client.files.folder_child_count(parent)
                         .get('folder', 0))
        self.new_folder('counted-child', parent=parent)
        self.assertEqual(1,
                         self.client.files.folder_child_count(parent)
                         .get('folder'))

    def test_list_folder_items_shape(self):
        parent = self.new_folder('items-parent')
        child = self.new_folder('items-child', parent=parent)
        items = self.client.files.list_folder_items(parent)
        self.assertEqual(1, len(items))
        # uuid and type are the only keys guaranteed across item types
        self.assertEqual(child, items[0]['uuid'])
        self.assertEqual(FileType.FOLDER, items[0]['type'])

    def test_list_folder_items_type_filter(self):
        parent = self.new_folder('filter-parent')
        self.new_folder('filter-child', parent=parent)
        self.assertEqual(
            0, len(self.client.files.list_folder_items(
                parent, item_type=FileType.NETWORK)))
        self.assertEqual(
            1, len(self.client.files.list_folder_items(
                parent, item_type=FileType.FOLDER)))

    def test_list_folder_items_defaults_to_home(self):
        """With no argument the special 'home' id lists the user's top
        level, which is where a new top level folder lands."""
        folder = self.new_folder('home-default')
        uuids = [i.get('uuid') for i in self.client.files.list_folder_items()]
        self.assertIn(folder, uuids)

    def test_home_default_agrees_with_users_home(self):
        """files.list_folder_items() and users.home() reach the same
        listing by different routes."""
        self.new_folder('home-agree')
        via_files = sorted(i['uuid'] for i in
                           self.client.files.list_folder_items())
        via_users = sorted(i['uuid'] for i in
                           self.client.users.home(self.user_id()))
        self.assertEqual(via_users, via_files)

    def test_get_unknown_folder_raises(self):
        self.assertRaises(NDExError, self.client.files.get_folder,
                          '00000000-0000-0000-0000-000000000000')

    def test_deleted_folder_is_no_longer_retrievable(self):
        folder = self.client.files.create_folder(self.name('doomed'))
        self.client.files.delete_folder(folder, force=True, permanent=True)
        self.assertRaises(NDExError, self.client.files.get_folder, folder)


@unittest.skipUnless(os.getenv('NDEX2_TEST_SERVER') is not None,
                     SKIP_REASON)
class TestShortcutsIntegration(V3IntegrationBase):

    def test_create_shortcut_to_a_folder(self):
        target = self.new_folder('shortcut-target')
        parent = self.new_folder('shortcut-parent')
        sid = self.client.files.create_shortcut(
            self.name('shortcut'), target, FileType.FOLDER, parent=parent)
        self._shortcuts.append(sid)
        record = self.client.files.get_shortcut(sid)
        self.assertEqual(str(target), str(record.get('target')))

    def test_top_level_shortcut_appears_in_user_home(self):
        """The former list_shortcuts() wrapper is gone: GET
        /v3/files/shortcuts is being retired from the server."""
        target = self.new_folder('sc-list-target')
        sid = self.client.files.create_shortcut(
            self.name('sc-listed'), target, FileType.FOLDER)
        self._shortcuts.append(sid)
        uuids = [i.get('uuid') for i in
                 self.client.users.home(self.user_id())]
        self.assertIn(sid, uuids)


@unittest.skipUnless(os.getenv('NDEX2_TEST_SERVER') is not None,
                     SKIP_REASON)
class TestSharingIntegration(V3IntegrationBase):

    def test_share_mints_a_key_that_allows_anonymous_read(self):
        folder = self.new_folder('shared')
        keys = self.client.files.share({folder: FileType.FOLDER})
        key = keys.get(folder) or list(keys.values())[0]
        self.assertTrue(key)
        record = self.anon.files.get_folder(folder, access_key=key)
        self.assertEqual(self.name('shared'), record.get('name'))
        self.client.files.unshare({folder: FileType.FOLDER})

    def test_folder_access_key_is_retrievable_after_sharing(self):
        """share() mints an access key; folder_access_key() reads it back.

        Note that a folder shared this way does not necessarily appear in
        list_shared(), which reports a different notion of sharing.
        """
        folder = self.new_folder('shared-key')
        self.client.files.share({folder: FileType.FOLDER})
        try:
            self.assertTrue(
                isinstance(self.client.files.folder_access_key(folder), dict))
        finally:
            self.client.files.unshare({folder: FileType.FOLDER})

    def test_list_shared_returns_a_list(self):
        self.assertTrue(isinstance(self.client.files.list_shared(), list))

    def test_set_members_rejects_a_bad_permission_locally(self):
        folder = self.new_folder('bad-perm')
        self.assertRaises(NDExInvalidParameterError,
                          self.client.files.set_members,
                          {folder: FileType.FOLDER},
                          {self.user_id(): 'SUPERUSER'})

    def test_set_visibility_on_a_folder(self):
        folder = self.new_folder('visible')
        self.client.files.set_visibility(
            Visibility.PUBLIC, {folder: FileType.FOLDER})
        self.assertEqual(Visibility.PUBLIC,
                         str(self.client.files.get_folder(folder)
                             .get('visibility')).upper())
        self.client.files.set_visibility(
            Visibility.PRIVATE, {folder: FileType.FOLDER})
        self.assertEqual(Visibility.PRIVATE,
                         str(self.client.files.get_folder(folder)
                             .get('visibility')).upper())


@unittest.skipUnless(os.getenv('NDEX2_TEST_SERVER') is not None,
                     SKIP_REASON)
class TestCountTrashSearchIntegration(V3IntegrationBase):

    def test_count_returns_the_three_types(self):
        counts = self.client.files.count()
        for key in ('network', 'folder', 'shortcut'):
            self.assertIn(key, counts)

    def test_count_increases_after_creating_a_folder(self):
        before = self.client.files.count().get('folder', 0)
        self.new_folder('counted-total')
        self.assertEqual(before + 1,
                         self.client.files.count().get('folder'))

    def test_search_returns_a_well_formed_result(self):
        result = self.client.files.search(self.tag,
                                          visibility=Visibility.PRIVATE,
                                          size=50)
        self.assertIn('numFound', result)
        self.assertTrue(isinstance(result.get('files', []), list))

    def test_search_eventually_finds_a_new_folder(self):
        """Search is backed by an index that updates asynchronously, so a
        just-created folder may not be visible yet. Poll briefly, then skip
        rather than fail, since indexing lag is not a client defect.
        """
        folder = self.new_folder('searchable')
        deadline = time.time() + 20
        while time.time() < deadline:
            result = self.client.files.search(
                self.tag, visibility=Visibility.PRIVATE, size=50)
            if folder in [f.get('uuid') for f in result.get('files', [])]:
                return
            time.sleep(2)
        self.skipTest('folder not indexed within 20s; search indexing lag')

    def test_search_rejects_unlisted_locally(self):
        self.assertRaises(NDExInvalidParameterError,
                          self.client.files.search, '', None, None, None,
                          Visibility.UNLISTED)

    def test_trash_then_restore_a_folder(self):
        folder = self.new_folder('trashable')
        self.client.files.delete_folder(folder)
        trashed = [i.get('uuid') for i in self.client.files.list_trash()]
        self.assertIn(folder, trashed)
        self.client.files.restore(folders=[folder])
        self.assertEqual(self.name('trashable'),
                         self.client.files.get_folder(folder).get('name'))


if __name__ == '__main__':
    unittest.main()
