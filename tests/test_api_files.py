#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ndex2.api.files`."""

import os
import json
import unittest

import requests_mock

from ndex2.client import Ndex2
from ndex2.constants import FileType
from ndex2.constants import Permissions
from ndex2.constants import Visibility
from ndex2.exceptions import NDExError
from ndex2.exceptions import NDExInvalidParameterError
from ndex2.exceptions import NDExNotFoundError
from ndex2.exceptions import NDExUnauthorizedError

SKIP_REASON = 'NDEX2_TEST_SERVER environment variable detected, ' \
              'skipping for integration tests'

HOST = 'http://foo.com'
V3 = HOST + '/v3'
FOLDER_ID = '11111111-1111-1111-1111-111111111111'
NETWORK_ID = '22222222-2222-2222-2222-222222222222'
SHORTCUT_ID = '33333333-3333-3333-3333-333333333333'
USER_ID = '44444444-4444-4444-4444-444444444444'
JSON_HEADERS = {'Content-Type': 'application/json'}


def client(authenticated=True):
    if authenticated:
        return Ndex2(host=HOST, username='bob', password='secret',
                     skip_version_check=True)
    return Ndex2(host=HOST, skip_version_check=True)


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestFilesAPIWiring(unittest.TestCase):

    def test_namespace_present_and_shares_transport(self):
        c = client()
        self.assertIs(c._http, c.files._http)

    def test_shares_session_with_flat_methods(self):
        c = client()
        self.assertIs(c.s, c.files._http.session)

    def test_all_24_methods_present(self):
        methods = [m for m in dir(client().files) if not m.startswith('_')]
        self.assertEqual(24, len(methods))

    def test_discontinued_listing_methods_are_gone(self):
        """GET /v3/files/folders and /v3/files/shortcuts are being retired
        from the server, so the client no longer wraps them."""
        for gone in ('list_folders', 'list_shortcuts'):
            self.assertFalse(hasattr(client().files, gone), gone)

    def test_unauthenticated_write_rejected_before_request(self):
        c = client(authenticated=False)
        self.assertRaises(NDExUnauthorizedError, c.files.create_folder, 'x')


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestFolders(unittest.TestCase):

    def test_create_folder_minimal(self):
        c = client()
        with requests_mock.mock() as m:
            m.post(V3 + '/files/folders/', status_code=201,
                   json={'uuid': FOLDER_ID}, headers=JSON_HEADERS)
            self.assertEqual(FOLDER_ID, c.files.create_folder('My Folder'))
            self.assertEqual({'name': 'My Folder'},
                             json.loads(m.request_history[0].text))

    def test_create_folder_all_fields(self):
        c = client()
        with requests_mock.mock() as m:
            m.post(V3 + '/files/folders/', status_code=201,
                   json={'uuid': FOLDER_ID}, headers=JSON_HEADERS)
            c.files.create_folder('F', parent=FOLDER_ID, description='d',
                                  visibility='public')
            self.assertEqual({'name': 'F', 'parent': FOLDER_ID,
                              'description': 'd', 'visibility': 'PUBLIC'},
                             json.loads(m.request_history[0].text))

    def test_create_folder_uses_location_fallback(self):
        c = client()
        loc = V3 + '/files/folders/' + FOLDER_ID
        with requests_mock.mock() as m:
            m.post(V3 + '/files/folders/', status_code=201, text='',
                   headers={'Location': loc})
            self.assertEqual(FOLDER_ID, c.files.create_folder('F'))

    def test_create_folder_no_uuid_raises(self):
        c = client()
        with requests_mock.mock() as m:
            m.post(V3 + '/files/folders/', status_code=201, text='')
            self.assertRaises(NDExError, c.files.create_folder, 'F')

    def test_create_folder_invalid_name(self):
        c = client()
        for bad in (None, '   ', 5):
            self.assertRaises(NDExInvalidParameterError,
                              c.files.create_folder, bad)

    def test_create_folder_invalid_visibility(self):
        c = client()
        self.assertRaises(NDExInvalidParameterError, c.files.create_folder,
                          'F', None, None, 'SEMIPUBLIC')

    def test_get_folder(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/files/folders/' + FOLDER_ID,
                  json={'name': 'f'}, headers=JSON_HEADERS)
            self.assertEqual('f', c.files.get_folder(FOLDER_ID)['name'])

    def test_get_folder_access_key_param(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/files/folders/' + FOLDER_ID, json={},
                  headers=JSON_HEADERS)
            c.files.get_folder(FOLDER_ID, access_key='abc')
            self.assertEqual(['abc'], m.request_history[0].qs['accesskey'])

    def test_get_folder_omits_none_params(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/files/folders/' + FOLDER_ID, json={},
                  headers=JSON_HEADERS)
            c.files.get_folder(FOLDER_ID)
            self.assertNotIn('accesskey', m.request_history[0].qs)

    def test_get_folder_not_found(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/files/folders/' + FOLDER_ID, status_code=404,
                  text='nope')
            self.assertRaises(NDExNotFoundError, c.files.get_folder,
                              FOLDER_ID)

    def test_update_folder(self):
        c = client()
        with requests_mock.mock() as m:
            m.put(V3 + '/files/folders/' + FOLDER_ID, status_code=204)
            c.files.update_folder(FOLDER_ID, name='new', parent=FOLDER_ID)
            self.assertEqual({'name': 'new', 'parent': FOLDER_ID},
                             json.loads(m.request_history[0].text))

    def test_update_folder_requires_a_field(self):
        c = client()
        self.assertRaises(NDExInvalidParameterError, c.files.update_folder,
                          FOLDER_ID)

    def test_delete_folder_defaults(self):
        c = client()
        with requests_mock.mock() as m:
            m.delete(V3 + '/files/folders/' + FOLDER_ID, status_code=204)
            c.files.delete_folder(FOLDER_ID)
            qs = m.request_history[0].qs
            self.assertEqual(['false'], qs['force'])
            self.assertEqual(['false'], qs['permanent'])

    def test_delete_folder_force_and_permanent(self):
        c = client()
        with requests_mock.mock() as m:
            m.delete(V3 + '/files/folders/' + FOLDER_ID, status_code=204)
            c.files.delete_folder(FOLDER_ID, force=True, permanent=True)
            qs = m.request_history[0].qs
            self.assertEqual(['true'], qs['force'])
            self.assertEqual(['true'], qs['permanent'])

    def test_list_folder_items(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/files/folders/' + FOLDER_ID + '/list',
                  json=[{'uuid': NETWORK_ID, 'type': 'NETWORK'}],
                  headers=JSON_HEADERS)
            res = c.files.list_folder_items(FOLDER_ID, item_type='network')
            self.assertEqual(1, len(res))
            url = m.request_history[0].url
            self.assertIn('type=NETWORK', url)
            self.assertIn('format=update', url)

    def test_list_folder_items_empty_returns_list(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/files/folders/' + FOLDER_ID + '/list',
                  status_code=204)
            self.assertEqual([], c.files.list_folder_items(FOLDER_ID))

    def test_list_folder_items_invalid_type(self):
        c = client()
        self.assertRaises(NDExInvalidParameterError,
                          c.files.list_folder_items, FOLDER_ID, 'GROUP')

    def test_folder_child_count(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/files/folders/' + FOLDER_ID + '/count',
                  json={'network': 3, 'folder': 1, 'shortcut': 0},
                  headers=JSON_HEADERS)
            self.assertEqual(3,
                             c.files.folder_child_count(FOLDER_ID)['network'])

    def test_folder_access_key(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/files/folders/' + FOLDER_ID + '/accesskey',
                  json={'accessKey': 'k'}, headers=JSON_HEADERS)
            self.assertEqual({'accessKey': 'k'},
                             c.files.folder_access_key(FOLDER_ID))


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestShortcuts(unittest.TestCase):

    def test_create_shortcut(self):
        c = client()
        with requests_mock.mock() as m:
            m.post(V3 + '/files/shortcuts/', status_code=201,
                   json={'uuid': SHORTCUT_ID}, headers=JSON_HEADERS)
            res = c.files.create_shortcut('link', NETWORK_ID, 'network',
                                          parent=FOLDER_ID)
            self.assertEqual(SHORTCUT_ID, res)
            self.assertEqual({'name': 'link', 'target': NETWORK_ID,
                              'targetType': 'NETWORK', 'parent': FOLDER_ID},
                             json.loads(m.request_history[0].text))

    def test_create_shortcut_requires_target_type(self):
        c = client()
        self.assertRaises(NDExInvalidParameterError, c.files.create_shortcut,
                          'link', NETWORK_ID, None)

    def test_get_shortcut(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/files/shortcuts/' + SHORTCUT_ID,
                  json={'target': NETWORK_ID}, headers=JSON_HEADERS)
            self.assertEqual(NETWORK_ID,
                             c.files.get_shortcut(SHORTCUT_ID)['target'])

    def test_update_shortcut(self):
        c = client()
        with requests_mock.mock() as m:
            m.put(V3 + '/files/shortcuts/' + SHORTCUT_ID, status_code=204)
            c.files.update_shortcut(SHORTCUT_ID, name='n',
                                    target_type='folder')
            self.assertEqual({'name': 'n', 'targetType': 'FOLDER'},
                             json.loads(m.request_history[0].text))

    def test_update_shortcut_requires_a_field(self):
        c = client()
        self.assertRaises(NDExInvalidParameterError, c.files.update_shortcut,
                          SHORTCUT_ID)

    def test_delete_shortcut(self):
        c = client()
        with requests_mock.mock() as m:
            m.delete(V3 + '/files/shortcuts/' + SHORTCUT_ID, status_code=204)
            self.assertIsNone(c.files.delete_shortcut(SHORTCUT_ID))


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestTrash(unittest.TestCase):

    def test_list_trash(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/files/trash', json=[{'uuid': NETWORK_ID}],
                  headers=JSON_HEADERS)
            self.assertEqual(1, len(c.files.list_trash()))

    def test_restore(self):
        c = client()
        with requests_mock.mock() as m:
            m.post(V3 + '/files/trash/restore', status_code=204)
            c.files.restore(networks=[NETWORK_ID], folders=FOLDER_ID)
            self.assertEqual({'networks': [NETWORK_ID],
                              'folders': [FOLDER_ID]},
                             json.loads(m.request_history[0].text))

    def test_restore_requires_a_field(self):
        self.assertRaises(NDExInvalidParameterError, client().files.restore)

    def test_restore_rejects_empty_list(self):
        self.assertRaises(NDExInvalidParameterError, client().files.restore,
                          [])

    def test_clear_trash(self):
        c = client()
        with requests_mock.mock() as m:
            m.delete(V3 + '/files/trash', status_code=204)
            self.assertIsNone(c.files.clear_trash())

    def test_delete_permanently(self):
        c = client()
        with requests_mock.mock() as m:
            m.delete(V3 + '/files/trash/' + NETWORK_ID, status_code=204)
            self.assertIsNone(c.files.delete_permanently(NETWORK_ID))


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestSharing(unittest.TestCase):

    def test_share_with_dict(self):
        c = client()
        with requests_mock.mock() as m:
            m.post(V3 + '/files/sharing/share', json={NETWORK_ID: 'k'},
                   headers=JSON_HEADERS)
            res = c.files.share({NETWORK_ID: FileType.NETWORK})
            self.assertEqual({NETWORK_ID: 'k'}, res)
            self.assertEqual({'files': {NETWORK_ID: 'NETWORK'}},
                             json.loads(m.request_history[0].text))

    def test_share_with_default_type(self):
        c = client()
        with requests_mock.mock() as m:
            m.post(V3 + '/files/sharing/share', json={},
                   headers=JSON_HEADERS)
            c.files.share([NETWORK_ID, FOLDER_ID],
                          default_type=FileType.NETWORK)
            self.assertEqual({NETWORK_ID: 'NETWORK', FOLDER_ID: 'NETWORK'},
                             json.loads(m.request_history[0].text)['files'])

    def test_share_with_pairs(self):
        c = client()
        with requests_mock.mock() as m:
            m.post(V3 + '/files/sharing/share', json={},
                   headers=JSON_HEADERS)
            c.files.share([(NETWORK_ID, 'network'), (FOLDER_ID, 'folder')])
            self.assertEqual({NETWORK_ID: 'NETWORK', FOLDER_ID: 'FOLDER'},
                             json.loads(m.request_history[0].text)['files'])

    def test_share_missing_type_raises(self):
        self.assertRaises(NDExInvalidParameterError, client().files.share,
                          [NETWORK_ID])

    def test_share_empty_raises(self):
        self.assertRaises(NDExInvalidParameterError, client().files.share, [])

    def test_unshare(self):
        c = client()
        with requests_mock.mock() as m:
            m.post(V3 + '/files/sharing/unshare', status_code=204)
            c.files.unshare(NETWORK_ID, default_type='network')
            self.assertEqual({'files': {NETWORK_ID: 'NETWORK'}},
                             json.loads(m.request_history[0].text))

    def test_set_members(self):
        c = client()
        with requests_mock.mock() as m:
            m.post(V3 + '/files/sharing/members', json={},
                   headers=JSON_HEADERS)
            c.files.set_members({FOLDER_ID: FileType.FOLDER},
                                {USER_ID: 'write'})
            self.assertEqual({'files': {FOLDER_ID: 'FOLDER'},
                              'members': {USER_ID: 'WRITE'}},
                             json.loads(m.request_history[0].text))

    def test_set_members_invalid_permission(self):
        self.assertRaises(NDExInvalidParameterError,
                          client().files.set_members,
                          {NETWORK_ID: 'network'}, {USER_ID: 'SUPERUSER'})

    def test_set_members_empty_members(self):
        self.assertRaises(NDExInvalidParameterError,
                          client().files.set_members,
                          {NETWORK_ID: 'network'}, {})

    def test_set_members_accepts_all_permissions(self):
        c = client()
        for perm in (Permissions.READ, Permissions.WRITE, Permissions.ADMIN,
                     Permissions.MEMBER):
            with requests_mock.mock() as m:
                m.post(V3 + '/files/sharing/members', json={},
                       headers=JSON_HEADERS)
                c.files.set_members({NETWORK_ID: 'network'},
                                    {USER_ID: perm})
                self.assertEqual(
                    perm,
                    json.loads(m.request_history[0].text)['members'][USER_ID])

    def test_list_members(self):
        c = client()
        with requests_mock.mock() as m:
            m.post(V3 + '/files/sharing/members/list',
                   json=[{'uuid': NETWORK_ID}], headers=JSON_HEADERS)
            res = c.files.list_members({NETWORK_ID: 'network'})
            self.assertEqual(1, len(res))
            self.assertEqual({NETWORK_ID: 'NETWORK'},
                             json.loads(m.request_history[0].text))

    def test_list_shared(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/files/sharing/list', json=[],
                  headers=JSON_HEADERS)
            self.assertEqual([], c.files.list_shared())


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestCopyCountVisibilitySearch(unittest.TestCase):

    def test_copy(self):
        c = client()
        new_id = '66666666-6666-6666-6666-666666666666'
        with requests_mock.mock() as m:
            m.post(V3 + '/files/copy', status_code=201,
                   json={'uuid': new_id}, headers=JSON_HEADERS)
            self.assertEqual(new_id, c.files.copy(NETWORK_ID, 'network',
                                                  FOLDER_ID))
            self.assertEqual({'fileId': NETWORK_ID, 'type': 'NETWORK',
                              'targetId': FOLDER_ID},
                             json.loads(m.request_history[0].text))

    def test_count(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/files/count',
                  json={'network': 9, 'folder': 2, 'shortcut': 1},
                  headers=JSON_HEADERS)
            self.assertEqual(9, c.files.count()['network'])

    def test_set_visibility(self):
        c = client()
        with requests_mock.mock() as m:
            m.post(V3 + '/batch/files/setvisibility', status_code=204)
            c.files.set_visibility('public', [NETWORK_ID],
                                   default_type='network')
            self.assertEqual({'visibility': 'PUBLIC',
                              'files': {NETWORK_ID: 'NETWORK'}},
                             json.loads(m.request_history[0].text))

    def test_set_visibility_accepts_mixed_types(self):
        """setvisibility works on folders and shortcuts, not just networks."""
        c = client()
        with requests_mock.mock() as m:
            m.post(V3 + '/batch/files/setvisibility', status_code=204)
            c.files.set_visibility(Visibility.PRIVATE,
                                   {NETWORK_ID: FileType.NETWORK,
                                    FOLDER_ID: FileType.FOLDER,
                                    SHORTCUT_ID: FileType.SHORTCUT})
            self.assertEqual({NETWORK_ID: 'NETWORK', FOLDER_ID: 'FOLDER',
                              SHORTCUT_ID: 'SHORTCUT'},
                             json.loads(m.request_history[0].text)['files'])

    def test_set_visibility_requires_visibility(self):
        self.assertRaises(NDExInvalidParameterError,
                          client().files.set_visibility, None, [NETWORK_ID],
                          'network')

    def test_search_defaults(self):
        c = client()
        with requests_mock.mock() as m:
            m.post(V3 + '/search/files',
                   json={'numFound': 0, 'start': 0, 'files': []},
                   headers=JSON_HEADERS)
            self.assertEqual(0, c.files.search()['numFound'])
            self.assertEqual({'searchString': ''},
                             json.loads(m.request_history[0].text))
            qs = m.request_history[0].qs
            self.assertEqual(['0'], qs['start'])
            self.assertEqual(['100'], qs['size'])
            self.assertNotIn('visibility', qs)

    def test_search_all_filters(self):
        c = client()
        with requests_mock.mock() as m:
            m.post(V3 + '/search/files', json={}, headers=JSON_HEADERS)
            c.files.search(search_string='brca', account_name='bob',
                           permission='write', file_type='folder',
                           visibility='private', start=20, size=10)
            self.assertEqual({'searchString': 'brca', 'accountName': 'bob',
                              'permission': 'WRITE', 'type': 'FOLDER'},
                             json.loads(m.request_history[0].text))
            url = m.request_history[0].url
            self.assertIn('visibility=PRIVATE', url)
            self.assertIn('start=20', url)
            self.assertIn('size=10', url)

    def test_search_rejects_unlisted(self):
        self.assertRaises(NDExInvalidParameterError, client().files.search,
                          '', None, None, None, 'UNLISTED')

    def test_search_private_requires_auth(self):
        self.assertRaises(NDExUnauthorizedError,
                          client(authenticated=False).files.search,
                          '', None, None, None, 'PRIVATE')

    def test_search_public_allows_anonymous(self):
        c = client(authenticated=False)
        with requests_mock.mock() as m:
            m.post(V3 + '/search/files', json={}, headers=JSON_HEADERS)
            self.assertEqual({}, c.files.search(visibility='public'))


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestExistingMethodsUnaffected(unittest.TestCase):
    """Adding the namespace must not disturb the flat v2 API."""

    def test_flat_networkset_call_still_targets_v2(self):
        c = client()
        with requests_mock.mock() as m:
            m.post(HOST + '/v2/networkset', text=FOLDER_ID,
                   headers={'Content-Type': 'text/plain'})
            c.create_networkset('My Set', 'desc')
            self.assertIn('/v2/networkset', m.request_history[0].url)

    def test_flat_and_namespace_share_credentials(self):
        c = client()
        self.assertEqual(('bob', 'secret'), c.s.auth)
        self.assertEqual(('bob', 'secret'), c.files._http.session.auth)


if __name__ == '__main__':
    unittest.main()


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestNoneIdentifiersRejected(unittest.TestCase):
    """A None identifier must be rejected, not stringified to 'None'."""

    def test_create_shortcut_none_target(self):
        self.assertRaises(NDExInvalidParameterError,
                          client().files.create_shortcut,
                          'link', None, 'network')

    def test_copy_none_file_id(self):
        self.assertRaises(NDExInvalidParameterError, client().files.copy,
                          None, 'network', FOLDER_ID)

    def test_copy_none_target_id(self):
        self.assertRaises(NDExInvalidParameterError, client().files.copy,
                          NETWORK_ID, 'network', None)

    def test_require_id_accepts_uuid_objects(self):
        import uuid
        from ndex2.api._validators import require_id
        val = uuid.uuid4()
        self.assertEqual(str(val), require_id(val, 'x'))

    def test_require_id_rejects_none_and_blank(self):
        from ndex2.api._validators import require_id
        self.assertRaises(NDExInvalidParameterError, require_id, None, 'x')
        self.assertRaises(NDExInvalidParameterError, require_id, '   ', 'x')
