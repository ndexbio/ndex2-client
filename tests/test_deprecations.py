#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for the network set and group deprecation warnings.

These methods remain fully supported. On the server a network set is stored
as a folder, and a group as a folder several users hold permissions on, so
the v2 endpoints continue to work. The warnings steer new code towards the
namespaces without breaking existing code.

The important check here is not that a warning fires but that the method it
names actually exists. A warning pointing at a method that was renamed or
removed is worse than no warning: it sends the reader somewhere that does
not exist, and nothing else in the test suite would notice.
"""

import os
import re
import unittest
import warnings

import requests_mock

from ndex2.client import Ndex2

SKIP_REASON = 'NDEX2_TEST_SERVER environment variable detected, ' \
              'skipping for integration tests'

HOST = 'http://foo.com'
SET_ID = '99999999-9999-9999-9999-999999999999'
NETWORK_ID = '22222222-2222-2222-2222-222222222222'
USER_ID = '44444444-4444-4444-4444-444444444444'
TEXT_HEADERS = {'Content-Type': 'text/plain'}
JSON_HEADERS = {'Content-Type': 'application/json'}


def client():
    return Ndex2(host=HOST, username='bob', password='secret',
                 skip_version_check=True)


def warns(fn):
    """
    Runs *fn* and returns the DeprecationWarning messages it raised.

    :param fn: Zero argument callable
    :return: Warning messages
    :rtype: list
    """
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        try:
            fn()
        except Exception:
            pass
    return [str(w.message) for w in caught
            if w.category is DeprecationWarning]


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestDeprecationWarningsFire(unittest.TestCase):

    def calls(self, c, m):
        """Registers permissive mocks and returns the calls to exercise."""
        m.register_uri(requests_mock.ANY, requests_mock.ANY, text='',
                       status_code=200)
        return {
            'create_networkset':
                lambda: c.create_networkset('n', 'd'),
            'get_networkset':
                lambda: c.get_networkset(SET_ID),
            'get_network_set':
                lambda: c.get_network_set(SET_ID),
            'get_networksets_for_user_id':
                lambda: c.get_networksets_for_user_id(USER_ID),
            'delete_networkset':
                lambda: c.delete_networkset(SET_ID),
            'add_networks_to_networkset':
                lambda: c.add_networks_to_networkset(SET_ID, [NETWORK_ID]),
            'delete_networks_from_networkset':
                lambda: c.delete_networks_from_networkset(SET_ID,
                                                          [NETWORK_ID]),
            'update_network_group_permission':
                lambda: c.update_network_group_permission('g', NETWORK_ID,
                                                          'READ'),
            'grant_networks_to_group':
                lambda: c.grant_networks_to_group('g', [NETWORK_ID]),
        }

    def test_every_networkset_and_group_method_warns(self):
        c = client()
        with requests_mock.mock() as m:
            for name, call in self.calls(c, m).items():
                self.assertTrue(warns(call),
                                '%s did not emit a DeprecationWarning' % name)

    def test_include_groups_parameter_warns(self):
        c = client()
        with requests_mock.mock() as m:
            m.post(HOST + '/v2/search/network', text='', status_code=200)
            self.assertTrue(warns(lambda: c.search_networks(
                'x', include_groups=True)))

    def test_search_networks_is_silent_without_include_groups(self):
        """Only the group path is deprecated, not the whole method."""
        c = client()
        with requests_mock.mock() as m:
            m.post(HOST + '/v2/search/network', text='', status_code=200)
            self.assertEqual([], warns(lambda: c.search_networks('x')))

    def test_non_deprecated_methods_are_silent(self):
        c = client()
        with requests_mock.mock() as m:
            m.get(HOST + '/v2/network/' + NETWORK_ID + '/summary', json={},
                  headers=JSON_HEADERS)
            m.get(HOST + '/v2/user', json={'externalId': USER_ID},
                  headers=JSON_HEADERS)
            self.assertEqual([], warns(
                lambda: c.get_network_summary(NETWORK_ID)))
            self.assertEqual([], warns(
                lambda: c.get_user_by_username('bob')))


@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestReplacementsActuallyExist(unittest.TestCase):
    """Every method named in a warning must be reachable on the client.

    This is what guards against a warning that points at a class or method
    which has since been renamed or deleted.
    """

    def collect_messages(self):
        c = client()
        messages = []
        with requests_mock.mock() as m:
            m.register_uri(requests_mock.ANY, requests_mock.ANY, text='',
                           status_code=200)
            for call in (
                    lambda: c.create_networkset('n', 'd'),
                    lambda: c.get_networkset(SET_ID),
                    lambda: c.get_networksets_for_user_id(USER_ID),
                    lambda: c.delete_networkset(SET_ID),
                    lambda: c.add_networks_to_networkset(SET_ID,
                                                         [NETWORK_ID]),
                    lambda: c.delete_networks_from_networkset(SET_ID,
                                                              [NETWORK_ID]),
                    lambda: c.update_network_group_permission('g',
                                                              NETWORK_ID,
                                                              'READ'),
                    lambda: c.grant_networks_to_group('g', [NETWORK_ID]),
                    lambda: c.search_networks('x', include_groups=True)):
                messages.extend(warns(call))
        return messages

    def test_messages_were_collected(self):
        self.assertGreaterEqual(len(self.collect_messages()), 9)

    def test_every_named_replacement_resolves(self):
        c = client()
        unresolved = []
        for message in self.collect_messages():
            for ref in re.findall(r'client\.(\w+)\.(\w+)\(\)', message):
                namespace, method = ref
                target = getattr(c, namespace, None)
                if target is None or not hasattr(target, method):
                    unresolved.append('client.%s.%s()' % ref)
        self.assertEqual([], sorted(set(unresolved)),
                         'warnings name methods that do not exist')

    def test_no_message_references_a_removed_class(self):
        """The v3 work briefly shipped as a separate Ndex3 class. Nothing
        should still point at it, or at any dotted module path."""
        for message in self.collect_messages():
            self.assertNotIn('Ndex3', message)
            self.assertNotIn('client_v3', message)



@unittest.skipIf(os.getenv('NDEX2_TEST_SERVER') is not None, SKIP_REASON)
class TestDeprecationDirectivesInDocstrings(unittest.TestCase):
    """The runtime warning is invisible while reading code, so the
    docstring carries the notice too. These methods are all published, so
    the directive reaches the Sphinx reference."""

    DEPRECATED = ('create_networkset', 'get_networkset',
                  'get_networksets_for_user_id', 'delete_networkset',
                  'add_networks_to_networkset',
                  'delete_networks_from_networkset',
                  'update_network_group_permission',
                  'grant_networks_to_group')

    def test_each_has_a_deprecated_directive(self):
        import inspect
        for name in self.DEPRECATED:
            doc = inspect.getdoc(getattr(Ndex2, name)) or ''
            self.assertIn('.. deprecated::', doc,
                          '%s docstring has no deprecated directive' % name)

    def test_directive_carries_a_version(self):
        """Omitting the version makes Sphinx consume the first words of the
        message as the version number."""
        import inspect
        for name in self.DEPRECATED:
            doc = inspect.getdoc(getattr(Ndex2, name)) or ''
            self.assertTrue(re.search(r'\.\. deprecated:: \d+\.\d+\.\d+',
                                      doc),
                            '%s directive has no version' % name)

    def test_directive_names_a_namespace_method(self):
        import inspect
        for name in self.DEPRECATED:
            doc = inspect.getdoc(getattr(Ndex2, name)) or ''
            section = doc.split('.. deprecated::', 1)[1]
            self.assertTrue(re.search(r'client\.\w+\.\w+\(\)', section),
                            '%s directive names no replacement' % name)


if __name__ == '__main__':
    unittest.main()
