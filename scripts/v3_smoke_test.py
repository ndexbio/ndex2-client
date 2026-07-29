#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
End-to-end smoke test for the v3 API namespaces on
:py:class:`ndex2.client.Ndex2`.

Exercises folders, shortcuts, network placement, sharing, access keys,
search, queries and trash against a live NDEx server. Nothing here is
mocked.

Every object is named with a timestamped run tag so it is obvious in the
web UI which run created it. By default the script pauses before cleanup
so the result can be inspected.

Usage::

    export NDEX_USER=your_account
    export NDEX_PASS=your_password
    python scripts/v3_smoke_test.py --host https://dev3.ndex.ucsd.edu/rest

    # leave everything behind for GUI inspection, no prompt
    python scripts/v3_smoke_test.py --keep

    # unattended
    python scripts/v3_smoke_test.py --cleanup

    # also verify a real bearer token authenticates the flat v2 methods
    python scripts/v3_smoke_test.py --id-token "$ID_TOKEN"

Exits non-zero if any check fails.
"""

import argparse
import datetime
import json
import os
import sys
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..'))

import requests                                     # noqa: E402

from ndex2.client import Ndex2                      # noqa: E402
from ndex2.constants import FileType                # noqa: E402
from ndex2.constants import Permissions             # noqa: E402
from ndex2.constants import Visibility              # noqa: E402
from ndex2.cx2 import CX2Network                    # noqa: E402
from ndex2.exceptions import NDExError              # noqa: E402
from ndex2.exceptions import NDExInvalidParameterError  # noqa: E402
from ndex2.exceptions import NDExUnauthorizedError  # noqa: E402

DEFAULT_HOST = 'https://dev3.ndex.ucsd.edu/rest'

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
GREY = '\033[90m'
BOLD = '\033[1m'
OFF = '\033[0m'


class Runner(object):
    """
    Tracks step results and the objects needing cleanup.
    """

    def __init__(self, verbose=False, color=True):
        self.verbose = verbose
        self.color = color
        self.passed = 0
        self.failed = []
        self.skipped = []
        self.networks = []
        self.shortcuts = []
        self.folders = []

    def _c(self, code, text):
        return text if not self.color else code + text + OFF

    def step(self, name, fn, required=True):
        """
        Runs one check.

        :param name: Human readable description
        :type name: str
        :param fn: Zero argument callable performing the check
        :param required: If ``False`` a failure is reported as a warning
                         and does not fail the run
        :type required: bool
        :return: Whatever *fn* returned, or ``None`` on failure
        """
        try:
            result = fn()
        except Exception as e:
            label, code = ('FAIL', RED) if required else ('WARN', YELLOW)
            print('  %s %s' % (self._c(code, '[' + label + ']'), name))
            print('         %s: %s' % (type(e).__name__, e))
            if self.verbose:
                traceback.print_exc()
            (self.failed if required else self.skipped).append(name)
            return None
        detail = ''
        if isinstance(result, str) and len(result) < 60:
            detail = self._c(GREY, '  ' + result)
        print('  %s %s%s' % (self._c(GREEN, '[ OK ]'), name, detail))
        self.passed += 1
        return result

    def section(self, title):
        print('\n%s' % self._c(BOLD, title))

    def summary(self):
        print('\n' + '=' * 62)
        print('%d passed, %d failed, %d skipped'
              % (self.passed, len(self.failed), len(self.skipped)))
        for name in self.failed:
            print('  %s %s' % (self._c(RED, 'FAILED:'), name))
        for name in self.skipped:
            print('  %s %s' % (self._c(YELLOW, 'SKIPPED:'), name))
        return len(self.failed) == 0


def build_network(name):
    """
    Builds a small but valid CX2 network.

    :param name: Network name
    :type name: str
    :return: CX2 network as a list of aspects
    :rtype: list
    """
    net = CX2Network()
    net.set_network_attributes({
        'name': name,
        'description': 'Created by v3_smoke_test.py; safe to delete.'})
    a = net.add_node(attributes={'name': 'ALPHA'})
    b = net.add_node(attributes={'name': 'BETA'})
    c = net.add_node(attributes={'name': 'GAMMA'})
    net.add_edge(source=a, target=b, attributes={'interaction': 'binds'})
    net.add_edge(source=b, target=c, attributes={'interaction': 'activates'})
    return net.to_cx2()


def uuid_of(url):
    """
    Extracts the trailing UUID from a network URL.

    The flat creation methods return the full URL of the new network.

    :param url: URL whose last path segment is a UUID
    :type url: str
    :return: The UUID
    :rtype: str
    """
    return str(url).rstrip('/').split('/')[-1]


def parse_args():
    p = argparse.ArgumentParser(
        description='End-to-end smoke test for the v3 API namespaces.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('--host', default=os.getenv('NDEX_HOST', DEFAULT_HOST),
                   help='REST base URL, including any servlet context path')
    p.add_argument('--web-host', default=os.getenv('NDEX_WEB_HOST'),
                   help='Base URL of the web UI, for printing links. '
                        'Defaults to --host with a trailing /rest removed.')
    p.add_argument('--username', default=os.getenv('NDEX_USER'))
    p.add_argument('--password', default=os.getenv('NDEX_PASS'))
    p.add_argument('--id-token', default=os.getenv('NDEX_ID_TOKEN'),
                   help='OAuth/Keycloak id token. If given, sign-in is '
                        'tested against the live server.')
    p.add_argument('--share-with-user',
                   help='UUID of a second user, to test member sharing')
    group = p.add_mutually_exclusive_group()
    group.add_argument('--keep', action='store_true',
                       help='Leave created objects behind, no prompt')
    group.add_argument('--cleanup', action='store_true',
                       help='Delete created objects without prompting')
    p.add_argument('--no-color', action='store_true')
    p.add_argument('-v', '--verbose', action='store_true')
    return p.parse_args()


def main():
    args = parse_args()
    if not args.username or not args.password:
        sys.stderr.write('ERROR: set NDEX_USER and NDEX_PASS, or pass '
                         '--username/--password\n')
        return 2

    web_host = args.web_host
    if web_host is None:
        web_host = args.host.rstrip('/')
        if web_host.endswith('/rest'):
            web_host = web_host[:-len('/rest')]

    tag = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    prefix = 'zz-v3-smoke ' + tag

    r = Runner(verbose=args.verbose, color=not args.no_color)
    print('%s\nhost      %s\nweb       %s\nuser      %s\nrun tag   %s\n%s'
          % ('=' * 62, args.host, web_host, args.username, tag, '=' * 62))

    client = Ndex2(host=args.host, username=args.username,
                   password=args.password, skip_version_check=True)
    anon = Ndex2(host=args.host, skip_version_check=True)

    # ------------------------------------------------------------------
    r.section('Connectivity')
    # ------------------------------------------------------------------

    def check_status():
        status = client.admin.status()
        if not isinstance(status, dict):
            raise NDExError('status was not a JSON object')
        return str(status.get('message', ''))[:40]

    r.step('client.admin.status()', check_status)

    user = r.step('client.users.get()',
                  lambda: client.users.get(args.username))
    user_id = user.get('externalId') if isinstance(user, dict) else None
    if user_id is None:
        print('\nCannot continue without a user id.')
        r.summary()
        return 1
    print('         user id %s' % user_id)

    r.step('client.users.home()',
           lambda: '%d item(s) at root' % len(client.users.home(user_id)))
    r.step('client.files.count()',
           lambda: json.dumps(client.files.count()))

    # ------------------------------------------------------------------
    r.section('Folders')
    # ------------------------------------------------------------------

    parent = r.step(
        'create parent folder',
        lambda: client.files.create_folder(
            prefix, description='v3 namespace smoke test, safe to delete'))
    if parent is None:
        print('\nCannot continue without a folder.')
        r.summary()
        return 1
    r.folders.append(parent)

    child = r.step('create nested subfolder',
                   lambda: client.files.create_folder(prefix + ' / sub',
                                                      parent=parent))
    if child is not None:
        r.folders.append(child)

        def check_parentage():
            actual = str(client.files.get_folder(child).get('parent'))
            if actual != str(parent):
                raise NDExError('parent is %s, expected %s'
                                % (actual, parent))
            return 'parent link correct'

        r.step('subfolder reports correct parent', check_parentage)

    r.step('update folder description',
           lambda: client.files.update_folder(
               parent, description='updated by smoke test')
           or 'updated')

    def check_listed():
        for folder in client.files.list_folders(limit=500):
            if str(folder.get('externalId')) == str(parent):
                return 'found in list'
        raise NDExError('parent folder missing from list_folders')

    r.step('folder appears in list_folders', check_listed)

    r.step('folder_child_count',
           lambda: json.dumps(client.files.folder_child_count(parent)))

    # ------------------------------------------------------------------
    r.section('Creating a network directly in a folder')
    # ------------------------------------------------------------------

    net_url = r.step(
        'save_new_cx2_network(folder_id=...)',
        lambda: client.save_new_cx2_network(
            build_network(prefix + ' / network A'), folder_id=parent))
    net_id = uuid_of(net_url) if net_url else None
    if net_id is not None:
        r.networks.append(net_id)
        print('         network id %s' % net_id)

        def check_folder_id():
            """The folderId query parameter is the one thing most likely to
            be wrong, and a mismatch is silent: the network is simply
            created at the top level instead."""
            actual = str(client.networks.get_summary(net_id).get('folderId'))
            if actual != str(parent):
                raise NDExError('folderId is %s, expected %s; the folder_id '
                                'parameter did not take effect'
                                % (actual, parent))
            return 'folderId matches the requested folder'

        r.step('network landed in the requested folder', check_folder_id)

        def check_in_folder():
            for item in client.files.list_folder_items(parent):
                if str(item.get('uuid')) == str(net_id):
                    return 'found in listing'
            raise NDExError('network missing from folder listing')

        r.step('network listed in folder contents', check_in_folder)

        r.step('filter folder listing by type=NETWORK',
               lambda: '%d network(s)' % len(client.files.list_folder_items(
                   parent, item_type=FileType.NETWORK)))

    # ------------------------------------------------------------------
    r.section('Moving, shortcuts and copies')
    # ------------------------------------------------------------------

    if net_id is not None and child is not None:
        def move_and_verify():
            client.networks.move_to_folder(child, [net_id])
            if str(client.networks.get_summary(net_id).get('folderId')) \
                    != str(child):
                raise NDExError('folderId did not update after move')
            return 'moved into subfolder'

        r.step('networks.move_to_folder', move_and_verify)

        shortcut = r.step(
            'files.create_shortcut',
            lambda: client.files.create_shortcut(
                prefix + ' / shortcut to A', net_id, FileType.NETWORK,
                parent=parent))
        if shortcut is not None:
            r.shortcuts.append(shortcut)

            def check_target():
                actual = str(client.files.get_shortcut(shortcut)
                             .get('target'))
                if actual != str(net_id):
                    raise NDExError('shortcut target is %s, expected %s'
                                    % (actual, net_id))
                return 'target correct'

            r.step('shortcut resolves to the network', check_target)

        copy_id = r.step('files.copy',
                         lambda: client.files.copy(net_id, FileType.NETWORK,
                                                   parent))
        if copy_id is not None:
            r.networks.append(copy_id)

    # ------------------------------------------------------------------
    r.section('Visibility and sharing')
    # ------------------------------------------------------------------

    if net_id is not None:
        def set_and_check(vis):
            client.files.set_visibility(vis, [net_id],
                                        default_type=FileType.NETWORK)
            actual = str(client.networks.get_summary(net_id)
                         .get('visibility')).upper()
            if actual != vis:
                raise NDExError('visibility is %s after setting %s'
                                % (actual, vis))
            return 'now ' + vis

        r.step('files.set_visibility PUBLIC',
               lambda: set_and_check(Visibility.PUBLIC))
        r.step('files.set_visibility PRIVATE',
               lambda: set_and_check(Visibility.PRIVATE))

    keys = r.step('files.share mints an access key',
                  lambda: client.files.share({parent: FileType.FOLDER}))
    access_key = None
    if isinstance(keys, dict):
        access_key = keys.get(str(parent)) or (
            list(keys.values())[0] if keys else None)

    if access_key:
        r.step('anonymous read of folder using access key',
               lambda: str(anon.files.get_folder(
                   parent, access_key=access_key).get('name'))[:40])
        r.step('files.folder_access_key',
               lambda: json.dumps(
                   client.files.folder_access_key(parent))[:50])
        r.step('files.list_shared',
               lambda: '%d shared item(s)' % len(client.files.list_shared()))
        r.step('files.unshare',
               lambda: client.files.unshare({parent: FileType.FOLDER})
               or 'revoked')

    if args.share_with_user and net_id is not None:
        r.step('files.set_members grants READ to a second user',
               lambda: json.dumps(client.files.set_members(
                   {net_id: FileType.NETWORK},
                   {args.share_with_user: Permissions.READ}))[:60])
        r.step('files.list_members',
               lambda: json.dumps(client.files.list_members(
                   {net_id: FileType.NETWORK}))[:60])
    else:
        r.skipped.append('member sharing (pass --share-with-user)')

    # ------------------------------------------------------------------
    r.section('Search and queries')
    # ------------------------------------------------------------------

    r.step('files.search by run tag',
           lambda: '%s hit(s)' % client.files.search(
               tag, visibility=Visibility.PRIVATE, size=50).get('numFound'))

    r.step('files.search filtered to folders',
           lambda: '%s folder hit(s)' % client.files.search(
               tag, file_type=FileType.FOLDER,
               visibility=Visibility.PRIVATE).get('numFound'))

    if net_id is not None:
        r.step('networks.get_summaries (batch)',
               lambda: '%d summary/summaries'
               % len(client.networks.get_summaries([net_id])))
        r.step('networks.list_aspects',
               lambda: '%d aspect(s)'
               % len(client.networks.list_aspects(net_id)))
        r.step('networks.query returns CX2',
               lambda: '%d bytes' % len(client.networks.query(
                   net_id, 'ALPHA', search_depth=1).content))
        r.step('networks.interconnect_query returns CX2',
               lambda: '%d bytes'
               % len(client.networks.interconnect_query(
                   net_id, 'ALPHA BETA').content))
        r.step('networks.get_node_attributes',
               lambda: '%d bytes' % len(client.networks.get_node_attributes(
                   net_id, attribute_names=['name']).content))
        r.step('networks.export_as_tsv',
               lambda: '%d bytes'
               % len(client.networks.export_as_tsv(net_id).content),
               required=False)

    # ------------------------------------------------------------------
    r.section('Trash and restore')
    # ------------------------------------------------------------------

    if net_id is not None and len(r.networks) > 1:
        victim = r.networks[-1]

        def trash_it():
            client.networks.delete(victim)
            if not any(str(i.get('uuid')) == str(victim)
                       for i in client.files.list_trash()):
                raise NDExError('network not in trash after delete')
            return 'in trash'

        if r.step('networks.delete soft-deletes to trash', trash_it):
            def restore_it():
                client.files.restore(networks=[victim])
                client.networks.get_summary(victim)
                return 'restored'

            r.step('files.restore', restore_it)

    # ------------------------------------------------------------------
    r.section('Authentication switching')
    #
    # The transport shares its session with the flat v2 methods, so setting
    # a bearer token changes how those authenticate too. These checks exist
    # to catch that reaching outside the namespaces and breaking v2 calls.
    # ------------------------------------------------------------------

    # the flat verb helpers raise requests.HTTPError rather than converting
    # to NDExError, so both have to be treated as failure here
    AUTH_FAILURES = (NDExError, requests.exceptions.HTTPError)

    def flat_v2_call_works():
        """Calls a flat v2 method that requires credentials.

        Returns the parsed record. Note that Ndex2._return_response only
        parses JSON when Content-Type is exactly 'application/json', so a
        server appending a charset yields a string instead of a dict; the
        check below tolerates either."""
        record = client.get_user_by_username(args.username)
        if isinstance(record, str):
            return json.loads(record)
        return record

    r.step('flat v2 method authenticates with basic auth',
           lambda: 'externalId ' + str(flat_v2_call_works()
                                       .get('externalId'))[:12])

    def restore_basic():
        client._http.set_auth(username=args.username,
                              password=args.password)
        flat_v2_call_works()
        return 'basic auth restored'

    def bogus_bearer_reaches_flat_path():
        """Proves the bearer token replaces basic auth on the shared session
        rather than sitting alongside it. With a deliberately invalid token
        the flat v2 call must fail; had it succeeded, basic auth would still
        be in play. Credentials are restored either way, so a failure here
        does not strand the rest of the run."""
        rejected = False
        try:
            client._http.set_auth(bearer_token='not-a-real-token')
            try:
                flat_v2_call_works()
            except AUTH_FAILURES:
                rejected = True
        finally:
            client._http.set_auth(username=args.username,
                                  password=args.password)
        if not rejected:
            raise NDExError('flat v2 call succeeded with an invalid bearer '
                            'token, so it is still using basic auth')
        return 'flat v2 call correctly rejected the bogus token'

    r.step('bearer token replaces basic auth on the flat path',
           bogus_bearer_reaches_flat_path)
    r.step('basic auth can be restored', restore_basic)

    if args.id_token:
        def real_signin():
            user_rec = client.users.signin(args.id_token)
            if not isinstance(user_rec, dict):
                raise NDExError('signin did not return a user record')
            return 'signed in as ' + str(user_rec.get('userName',
                                                      user_rec.get(
                                                          'externalId')))

        def flat_works_with_token():
            record = flat_v2_call_works()
            if not isinstance(record, dict):
                raise NDExError('flat v2 call did not return a user record')
            return 'flat v2 method works with a bearer token'

        r.step('users.signin with a real id token', real_signin)
        r.step('flat v2 method authenticates with the bearer token',
               flat_works_with_token)
        r.step('basic auth restored after sign-in', restore_basic)
    else:
        r.skipped.append('real bearer token sign-in (pass --id-token)')

    # ------------------------------------------------------------------
    r.section('Client side rejections (these SHOULD fail)')
    # ------------------------------------------------------------------

    def expect(label, fn, exc):
        def check():
            try:
                fn()
            except exc:
                return 'correctly rejected'
            raise NDExError('call unexpectedly succeeded')
        r.step(label, check)

    expect('UNLISTED search rejected client side',
           lambda: client.files.search(visibility=Visibility.UNLISTED),
           NDExInvalidParameterError)
    expect('untyped file list rejected client side',
           lambda: client.files.share(['no-type-given']),
           NDExInvalidParameterError)
    expect('None folder id rejected client side',
           lambda: client.networks.move_to_folder(None, [net_id or 'x']),
           NDExInvalidParameterError)
    expect('unauthenticated write rejected client side',
           lambda: anon.files.create_folder('should not be created'),
           NDExUnauthorizedError)

    # ------------------------------------------------------------------
    # GUI verification
    # ------------------------------------------------------------------

    print('\n%s' % ('=' * 62))
    print('Verify in the web UI:')
    print('  folder tree   %s/folders/%s' % (web_host, parent))
    if child:
        print('  subfolder     %s/folders/%s' % (web_host, child))
    if net_id:
        print('  network       %s/networks/%s' % (web_host, net_id))
    print('  search for    %s' % prefix)
    print('\nExpected structure:')
    print('  %s/' % prefix)
    print('    |-- sub/')
    if net_id:
        print('    |     +-- network A          (3 nodes, 2 edges)')
    if r.shortcuts:
        print('    |-- shortcut to A           (shortcut)')
    if len(r.networks) > 1:
        print('    +-- network A (copy)')
    print('=' * 62)

    ok = r.summary()

    # ------------------------------------------------------------------
    # cleanup
    # ------------------------------------------------------------------

    do_cleanup = args.cleanup
    if not args.cleanup and not args.keep:
        try:
            reply = input('\nDelete the objects created by this run? '
                          '[y/N] ').strip().lower()
            do_cleanup = reply in ('y', 'yes')
        except (EOFError, KeyboardInterrupt):
            print('\nleaving objects in place')
            do_cleanup = False

    if args.keep or not do_cleanup:
        print('\nObjects left in place. To remove them later:')
        for nid in r.networks:
            print('  client.networks.delete(%r, permanent=True)' % nid)
        for sid in r.shortcuts:
            print('  client.files.delete_shortcut(%r)' % sid)
        for fid in reversed(r.folders):
            print('  client.files.delete_folder(%r, force=True, '
                  'permanent=True)' % fid)
    else:
        print('\nCleaning up...')
        for sid in r.shortcuts:
            _quiet(client.files.delete_shortcut, sid)
        for nid in r.networks:
            _quiet(client.networks.delete, nid, permanent=True)
        for fid in reversed(r.folders):
            _quiet(client.files.delete_folder, fid, force=True,
                   permanent=True)
        print('  done')

    return 0 if ok else 1


def _quiet(fn, *args, **kwargs):
    """
    Calls *fn*, reporting but not raising on failure, so one failed delete
    does not strand the remaining objects.
    """
    try:
        fn(*args, **kwargs)
        print('  removed %s' % (args[0] if args else ''))
    except Exception as e:
        print('  could not remove %s: %s' % (args[0] if args else '', e))


if __name__ == '__main__':
    sys.exit(main())
