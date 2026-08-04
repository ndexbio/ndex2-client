# -*- coding: utf-8 -*-

"""
Shared setup for the v3 namespace integration tests.

Not named ``test_*`` so pytest does not collect it.

Every object created by these tests is named with a unique run tag and
recorded for teardown, so a failure part way through does not leave
material behind on the server.
"""

import os
import unittest
import uuid

from ndex2.client import Ndex2
from ndex2.cx2 import CX2Network

SKIP_REASON = 'NDEX2_TEST_SERVER, NDEX2_TEST_USER, NDEX2_TEST_PASS ' \
              'environment variables not set, cannot run integration' \
              ' tests with server'


def creds_present():
    """
    Whether all three credential environment variables are set.

    :return: ``True`` if integration tests can run
    :rtype: bool
    """
    return all(os.getenv(v) is not None
               for v in ('NDEX2_TEST_SERVER', 'NDEX2_TEST_USER',
                         'NDEX2_TEST_PASS'))


@unittest.skipUnless(creds_present(), SKIP_REASON)
class V3IntegrationBase(unittest.TestCase):
    """
    Base class providing a client, a unique run tag and teardown.
    """

    def setUp(self):
        self.server = os.getenv('NDEX2_TEST_SERVER')
        self.user = os.getenv('NDEX2_TEST_USER')
        self.password = os.getenv('NDEX2_TEST_PASS')
        self.client = Ndex2(self.server, self.user, self.password,
                            skip_version_check=True,
                            user_agent='ndex2-client integration test')
        self.anon = Ndex2(self.server, skip_version_check=True)
        self.tag = 'zz-itest-' + uuid.uuid4().hex[:12]
        self._folders = []
        self._shortcuts = []
        self._networks = []

    def tearDown(self):
        """
        Removes everything the test created, best effort so that one
        failure does not strand the rest.
        """
        for sid in self._shortcuts:
            self._quiet(self.client.files.delete_shortcut, sid)
        for nid in self._networks:
            self._quiet(self.client.networks.delete, nid, permanent=True)
        for fid in reversed(self._folders):
            self._quiet(self.client.files.delete_folder, fid,
                        force=True, permanent=True)

    @staticmethod
    def _quiet(fn, *args, **kwargs):
        try:
            fn(*args, **kwargs)
        except Exception:
            pass

    # ------------------------------------------------------------------

    def name(self, suffix=''):
        """
        Builds a unique object name for this run.

        :param suffix: Appended to the run tag
        :type suffix: str
        :return: Unique name
        :rtype: str
        """
        return self.tag + (' ' + suffix if suffix else '')

    def new_folder(self, suffix='folder', parent=None):
        """
        Creates a folder and registers it for teardown.

        :param suffix: Appended to the run tag to build the name
        :type suffix: str
        :param parent: UUID of the parent folder
        :type parent: str
        :return: UUID of the new folder
        :rtype: str
        """
        fid = self.client.files.create_folder(
            self.name(suffix), parent=parent)
        self._folders.append(fid)
        return fid

    def new_network(self, suffix='network', folder_id=None):
        """
        Creates a small CX2 network and registers it for teardown.

        :param suffix: Appended to the run tag to build the name
        :type suffix: str
        :param folder_id: UUID of the folder to create it in
        :type folder_id: str
        :return: UUID of the new network
        :rtype: str
        """
        net = CX2Network()
        net.set_network_attributes({
            'name': self.name(suffix),
            'description': 'ndex2-client integration test, safe to delete'})
        a = net.add_node(attributes={'name': 'ALPHA'})
        b = net.add_node(attributes={'name': 'BETA'})
        net.add_edge(source=a, target=b, attributes={'interaction': 'binds'})
        url = self.client.save_new_cx2_network(
            net.to_cx2(), folder_id=folder_id)
        nid = str(url).rstrip('/').split('/')[-1]
        self._networks.append(nid)
        return nid

    def user_id(self):
        """
        :return: UUID of the authenticated user
        :rtype: str
        """
        return self.client.users.get(self.user)['externalId']
