#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ndex2.client_v3` package."""

import io
import os
import json
import unittest

import requests_mock

from ndex2.client_v3 import Ndex3
from ndex2.client_v3 import FileType
from ndex2.client_v3 import Visibility
from ndex2.client_v3 import Permissions
from ndex2.exceptions import NDExError
from ndex2.exceptions import NDExInvalidParameterError
from ndex2.exceptions import NDExNotFoundError
from ndex2.exceptions import NDExUnauthorizedError
from ndex2.exceptions import NDExUnsupportedCallError

SKIP_REASON = 'NDEX2_TEST_SERVER environment variable detected, ' \
              'skipping for integration tests'

HOST = 'http://foo.com'
V3 = HOST + '/v3'
FOLDER_ID = '11111111-1111-1111-1111-111111111111'
NETWORK_ID = '22222222-2222-2222-2222-222222222222'
SHORTCUT_ID = '33333333-3333-3333-3333-333333333333'
USER_ID = '44444444-4444-4444-4444-444444444444'
WORKSPACE_ID = '55555555-5555-5555-5555-555555555555'

JSON_HEADERS = {'Content-Type': 'application/json'}


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestNdex3(unittest.TestCase):

    def get_client(self, authenticated=True):
        if authenticated is True:
            return Ndex3(host=HOST, username='bob', password='secret')
        return Ndex3(host=HOST)

    # ------------------------------------------------------------------
    # constructor and auth
    # ------------------------------------------------------------------

    def test_constructor_defaults_to_v3_endpoint(self):
        client = self.get_client()
        self.assertEqual('/v3', client.version_endpoint)
        self.assertEqual(HOST, client.host)
        self.assertEqual(('bob', 'secret'), client.s.auth)

    def test_constructor_strips_trailing_slash(self):
        client = Ndex3(host=HOST + '/')
        self.assertEqual(HOST, client.host)

    def test_constructor_prepends_scheme(self):
        client = Ndex3(host='foo.com')
        self.assertEqual('http://foo.com', client.host)

    def test_constructor_with_bearer_token(self):
        client = Ndex3(host=HOST, bearer_token='tok')
        self.assertEqual('Bearer tok', client.s.headers['Authorization'])

    def test_bearer_token_wins_over_basic(self):
        client = Ndex3(host=HOST, username='bob', password='secret',
                       bearer_token='tok')
        self.assertEqual('Bearer tok', client.s.headers['Authorization'])
        self.assertIsNone(client.s.auth)

    def test_unauthenticated_call_raises(self):
        client = self.get_client(authenticated=False)
        self.assertRaises(NDExUnauthorizedError,
                          client.create_folder, 'name')

    def test_update_status_rejects_non_v3_server(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/admin/status', text='not json',
                     headers={'Content-Type': 'text/plain'})
            self.assertRaises(NDExError, client.update_status)

    def test_update_status_success(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/admin/status', json={'message': 'Online'},
                     headers=JSON_HEADERS)
            self.assertEqual({'message': 'Online'}, client.update_status())
            self.assertEqual({'message': 'Online'}, client.status)

    # ------------------------------------------------------------------
    # error translation
    # ------------------------------------------------------------------

    def test_404_becomes_not_found_error(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/files/folders/' + FOLDER_ID, status_code=404,
                     text='nope')
            self.assertRaises(NDExNotFoundError, client.get_folder,
                              FOLDER_ID)

    def test_401_becomes_unauthorized_error(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/files/folders/' + FOLDER_ID, status_code=401,
                     text='denied')
            self.assertRaises(NDExUnauthorizedError, client.get_folder,
                              FOLDER_ID)

    def test_500_becomes_ndex_error(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/files/folders/' + FOLDER_ID, status_code=500,
                     text='boom')
            self.assertRaises(NDExError, client.get_folder, FOLDER_ID)

    def test_204_returns_none(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.delete(V3 + '/files/shortcuts/' + SHORTCUT_ID,
                        status_code=204)
            self.assertIsNone(client.delete_shortcut(SHORTCUT_ID))

    # ------------------------------------------------------------------
    # folders
    # ------------------------------------------------------------------

    def test_create_folder_minimal(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/files/folders/', status_code=201,
                      json={'uuid': FOLDER_ID}, headers=JSON_HEADERS)
            self.assertEqual(FOLDER_ID, client.create_folder('My Folder'))
            body = json.loads(mock.request_history[0].text)
            self.assertEqual({'name': 'My Folder'}, body)

    def test_create_folder_all_fields(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/files/folders/', status_code=201,
                      json={'uuid': FOLDER_ID}, headers=JSON_HEADERS)
            client.create_folder('My Folder', parent=FOLDER_ID,
                                 description='desc', visibility='public')
            body = json.loads(mock.request_history[0].text)
            self.assertEqual({'name': 'My Folder', 'parent': FOLDER_ID,
                              'description': 'desc',
                              'visibility': 'PUBLIC'}, body)

    def test_create_folder_falls_back_to_location_header(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            loc = V3 + '/files/folders/' + FOLDER_ID
            mock.post(V3 + '/files/folders/', status_code=201, text='',
                      headers={'Location': loc})
            self.assertEqual(FOLDER_ID, client.create_folder('My Folder'))

    def test_create_folder_no_uuid_raises(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/files/folders/', status_code=201, text='')
            self.assertRaises(NDExError, client.create_folder, 'My Folder')

    def test_create_folder_invalid_name(self):
        client = self.get_client()
        self.assertRaises(NDExInvalidParameterError, client.create_folder,
                          None)
        self.assertRaises(NDExInvalidParameterError, client.create_folder,
                          '   ')
        self.assertRaises(NDExInvalidParameterError, client.create_folder, 5)

    def test_create_folder_invalid_visibility(self):
        client = self.get_client()
        self.assertRaises(NDExInvalidParameterError, client.create_folder,
                          'name', None, None, 'SEMIPUBLIC')

    def test_get_folder(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/files/folders/' + FOLDER_ID,
                     json={'name': 'f', 'externalId': FOLDER_ID},
                     headers=JSON_HEADERS)
            res = client.get_folder(FOLDER_ID)
            self.assertEqual('f', res['name'])

    def test_get_folder_with_access_key(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/files/folders/' + FOLDER_ID, json={},
                     headers=JSON_HEADERS)
            client.get_folder(FOLDER_ID, access_key='abc')
            self.assertEqual(['abc'],
                             mock.request_history[0].qs['accesskey'])

    def test_get_folder_omits_none_params(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/files/folders/' + FOLDER_ID, json={},
                     headers=JSON_HEADERS)
            client.get_folder(FOLDER_ID)
            self.assertNotIn('accesskey', mock.request_history[0].qs)

    def test_update_folder(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.put(V3 + '/files/folders/' + FOLDER_ID, status_code=204)
            client.update_folder(FOLDER_ID, name='new', parent=FOLDER_ID)
            body = json.loads(mock.request_history[0].text)
            self.assertEqual({'name': 'new', 'parent': FOLDER_ID}, body)

    def test_update_folder_requires_a_field(self):
        client = self.get_client()
        self.assertRaises(NDExInvalidParameterError, client.update_folder,
                          FOLDER_ID)

    def test_delete_folder_defaults(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.delete(V3 + '/files/folders/' + FOLDER_ID, status_code=204)
            client.delete_folder(FOLDER_ID)
            qs = mock.request_history[0].qs
            self.assertEqual(['false'], qs['force'])
            self.assertEqual(['false'], qs['permanent'])

    def test_delete_folder_force_and_permanent(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.delete(V3 + '/files/folders/' + FOLDER_ID, status_code=204)
            client.delete_folder(FOLDER_ID, force=True, permanent=True)
            qs = mock.request_history[0].qs
            self.assertEqual(['true'], qs['force'])
            self.assertEqual(['true'], qs['permanent'])

    def test_list_folder_items(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/files/folders/' + FOLDER_ID + '/list',
                     json=[{'uuid': NETWORK_ID, 'type': 'NETWORK'}],
                     headers=JSON_HEADERS)
            res = client.list_folder_items(FOLDER_ID, item_type='network')
            self.assertEqual(1, len(res))
            url = mock.request_history[0].url
            self.assertIn('type=NETWORK', url)
            self.assertIn('format=update', url)

    def test_list_folder_items_empty_body_returns_list(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/files/folders/' + FOLDER_ID + '/list',
                     status_code=204)
            self.assertEqual([], client.list_folder_items(FOLDER_ID))

    def test_list_folder_items_invalid_type(self):
        client = self.get_client()
        self.assertRaises(NDExInvalidParameterError,
                          client.list_folder_items, FOLDER_ID, 'update',
                          'GROUP')

    def test_get_folder_child_count(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/files/folders/' + FOLDER_ID + '/count',
                     json={'network': 3, 'folder': 1, 'shortcut': 0},
                     headers=JSON_HEADERS)
            self.assertEqual(3, client.get_folder_child_count(
                FOLDER_ID)['network'])

    def test_get_folder_access_key(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/files/folders/' + FOLDER_ID + '/accesskey',
                     json={'accessKey': 'abc'}, headers=JSON_HEADERS)
            self.assertEqual({'accessKey': 'abc'},
                             client.get_folder_access_key(FOLDER_ID))

    def test_list_folders(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/files/folders/', json=[{'name': 'a'}],
                     headers=JSON_HEADERS)
            self.assertEqual(1, len(client.list_folders(limit=5)))
            self.assertEqual(['5'], mock.request_history[0].qs['limit'])

    # ------------------------------------------------------------------
    # shortcuts
    # ------------------------------------------------------------------

    def test_create_shortcut(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/files/shortcuts/', status_code=201,
                      json={'uuid': SHORTCUT_ID}, headers=JSON_HEADERS)
            res = client.create_shortcut('link', NETWORK_ID, 'network',
                                         parent=FOLDER_ID)
            self.assertEqual(SHORTCUT_ID, res)
            body = json.loads(mock.request_history[0].text)
            self.assertEqual({'name': 'link', 'target': NETWORK_ID,
                              'targetType': 'NETWORK',
                              'parent': FOLDER_ID}, body)

    def test_create_shortcut_requires_target_type(self):
        client = self.get_client()
        self.assertRaises(NDExInvalidParameterError, client.create_shortcut,
                          'link', NETWORK_ID, None)

    def test_get_shortcut(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/files/shortcuts/' + SHORTCUT_ID,
                     json={'target': NETWORK_ID}, headers=JSON_HEADERS)
            self.assertEqual(NETWORK_ID,
                             client.get_shortcut(SHORTCUT_ID)['target'])

    def test_update_shortcut(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.put(V3 + '/files/shortcuts/' + SHORTCUT_ID, status_code=204)
            client.update_shortcut(SHORTCUT_ID, name='n',
                                   target_type='folder')
            body = json.loads(mock.request_history[0].text)
            self.assertEqual({'name': 'n', 'targetType': 'FOLDER'}, body)

    def test_update_shortcut_requires_a_field(self):
        client = self.get_client()
        self.assertRaises(NDExInvalidParameterError, client.update_shortcut,
                          SHORTCUT_ID)

    def test_list_shortcuts(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/files/shortcuts/', json=[], headers=JSON_HEADERS)
            self.assertEqual([], client.list_shortcuts())

    # ------------------------------------------------------------------
    # files: count, trash, copy
    # ------------------------------------------------------------------

    def test_get_file_count(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/files/count',
                     json={'network': 9, 'folder': 2, 'shortcut': 1},
                     headers=JSON_HEADERS)
            self.assertEqual(9, client.get_file_count()['network'])

    def test_list_trash(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/files/trash', json=[{'uuid': NETWORK_ID}],
                     headers=JSON_HEADERS)
            self.assertEqual(1, len(client.list_trash()))

    def test_restore_from_trash(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/files/trash/restore', status_code=204)
            client.restore_from_trash(networks=[NETWORK_ID],
                                      folders=FOLDER_ID)
            body = json.loads(mock.request_history[0].text)
            self.assertEqual({'networks': [NETWORK_ID],
                              'folders': [FOLDER_ID]}, body)

    def test_restore_from_trash_requires_a_field(self):
        client = self.get_client()
        self.assertRaises(NDExInvalidParameterError,
                          client.restore_from_trash)

    def test_restore_from_trash_rejects_empty_list(self):
        client = self.get_client()
        self.assertRaises(NDExInvalidParameterError,
                          client.restore_from_trash, [])

    def test_clear_trash(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.delete(V3 + '/files/trash', status_code=204)
            self.assertIsNone(client.clear_trash())

    def test_delete_trashed_item(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.delete(V3 + '/files/trash/' + NETWORK_ID, status_code=204)
            self.assertIsNone(client.delete_trashed_item(NETWORK_ID))

    def test_copy_file(self):
        client = self.get_client()
        new_id = '66666666-6666-6666-6666-666666666666'
        with requests_mock.mock() as mock:
            mock.post(V3 + '/files/copy', status_code=201,
                      json={'uuid': new_id}, headers=JSON_HEADERS)
            res = client.copy_file(NETWORK_ID, 'network', FOLDER_ID)
            self.assertEqual(new_id, res)
            body = json.loads(mock.request_history[0].text)
            self.assertEqual({'fileId': NETWORK_ID, 'type': 'NETWORK',
                              'targetId': FOLDER_ID}, body)

    # ------------------------------------------------------------------
    # files: sharing
    # ------------------------------------------------------------------

    def test_share_files_with_dict(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/files/sharing/share',
                      json={NETWORK_ID: 'key123'}, headers=JSON_HEADERS)
            res = client.share_files({NETWORK_ID: FileType.NETWORK})
            self.assertEqual({NETWORK_ID: 'key123'}, res)
            body = json.loads(mock.request_history[0].text)
            self.assertEqual({'files': {NETWORK_ID: 'NETWORK'}}, body)

    def test_share_files_with_default_type(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/files/sharing/share', json={},
                      headers=JSON_HEADERS)
            client.share_files([NETWORK_ID, FOLDER_ID],
                               default_type=FileType.NETWORK)
            body = json.loads(mock.request_history[0].text)
            self.assertEqual({NETWORK_ID: 'NETWORK', FOLDER_ID: 'NETWORK'},
                             body['files'])

    def test_share_files_with_pairs(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/files/sharing/share', json={},
                      headers=JSON_HEADERS)
            client.share_files([(NETWORK_ID, 'network'),
                                (FOLDER_ID, 'folder')])
            body = json.loads(mock.request_history[0].text)
            self.assertEqual({NETWORK_ID: 'NETWORK', FOLDER_ID: 'FOLDER'},
                             body['files'])

    def test_share_files_missing_type_raises(self):
        client = self.get_client()
        self.assertRaises(NDExInvalidParameterError, client.share_files,
                          [NETWORK_ID])

    def test_share_files_empty_raises(self):
        client = self.get_client()
        self.assertRaises(NDExInvalidParameterError, client.share_files, [])

    def test_unshare_files(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/files/sharing/unshare', status_code=204)
            client.unshare_files(NETWORK_ID, default_type='network')
            body = json.loads(mock.request_history[0].text)
            self.assertEqual({'files': {NETWORK_ID: 'NETWORK'}}, body)

    def test_set_sharing_members(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/files/sharing/members', json={},
                      headers=JSON_HEADERS)
            client.set_sharing_members({NETWORK_ID: FileType.NETWORK},
                                       {USER_ID: 'read'})
            body = json.loads(mock.request_history[0].text)
            self.assertEqual({'files': {NETWORK_ID: 'NETWORK'},
                              'members': {USER_ID: 'READ'}}, body)

    def test_set_sharing_members_invalid_permission(self):
        client = self.get_client()
        self.assertRaises(NDExInvalidParameterError,
                          client.set_sharing_members,
                          {NETWORK_ID: 'network'}, {USER_ID: 'SUPERUSER'})

    def test_set_sharing_members_empty_members(self):
        client = self.get_client()
        self.assertRaises(NDExInvalidParameterError,
                          client.set_sharing_members,
                          {NETWORK_ID: 'network'}, {})

    def test_list_sharing_members(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/files/sharing/members/list',
                      json=[{'uuid': NETWORK_ID}], headers=JSON_HEADERS)
            res = client.list_sharing_members({NETWORK_ID: 'network'})
            self.assertEqual(1, len(res))
            self.assertEqual({NETWORK_ID: 'NETWORK'},
                             json.loads(mock.request_history[0].text))

    def test_transfer_network_ownership(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/files/sharing/transfer', status_code=204)
            client.transfer_network_ownership([NETWORK_ID], USER_ID)
            body = json.loads(mock.request_history[0].text)
            self.assertEqual({'networks': [NETWORK_ID],
                              'new_owner': USER_ID}, body)

    def test_list_shared_files(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/files/sharing/list', json=[],
                     headers=JSON_HEADERS)
            self.assertEqual([], client.list_shared_files())

    # ------------------------------------------------------------------
    # batch
    # ------------------------------------------------------------------

    def test_get_network_summaries(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/batch/networks/summary',
                      json=[{'uuid': NETWORK_ID}], headers=JSON_HEADERS)
            res = client.get_network_summaries([NETWORK_ID])
            self.assertEqual(1, len(res))
            self.assertEqual([NETWORK_ID],
                             json.loads(mock.request_history[0].text))
            self.assertIn('format=FULL', mock.request_history[0].url)

    def test_move_networks_to_folder(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/batch/networks/move', status_code=204)
            client.move_networks_to_folder(FOLDER_ID, [NETWORK_ID])
            body = json.loads(mock.request_history[0].text)
            self.assertEqual({'targetFolder': FOLDER_ID,
                              'networks': [NETWORK_ID]}, body)

    def test_move_networks_to_folder_empty_list(self):
        client = self.get_client()
        self.assertRaises(NDExInvalidParameterError,
                          client.move_networks_to_folder, FOLDER_ID, [])

    def test_set_file_visibility(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/batch/files/setvisibility', status_code=204)
            client.set_file_visibility('public', [NETWORK_ID],
                                       default_type='network')
            body = json.loads(mock.request_history[0].text)
            self.assertEqual({'visibility': 'PUBLIC',
                              'files': {NETWORK_ID: 'NETWORK'}}, body)

    def test_set_file_visibility_requires_visibility(self):
        client = self.get_client()
        self.assertRaises(NDExInvalidParameterError,
                          client.set_file_visibility, None, [NETWORK_ID],
                          'network')

    # ------------------------------------------------------------------
    # search
    # ------------------------------------------------------------------

    def test_search_files_defaults(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/search/files',
                      json={'numFound': 0, 'start': 0, 'files': []},
                      headers=JSON_HEADERS)
            res = client.search_files()
            self.assertEqual(0, res['numFound'])
            body = json.loads(mock.request_history[0].text)
            self.assertEqual({'searchString': ''}, body)
            qs = mock.request_history[0].qs
            self.assertEqual(['0'], qs['start'])
            self.assertEqual(['100'], qs['size'])
            self.assertNotIn('visibility', qs)

    def test_search_files_all_filters(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/search/files', json={}, headers=JSON_HEADERS)
            client.search_files(search_string='brca', account_name='bob',
                                permission='write', file_type='folder',
                                visibility='private', start=20, size=10)
            body = json.loads(mock.request_history[0].text)
            self.assertEqual({'searchString': 'brca', 'accountName': 'bob',
                              'permission': 'WRITE', 'type': 'FOLDER'}, body)
            qs = mock.request_history[0].qs
            self.assertEqual(['private'], qs['visibility'])
            self.assertEqual(['20'], qs['start'])
            self.assertEqual(['10'], qs['size'])

    def test_search_files_rejects_unlisted(self):
        client = self.get_client()
        self.assertRaises(NDExInvalidParameterError, client.search_files,
                          '', None, None, None, 'UNLISTED')

    def test_search_files_private_requires_auth(self):
        client = self.get_client(authenticated=False)
        self.assertRaises(NDExUnauthorizedError, client.search_files,
                          '', None, None, None, 'PRIVATE')

    def test_search_files_public_allows_anonymous(self):
        client = self.get_client(authenticated=False)
        with requests_mock.mock() as mock:
            mock.post(V3 + '/search/files', json={}, headers=JSON_HEADERS)
            self.assertEqual({}, client.search_files(visibility='public'))

    # ------------------------------------------------------------------
    # networks
    # ------------------------------------------------------------------

    def test_get_network_summary(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/networks/' + NETWORK_ID + '/summary',
                     json={'uuid': NETWORK_ID, 'folderId': FOLDER_ID},
                     headers=JSON_HEADERS)
            res = client.get_network_summary(NETWORK_ID)
            self.assertEqual(FOLDER_ID, res['folderId'])

    def test_save_new_cx2_network_in_folder(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/networks', status_code=201,
                      json={'uuid': NETWORK_ID}, headers=JSON_HEADERS)
            res = client.save_new_cx2_network_in_folder(
                [{'CXVersion': '2.0'}], visibility='private',
                folder_id=FOLDER_ID)
            self.assertEqual(NETWORK_ID, res)
            url = mock.request_history[0].url
            self.assertIn('visibility=PRIVATE', url)
            self.assertIn('folderId=' + FOLDER_ID, url)

    def test_save_new_cx2_network_in_folder_rejects_non_list(self):
        client = self.get_client()
        self.assertRaises(NDExInvalidParameterError,
                          client.save_new_cx2_network_in_folder,
                          {'CXVersion': '2.0'})

    def test_delete_network(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.delete(V3 + '/networks/' + NETWORK_ID, status_code=204)
            client.delete_network(NETWORK_ID, permanent=True)
            self.assertEqual(['true'],
                             mock.request_history[0].qs['permanent'])

    def test_get_network_aspects(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/networks/' + NETWORK_ID + '/aspects',
                     json=[{'name': 'nodes'}], headers=JSON_HEADERS)
            self.assertEqual(1, len(client.get_network_aspects(NETWORK_ID)))

    def test_export_network_as_tsv(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/networks/' + NETWORK_ID + '/export',
                     text='a\tb\n', headers={'Content-Type': 'text/plain'})
            res = client.export_network_as_tsv(NETWORK_ID, type='edge')
            self.assertEqual('a\tb\n', res.text)
            qs = mock.request_history[0].qs
            self.assertEqual(['edge'], qs['type'])
            self.assertEqual(['true'], qs['header'])

    def test_mint_doi(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/networks/' + NETWORK_ID + '/DOI',
                     text='requested',
                     headers={'Content-Type': 'text/plain'})
            self.assertEqual('requested',
                             client.mint_doi(NETWORK_ID, 'k', 'a@b.com'))

    def test_mint_doi_requires_email(self):
        client = self.get_client()
        self.assertRaises(NDExInvalidParameterError, client.mint_doi,
                          NETWORK_ID, 'k', None)

    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------

    def test_get_user_by_username(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/users', json={'externalId': USER_ID},
                     headers=JSON_HEADERS)
            res = client.get_user_by_username('bob')
            self.assertEqual(USER_ID, res['externalId'])
            self.assertEqual(['bob'], mock.request_history[0].qs['username'])

    def test_get_user_home(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/users/' + USER_ID + '/home',
                     json=[{'uuid': FOLDER_ID, 'type': 'FOLDER'}],
                     headers=JSON_HEADERS)
            res = client.get_user_home(USER_ID)
            self.assertEqual('FOLDER', res[0]['type'])
            self.assertEqual(['update'],
                             mock.request_history[0].qs['format'])

    def test_get_workspaces_for_user(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/users/' + USER_ID + '/workspaces', json=[],
                     headers=JSON_HEADERS)
            self.assertEqual([], client.get_workspaces_for_user(USER_ID))

    def test_signin_sets_bearer_token(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/users/signin', json={'externalId': USER_ID},
                      headers=JSON_HEADERS)
            res = client.signin('tok')
            self.assertEqual(USER_ID, res['externalId'])
            self.assertEqual('tok', client.bearer_token)
            self.assertEqual('Bearer tok', client.s.headers['Authorization'])
            self.assertIsNone(client.s.auth)
            self.assertEqual({'id_token': 'tok'},
                             json.loads(mock.request_history[0].text))

    def test_signin_requires_token(self):
        client = self.get_client()
        self.assertRaises(NDExInvalidParameterError, client.signin, None)

    # ------------------------------------------------------------------
    # workspaces
    # ------------------------------------------------------------------

    def test_create_workspace(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/workspaces', status_code=201,
                      json={'uuid': WORKSPACE_ID}, headers=JSON_HEADERS)
            res = client.create_workspace('ws', options={'a': 1},
                                          network_ids=[NETWORK_ID])
            self.assertEqual(WORKSPACE_ID, res)
            body = json.loads(mock.request_history[0].text)
            self.assertEqual({'name': 'ws', 'options': {'a': 1},
                              'networkIDs': [NETWORK_ID]}, body)

    def test_get_workspace(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/workspaces/' + WORKSPACE_ID,
                     json={'name': 'ws'}, headers=JSON_HEADERS)
            self.assertEqual('ws',
                             client.get_workspace(WORKSPACE_ID)['name'])

    def test_update_workspace_requires_a_field(self):
        client = self.get_client()
        self.assertRaises(NDExInvalidParameterError,
                          client.update_workspace, WORKSPACE_ID)

    def test_rename_workspace(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.put(V3 + '/workspaces/' + WORKSPACE_ID + '/name',
                     status_code=204)
            client.rename_workspace(WORKSPACE_ID, 'new')
            self.assertEqual({'name': 'new'},
                             json.loads(mock.request_history[0].text))

    def test_update_workspace_networks(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.put(V3 + '/workspaces/' + WORKSPACE_ID + '/networkids',
                     status_code=204)
            client.update_workspace_networks(WORKSPACE_ID, [NETWORK_ID])
            self.assertEqual([NETWORK_ID],
                             json.loads(mock.request_history[0].text))

    def test_delete_workspace(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.delete(V3 + '/workspaces/' + WORKSPACE_ID, status_code=204)
            self.assertIsNone(client.delete_workspace(WORKSPACE_ID))

    # ------------------------------------------------------------------
    # removed in v3
    # ------------------------------------------------------------------

    def test_removed_methods_raise(self):
        client = self.get_client()
        cases = [(client.create_networkset, ('n', 'd')),
                 (client.get_networkset, (FOLDER_ID,)),
                 (client.get_network_set, (FOLDER_ID,)),
                 (client.get_networksets_for_user_id, (USER_ID,)),
                 (client.delete_networkset, (FOLDER_ID,)),
                 (client.add_networks_to_networkset,
                  (FOLDER_ID, [NETWORK_ID])),
                 (client.delete_networks_from_networkset,
                  (FOLDER_ID, [NETWORK_ID])),
                 (client.update_network_group_permission,
                  ('g', NETWORK_ID, 'READ')),
                 (client.grant_networks_to_group, ('g', [NETWORK_ID])),
                 (client.search_networks, ()),
                 (client.find_networks, ()),
                 (client.search_networks_by_property_filter, ())]
        for method, args in cases:
            self.assertRaises(NDExUnsupportedCallError, method, *args)

    def test_removed_method_message_names_replacement(self):
        client = self.get_client()
        try:
            client.add_networks_to_networkset(FOLDER_ID, [NETWORK_ID])
            self.fail('Expected NDExUnsupportedCallError')
        except NDExUnsupportedCallError as e:
            self.assertIn('move_networks_to_folder', str(e))

    # ------------------------------------------------------------------
    # constants
    # ------------------------------------------------------------------

    def test_enum_constants(self):
        self.assertEqual({'NETWORK', 'FOLDER', 'SHORTCUT'}, set(FileType.ALL))
        self.assertEqual({'PUBLIC', 'PRIVATE', 'UNLISTED'},
                         set(Visibility.ALL))
        self.assertEqual({'READ', 'WRITE', 'ADMIN', 'MEMBER'},
                         set(Permissions.ALL))


if __name__ == '__main__':
    unittest.main()


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestNdex3InheritedMethods(unittest.TestCase):
    """Covers v2 methods remapped onto v3, and inherited passthroughs."""

    def get_client(self):
        return Ndex3(host=HOST, username='bob', password='secret')

    # --- remapped onto v3 ------------------------------------------------

    def test_make_network_public(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/batch/files/setvisibility', status_code=204)
            client.make_network_public(NETWORK_ID)
            self.assertEqual({'visibility': 'PUBLIC',
                              'files': {NETWORK_ID: 'NETWORK'}},
                             json.loads(mock.request_history[0].text))

    def test_make_network_private(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/batch/files/setvisibility', status_code=204)
            client.make_network_private(NETWORK_ID)
            self.assertEqual('PRIVATE',
                             json.loads(mock.request_history[0].text)
                             ['visibility'])

    def test_update_network_user_permission(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/files/sharing/members', json={},
                      headers=JSON_HEADERS)
            client.update_network_user_permission(USER_ID, NETWORK_ID, 'write')
            self.assertEqual({'files': {NETWORK_ID: 'NETWORK'},
                              'members': {USER_ID: 'WRITE'}},
                             json.loads(mock.request_history[0].text))

    def test_grant_networks_to_user_batches_one_request(self):
        client = self.get_client()
        other = '77777777-7777-7777-7777-777777777777'
        with requests_mock.mock() as mock:
            mock.post(V3 + '/files/sharing/members', json={},
                      headers=JSON_HEADERS)
            client.grant_networks_to_user(USER_ID, [NETWORK_ID, other])
            self.assertEqual(1, len(mock.request_history))
            body = json.loads(mock.request_history[0].text)
            self.assertEqual({NETWORK_ID: 'NETWORK', other: 'NETWORK'},
                             body['files'])
            self.assertEqual({USER_ID: 'READ'}, body['members'])

    def test_grant_network_to_user_by_username(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/users', json={'externalId': USER_ID},
                     headers=JSON_HEADERS)
            mock.post(V3 + '/files/sharing/members', json={},
                      headers=JSON_HEADERS)
            client.grant_network_to_user_by_username('bob', NETWORK_ID,
                                                     'admin')
            body = json.loads(mock.request_history[1].text)
            self.assertEqual({USER_ID: 'ADMIN'}, body['members'])

    def test_grant_network_to_user_by_username_no_external_id(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/users', json={}, headers=JSON_HEADERS)
            self.assertRaises(NDExError,
                              client.grant_network_to_user_by_username,
                              'bob', NETWORK_ID, 'READ')

    # --- v3 network queries ---------------------------------------------

    def test_query_network_as_cx2_stream(self):
        client = self.get_client()
        route = V3 + '/search/networks/' + NETWORK_ID + '/query'
        with requests_mock.mock() as mock:
            mock.post(route, json=[{'CXVersion': '2.0'}],
                      headers=JSON_HEADERS)
            res = client.query_network_as_cx2_stream(
                NETWORK_ID, 'BRCA1', search_depth=2, edge_limit=10)
            self.assertEqual(200, res.status_code)
            body = json.loads(mock.request_history[0].text)
            self.assertEqual({'searchString': 'BRCA1', 'searchDepth': 2,
                              'edgeLimit': 10, 'errorWhenLimitIsOver': True,
                              'directOnly': False}, body)
            qs = mock.request_history[0].qs
            self.assertEqual(['false'], qs['save'])
            self.assertEqual(['false'], qs['preservecoordinates'])

    def test_query_network_as_cx2_stream_optional_fields(self):
        client = self.get_client()
        route = V3 + '/search/networks/' + NETWORK_ID + '/query'
        with requests_mock.mock() as mock:
            mock.post(route, json=[], headers=JSON_HEADERS)
            client.query_network_as_cx2_stream(
                NETWORK_ID, '', node_ids=[1, 2], aspects=['nodes'],
                save=True)
            body = json.loads(mock.request_history[0].text)
            self.assertEqual([1, 2], body['nodeIds'])
            self.assertEqual(['nodes'], body['aspects'])
            self.assertEqual(['true'], mock.request_history[0].qs['save'])

    def test_interconnect_query_as_cx2_stream(self):
        client = self.get_client()
        route = V3 + '/search/networks/' + NETWORK_ID + '/interconnectquery'
        with requests_mock.mock() as mock:
            mock.post(route, json=[], headers=JSON_HEADERS)
            res = client.interconnect_query_as_cx2_stream(NETWORK_ID, 'TP53')
            self.assertEqual(200, res.status_code)
            self.assertEqual('TP53',
                             json.loads(mock.request_history[0].text)
                             ['searchString'])

    def test_get_node_attributes(self):
        client = self.get_client()
        route = V3 + '/search/networks/' + NETWORK_ID + '/nodes'
        with requests_mock.mock() as mock:
            mock.post(route, json=[], headers=JSON_HEADERS)
            client.get_node_attributes(NETWORK_ID, node_ids=[1],
                                       attribute_names=['name'])
            self.assertEqual({'ids': [1], 'attributeNames': ['name']},
                             json.loads(mock.request_history[0].text))

    def test_get_node_attributes_empty_filter(self):
        client = self.get_client()
        route = V3 + '/search/networks/' + NETWORK_ID + '/nodes'
        with requests_mock.mock() as mock:
            mock.post(route, json=[], headers=JSON_HEADERS)
            client.get_node_attributes(NETWORK_ID)
            self.assertEqual({}, json.loads(mock.request_history[0].text))

    # --- inherited passthroughs that must still work ---------------------

    def test_get_id_for_user_uses_v3_user_lookup(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.get(V3 + '/users', json={'externalId': USER_ID},
                     headers=JSON_HEADERS)
            self.assertEqual(USER_ID, client.get_id_for_user('bob'))
            self.assertIn('/v3/users', mock.request_history[0].url)

    def test_save_new_cx2_network_hits_v3(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            loc = V3 + '/networks/' + NETWORK_ID
            mock.post(V3 + '/networks', status_code=201,
                      json={'uuid': NETWORK_ID}, headers={'Location': loc})
            res = client.save_new_cx2_network([{'CXVersion': '2.0'}])
            self.assertIn('/v3/networks', mock.request_history[0].url)
            self.assertEqual(NETWORK_ID, res)

    def test_upload_file_still_raises(self):
        client = self.get_client()
        self.assertRaises(NDExError, client.upload_file, 'foo.cx')

    # --- no v3 equivalent ------------------------------------------------

    def test_methods_without_v3_equivalent_raise(self):
        client = self.get_client()
        cases = [
            (client.get_neighborhood_as_cx_stream, (NETWORK_ID, 'x')),
            (client.get_neighborhood, (NETWORK_ID, 'x')),
            (client.get_interconnectquery_as_cx_stream, (NETWORK_ID, 'x')),
            (client.get_interconnectquery, (NETWORK_ID, 'x')),
            (client.search_network_nodes, (NETWORK_ID,)),
            (client.get_network_as_cx_stream, (NETWORK_ID,)),
            (client.get_network_aspect_as_cx_stream, (NETWORK_ID, 'nodes')),
            (client.save_cx_stream_as_new_network, (b'',)),
            (client.save_new_network, ([],)),
            (client.update_cx_network, (b'', NETWORK_ID)),
            (client.get_provenance, (NETWORK_ID,)),
            (client.set_provenance, (NETWORK_ID, {})),
            (client.get_sample_network, (NETWORK_ID,)),
            (client.set_network_sample, (NETWORK_ID, '')),
            (client.get_task_by_id, ('tid',)),
            (client.set_read_only, (NETWORK_ID, True)),
            (client.set_network_system_properties, (NETWORK_ID, {})),
            (client.set_network_properties, (NETWORK_ID, [])),
            (client.update_network_profile, (NETWORK_ID, {})),
            (client.get_user_by_id, (USER_ID,)),
            (client.get_user_network_summaries, ('bob',)),
            (client.get_network_summaries_for_user, ('bob',)),
            (client.get_network_ids_for_user, ('bob',)),
        ]
        for method, args in cases:
            self.assertRaises(NDExUnsupportedCallError, method, *args)

    def test_no_v3_equivalent_messages_name_replacement(self):
        client = self.get_client()
        expected = {
            client.get_neighborhood_as_cx_stream:
                'query_network_as_cx2_stream',
            client.search_network_nodes: 'get_node_attributes',
            client.get_network_as_cx_stream: 'get_network_as_cx2_stream',
            client.set_network_system_properties: 'set_file_visibility',
            client.get_user_by_id: 'get_user_by_username',
        }
        for method, needle in expected.items():
            try:
                method(NETWORK_ID, 'x')
            except NDExUnsupportedCallError as e:
                self.assertIn(needle, str(e))
            except TypeError:
                try:
                    method(NETWORK_ID)
                except NDExUnsupportedCallError as e:
                    self.assertIn(needle, str(e))


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestNdex3ReturnUrl(unittest.TestCase):
    """All three CX2 save methods return a UUID unless asked for a URL."""

    def get_client(self):
        return Ndex3(host=HOST, username='bob', password='secret')

    def test_all_three_default_to_uuid(self):
        client = self.get_client()
        loc = V3 + '/networks/' + NETWORK_ID
        for call in (lambda c: c.save_new_cx2_network([{'CXVersion': '2.0'}]),
                     lambda c: c.save_new_cx2_network_in_folder(
                         [{'CXVersion': '2.0'}]),
                     lambda c: c.save_cx2_stream_as_new_network(
                         io.BytesIO(b'[]'))):
            with requests_mock.mock() as mock:
                mock.post(V3 + '/networks', status_code=201,
                          json={'uuid': NETWORK_ID},
                          headers={'Location': loc})
                self.assertEqual(NETWORK_ID, call(client))

    def test_all_three_can_return_url(self):
        client = self.get_client()
        loc = V3 + '/networks/' + NETWORK_ID
        calls = (lambda c: c.save_new_cx2_network(
                     [{'CXVersion': '2.0'}], return_url=True),
                 lambda c: c.save_new_cx2_network_in_folder(
                     [{'CXVersion': '2.0'}], return_url=True),
                 lambda c: c.save_cx2_stream_as_new_network(
                     io.BytesIO(b'[]'), return_url=True))
        for call in calls:
            with requests_mock.mock() as mock:
                mock.post(V3 + '/networks', status_code=201,
                          json={'uuid': NETWORK_ID},
                          headers={'Location': loc})
                self.assertEqual(loc, call(client))

    def test_url_synthesized_when_location_absent(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/networks', status_code=201,
                      json={'uuid': NETWORK_ID})
            self.assertEqual(V3 + '/networks/' + NETWORK_ID,
                             client.save_new_cx2_network_in_folder(
                                 [{'CXVersion': '2.0'}], return_url=True))

    def test_uuid_from_url_helper(self):
        self.assertEqual(NETWORK_ID,
                         Ndex3._uuid_from_url(V3 + '/networks/' + NETWORK_ID))
        self.assertEqual(NETWORK_ID,
                         Ndex3._uuid_from_url(V3 + '/networks/' +
                                              NETWORK_ID + '/'))

    def test_folder_id_still_passed_with_return_url(self):
        client = self.get_client()
        with requests_mock.mock() as mock:
            mock.post(V3 + '/networks', status_code=201,
                      json={'uuid': NETWORK_ID})
            client.save_new_cx2_network_in_folder(
                [{'CXVersion': '2.0'}], folder_id=FOLDER_ID,
                return_url=True)
            self.assertIn('folderId=' + FOLDER_ID,
                          mock.request_history[0].url)

    def test_ndex2_behaviour_is_unchanged(self):
        """The URL-returning contract on Ndex2 must not be altered."""
        from ndex2.client import Ndex2
        legacy = Ndex2(host=HOST, username='bob', password='secret',
                       skip_version_check=True)
        loc = HOST + '/v3/networks/' + NETWORK_ID
        with requests_mock.mock() as mock:
            mock.post(HOST + '/v3/networks', status_code=201,
                      headers={'Location': loc})
            self.assertEqual(loc,
                             legacy.save_new_cx2_network([{'a': 1}]))
