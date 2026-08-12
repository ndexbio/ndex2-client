#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ndex2.api.networks`."""

import os
import json
import unittest

import requests_mock

from ndex2.client import Ndex2
from ndex2.exceptions import NDExInvalidParameterError
from ndex2.exceptions import NDExNotFoundError
from ndex2.exceptions import NDExUnauthorizedError

SKIP_REASON = 'NDEX2_TEST_SERVER environment variable detected, ' \
              'skipping for integration tests'

HOST = 'http://foo.com'
V3 = HOST + '/v3'
NETWORK_ID = '22222222-2222-2222-2222-222222222222'
OTHER_ID = '55555555-5555-5555-5555-555555555555'
FOLDER_ID = '11111111-1111-1111-1111-111111111111'
USER_ID = '44444444-4444-4444-4444-444444444444'
JSON_HEADERS = {'Content-Type': 'application/json'}


def client(authenticated=True):
    if authenticated:
        return Ndex2(host=HOST, username='bob', password='secret',
                     skip_version_check=True)
    return Ndex2(host=HOST, skip_version_check=True)


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestNetworksAPIWiring(unittest.TestCase):

    def test_namespace_shares_transport(self):
        c = client()
        self.assertIs(c._http, c.networks._http)
        self.assertIs(c.files._http, c.networks._http)

    def test_all_11_methods_present(self):
        methods = [m for m in dir(client().networks)
                   if not m.startswith('_')]
        self.assertEqual(11, len(methods))

    def test_creation_deliberately_absent(self):
        """Creation stays on the flat methods, which accept folder_id."""
        ns = client().networks
        for absent in ('create', 'save_new_cx2_network',
                       'create_from_stream'):
            self.assertFalse(hasattr(ns, absent))


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestSummariesAndAspects(unittest.TestCase):

    def test_get_summary(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/networks/' + NETWORK_ID + '/summary',
                  json={'uuid': NETWORK_ID, 'folderId': FOLDER_ID},
                  headers=JSON_HEADERS)
            res = c.networks.get_summary(NETWORK_ID)
            self.assertEqual(FOLDER_ID, res['folderId'])
            self.assertIn('format=FULL', m.request_history[0].url)

    def test_get_summary_access_key(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/networks/' + NETWORK_ID + '/summary', json={},
                  headers=JSON_HEADERS)
            c.networks.get_summary(NETWORK_ID, access_key='abc')
            self.assertEqual(['abc'], m.request_history[0].qs['accesskey'])

    def test_get_summary_invalid_id(self):
        for bad in (None, '  ', 7):
            self.assertRaises(NDExInvalidParameterError,
                              client().networks.get_summary, bad)

    def test_get_summary_not_found(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/networks/' + NETWORK_ID + '/summary',
                  status_code=404, text='nope')
            self.assertRaises(NDExNotFoundError, c.networks.get_summary,
                              NETWORK_ID)

    def test_get_summaries(self):
        c = client()
        with requests_mock.mock() as m:
            m.post(V3 + '/batch/networks/summary',
                   json=[{'uuid': NETWORK_ID}], headers=JSON_HEADERS)
            res = c.networks.get_summaries([NETWORK_ID, OTHER_ID])
            self.assertEqual(1, len(res))
            self.assertEqual([NETWORK_ID, OTHER_ID],
                             json.loads(m.request_history[0].text))

    def test_get_summaries_accepts_single_id(self):
        c = client()
        with requests_mock.mock() as m:
            m.post(V3 + '/batch/networks/summary', json=[],
                   headers=JSON_HEADERS)
            c.networks.get_summaries(NETWORK_ID)
            self.assertEqual([NETWORK_ID],
                             json.loads(m.request_history[0].text))

    def test_get_summaries_rejects_empty(self):
        self.assertRaises(NDExInvalidParameterError,
                          client().networks.get_summaries, [])

    def test_get_summaries_empty_body_returns_list(self):
        c = client()
        with requests_mock.mock() as m:
            m.post(V3 + '/batch/networks/summary', status_code=204)
            self.assertEqual([], c.networks.get_summaries([NETWORK_ID]))

    def test_list_aspects(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/networks/' + NETWORK_ID + '/aspects',
                  json=[{'name': 'nodes'}], headers=JSON_HEADERS)
            self.assertEqual(1, len(c.networks.list_aspects(NETWORK_ID)))

    def test_list_aspects_empty_body_returns_list(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/networks/' + NETWORK_ID + '/aspects',
                  status_code=204)
            self.assertEqual([], c.networks.list_aspects(NETWORK_ID))


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestLifecycle(unittest.TestCase):

    def test_delete_soft_by_default(self):
        c = client()
        with requests_mock.mock() as m:
            m.delete(V3 + '/networks/' + NETWORK_ID, status_code=204)
            c.networks.delete(NETWORK_ID)
            self.assertEqual(['false'],
                             m.request_history[0].qs['permanent'])

    def test_delete_permanent(self):
        c = client()
        with requests_mock.mock() as m:
            m.delete(V3 + '/networks/' + NETWORK_ID, status_code=204)
            c.networks.delete(NETWORK_ID, permanent=True)
            self.assertEqual(['true'], m.request_history[0].qs['permanent'])

    def test_delete_requires_auth(self):
        self.assertRaises(NDExUnauthorizedError,
                          client(authenticated=False).networks.delete,
                          NETWORK_ID)

    def test_move_to_folder(self):
        c = client()
        with requests_mock.mock() as m:
            m.post(V3 + '/batch/networks/move', status_code=204)
            c.networks.move_to_folder(FOLDER_ID, [NETWORK_ID, OTHER_ID])
            self.assertEqual({'targetFolder': FOLDER_ID,
                              'networks': [NETWORK_ID, OTHER_ID]},
                             json.loads(m.request_history[0].text))

    def test_move_to_folder_rejects_empty(self):
        self.assertRaises(NDExInvalidParameterError,
                          client().networks.move_to_folder, FOLDER_ID, [])

    def test_transfer_ownership(self):
        c = client()
        with requests_mock.mock() as m:
            m.post(V3 + '/files/sharing/transfer', status_code=204)
            c.networks.transfer_ownership([NETWORK_ID], USER_ID)
            self.assertEqual({'networks': [NETWORK_ID],
                              'new_owner': USER_ID},
                             json.loads(m.request_history[0].text))

    def test_transfer_ownership_requires_owner(self):
        self.assertRaises(NDExInvalidParameterError,
                          client().networks.transfer_ownership,
                          [NETWORK_ID], None)


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestExportAndDoi(unittest.TestCase):

    def test_export_as_tsv(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/networks/' + NETWORK_ID + '/export',
                  text='a\tb\n', headers={'Content-Type': 'text/plain'})
            res = c.networks.export_as_tsv(NETWORK_ID, type='edge')
            self.assertEqual('a\tb\n', res.text)
            qs = m.request_history[0].qs
            self.assertEqual(['edge'], qs['type'])
            self.assertEqual(['true'], qs['header'])
            self.assertEqual(['id'], qs['nodekey'])

    def test_export_as_tsv_no_header(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/networks/' + NETWORK_ID + '/export', text='')
            c.networks.export_as_tsv(NETWORK_ID, include_header=False)
            self.assertEqual(['false'], m.request_history[0].qs['header'])

    def test_mint_doi(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(V3 + '/networks/' + NETWORK_ID + '/DOI',
                  text='requested',
                  headers={'Content-Type': 'text/plain'})
            self.assertEqual('requested',
                             c.networks.mint_doi(NETWORK_ID, 'k', 'a@b.com'))
            qs = m.request_history[0].qs
            self.assertEqual(['k'], qs['key'])

    def test_mint_doi_requires_all_args(self):
        c = client()
        self.assertRaises(NDExInvalidParameterError, c.networks.mint_doi,
                          NETWORK_ID, 'k', None)
        self.assertRaises(NDExInvalidParameterError, c.networks.mint_doi,
                          NETWORK_ID, None, 'a@b.com')


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestQueries(unittest.TestCase):

    def test_query_targets_plural_v3_route(self):
        """v2 used /search/network/{id}/query; v3 renamed it to networks."""
        c = client()
        route = V3 + '/search/networks/' + NETWORK_ID + '/query'
        with requests_mock.mock() as m:
            m.post(route, json=[{'CXVersion': '2.0'}],
                   headers=JSON_HEADERS)
            res = c.networks.query(NETWORK_ID, 'BRCA1', search_depth=2,
                                   edge_limit=10)
            self.assertEqual(200, res.status_code)
            self.assertIn('/v3/search/networks/', m.request_history[0].url)
            self.assertEqual({'searchString': 'BRCA1', 'searchDepth': 2,
                              'edgeLimit': 10, 'errorWhenLimitIsOver': True,
                              'directOnly': False},
                             json.loads(m.request_history[0].text))

    def test_query_default_params(self):
        c = client()
        route = V3 + '/search/networks/' + NETWORK_ID + '/query'
        with requests_mock.mock() as m:
            m.post(route, json=[], headers=JSON_HEADERS)
            c.networks.query(NETWORK_ID, 'x')
            qs = m.request_history[0].qs
            self.assertEqual(['false'], qs['save'])
            self.assertEqual(['false'], qs['preservecoordinates'])
            body = json.loads(m.request_history[0].text)
            self.assertEqual(1, body['searchDepth'])
            self.assertEqual(2500, body['edgeLimit'])

    def test_query_optional_fields(self):
        c = client()
        route = V3 + '/search/networks/' + NETWORK_ID + '/query'
        with requests_mock.mock() as m:
            m.post(route, json=[], headers=JSON_HEADERS)
            c.networks.query(NETWORK_ID, '', node_ids=[1, 2],
                             aspects=['nodes'], save=True,
                             preserve_coordinates=True)
            body = json.loads(m.request_history[0].text)
            self.assertEqual([1, 2], body['nodeIds'])
            self.assertEqual(['nodes'], body['aspects'])
            qs = m.request_history[0].qs
            self.assertEqual(['true'], qs['save'])
            self.assertEqual(['true'], qs['preservecoordinates'])

    def test_query_omits_optional_fields_when_unset(self):
        c = client()
        route = V3 + '/search/networks/' + NETWORK_ID + '/query'
        with requests_mock.mock() as m:
            m.post(route, json=[], headers=JSON_HEADERS)
            c.networks.query(NETWORK_ID, 'x')
            body = json.loads(m.request_history[0].text)
            self.assertNotIn('nodeIds', body)
            self.assertNotIn('aspects', body)

    def test_interconnect_query(self):
        c = client()
        route = V3 + '/search/networks/' + NETWORK_ID + '/interconnectquery'
        with requests_mock.mock() as m:
            m.post(route, json=[], headers=JSON_HEADERS)
            res = c.networks.interconnect_query(NETWORK_ID, 'TP53')
            self.assertEqual(200, res.status_code)
            self.assertEqual('TP53',
                             json.loads(m.request_history[0].text)
                             ['searchString'])

    def test_query_and_interconnect_use_different_routes(self):
        c = client()
        base = V3 + '/search/networks/' + NETWORK_ID
        with requests_mock.mock() as m:
            m.post(base + '/query', json=[], headers=JSON_HEADERS)
            m.post(base + '/interconnectquery', json=[],
                   headers=JSON_HEADERS)
            c.networks.query(NETWORK_ID, 'x')
            c.networks.interconnect_query(NETWORK_ID, 'x')
            self.assertIn('/query?', m.request_history[0].url)
            self.assertNotIn('/interconnectquery', m.request_history[0].url)
            self.assertIn('/interconnectquery?', m.request_history[1].url)

    def test_query_invalid_network_id(self):
        self.assertRaises(NDExInvalidParameterError,
                          client().networks.query, None, 'x')

    def test_get_node_attributes(self):
        c = client()
        route = V3 + '/search/networks/' + NETWORK_ID + '/nodes'
        with requests_mock.mock() as m:
            m.post(route, json=[], headers=JSON_HEADERS)
            c.networks.get_node_attributes(NETWORK_ID, node_ids=[1],
                                           attribute_names=['name'])
            self.assertEqual({'ids': [1], 'attributeNames': ['name']},
                             json.loads(m.request_history[0].text))

    def test_get_node_attributes_empty_filter(self):
        c = client()
        route = V3 + '/search/networks/' + NETWORK_ID + '/nodes'
        with requests_mock.mock() as m:
            m.post(route, json=[], headers=JSON_HEADERS)
            c.networks.get_node_attributes(NETWORK_ID)
            self.assertEqual({}, json.loads(m.request_history[0].text))


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestFlatMethodsStillTargetV2(unittest.TestCase):
    """The overlapping flat methods must keep hitting the v2 routes."""

    def test_flat_neighborhood_uses_singular_v2_route(self):
        c = client()
        with requests_mock.mock() as m:
            m.post(HOST + '/v2/search/network/' + NETWORK_ID + '/query',
                   json={}, headers=JSON_HEADERS)
            c.get_neighborhood_as_cx_stream(NETWORK_ID, 'x')
            url = m.request_history[0].url
            self.assertIn('/v2/search/network/', url)
            self.assertNotIn('/search/networks/', url)

    def test_flat_get_network_summary_uses_v2(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(HOST + '/v2/network/' + NETWORK_ID + '/summary',
                  json={'externalId': NETWORK_ID}, headers=JSON_HEADERS)
            c.get_network_summary(NETWORK_ID)
            self.assertIn('/v2/network/', m.request_history[0].url)


if __name__ == '__main__':
    unittest.main()


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestNoneIdentifiersRejected(unittest.TestCase):
    """A None identifier must be rejected, not stringified to 'None'."""

    def test_move_to_folder_none_folder(self):
        self.assertRaises(NDExInvalidParameterError,
                          client().networks.move_to_folder, None,
                          [NETWORK_ID])

    def test_transfer_ownership_none_owner(self):
        self.assertRaises(NDExInvalidParameterError,
                          client().networks.transfer_ownership,
                          [NETWORK_ID], None)
