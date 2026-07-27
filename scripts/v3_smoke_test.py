#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
End-to-end smoke test for :py:class:`ndex2.client_v3.Ndex3`.

Exercises the v3 file system against a live NDEx server: folders,
shortcuts, network placement, sharing, access keys, search, queries,
trash and workspaces. Unlike the unit tests, nothing here is mocked.

Every object is named with a timestamped run tag so it is obvious in the
web UI which run created it, and so a failed run never collides with a
later one. By default the script pauses before cleanup so the structure
can be inspected in the GUI.

Usage::

    export NDEX_USER=your_account
    export NDEX_PASS=your_password
    python scripts/v3_smoke_test.py --host https://dev3.ndex.ucsd.edu/rest

    # leave everything behind for GUI inspection, no prompt
    python scripts/v3_smoke_test.py --keep

    # unattended, clean up without asking
    python scripts/v3_smoke_test.py --cleanup

Exits non-zero if any check fails.
"""

import argparse
import datetime
import json
import os
import sys
import traceback

# allow running from a source checkout without installing
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..'))

from ndex2.client_v3 import Ndex3          # noqa: E402
from ndex2.client_v3 import FileType        # noqa: E402
from ndex2.client_v3 import Permissions     # noqa: E402
from ndex2.client_v3 import Visibility      # noqa: E402
from ndex2.cx2 import CX2Network            # noqa: E402
from ndex2.exceptions import NDExError      # noqa: E402

DEFAULT_HOST = 'https://dev3.ndex.ucsd.edu/rest'

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
GREY = '\033[90m'
BOLD = '\033[1m'
OFF = '\033[0m'


class Runner(object):
    """
    Tracks step results and the objects that need cleaning up.
    """

    def __init__(self, verbose=False, color=True):
        self.verbose = verbose
        self.color = color
        self.passed = 0
        self.failed = []
        self.skipped = []
        # cleanup registers, torn down in reverse order of creation
        self.networks = []
        self.shortcuts = []
        self.folders = []
        self.workspaces = []

    def _c(self, code, text):
        if not self.color:
            return text
        return code + text + OFF

    def step(self, name, fn, required_ok=True):
        """
        Runs a single check.

        :param name: Human readable description
        :type name: str
        :param fn: Zero argument callable performing the check
        :param required_ok: If ``False`` a failure is reported but the
                            run is still considered a success. Use for
                            checks that depend on optional server
                            configuration.
        :type required_ok: bool
        :return: Whatever *fn* returned, or ``None`` on failure
        """
        try:
            result = fn()
        except Exception as e:
            label = 'WARN' if not required_ok else 'FAIL'
            code = YELLOW if not required_ok else RED
            print('  %s %s' % (self._c(code, '[' + label + ']'), name))
            print('         %s: %s' % (type(e).__name__, e))
            if self.verbose:
                traceback.print_exc()
            if required_ok:
                self.failed.append(name)
            else:
                self.skipped.append(name)
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
    Builds a tiny but valid CX2 network.

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


def parse_args():
    p = argparse.ArgumentParser(
        description='End-to-end smoke test for the Ndex3 v3 client.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('--host', default=os.getenv('NDEX_HOST', DEFAULT_HOST),
                   help='REST base URL, including any servlet context path')
    p.add_argument('--web-host', default=os.getenv('NDEX_WEB_HOST'),
                   help='Base URL of the web UI, for printing links. '
                        'Defaults to --host with a trailing /rest removed.')
    p.add_argument('--username', default=os.getenv('NDEX_USER'))
    p.add_argument('--password', default=os.getenv('NDEX_PASS'))
    p.add_argument('--share-with-user',
                   help='UUID of a second user, to test member sharing. '
                        'Skipped if not given.')
    group = p.add_mutually_exclusive_group()
    group.add_argument('--keep', action='store_true',
                       help='Leave all created objects behind, no prompt')
    group.add_argument('--cleanup', action='store_true',
                       help='Delete created objects without prompting')
    p.add_argument('--no-color', action='store_true')
    p.add_argument('-v', '--verbose', action='store_true',
                   help='Print full tracebacks on failure')
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

    client = Ndex3(host=args.host, username=args.username,
                   password=args.password)
    anon = Ndex3(host=args.host)

    # ------------------------------------------------------------------
    r.section('Connectivity')
    # ------------------------------------------------------------------

    def check_status():
        status = client.update_status()
        if not isinstance(status, dict):
            raise NDExError('status was not a JSON object')
        return str(status.get('message', ''))[:40]

    r.step('GET /v3/admin/status reachable', check_status)

    user = r.step('look up own account',
                  lambda: client.get_user_by_username(args.username))
    user_id = user.get('externalId') if isinstance(user, dict) else None
    if user_id is None:
        print('\nCannot continue without a user id.')
        r.summary()
        return 1
    print('         user id %s' % user_id)

    r.step('list home directory',
           lambda: '%d item(s) at root' % len(client.get_user_home(user_id)))
    r.step('count own files',
           lambda: json.dumps(client.get_file_count()))

    # ------------------------------------------------------------------
    r.section('Folders')
    # ------------------------------------------------------------------

    parent = r.step(
        'create parent folder',
        lambda: client.create_folder(
            prefix, description='v3 client smoke test, safe to delete'))
    if parent is None:
        print('\nCannot continue without a folder.')
        r.summary()
        return 1
    r.folders.append(parent)

    child = r.step('create nested subfolder',
                   lambda: client.create_folder(prefix + ' / sub',
                                                parent=parent))
    if child is not None:
        r.folders.append(child)

    def check_parentage():
        folder = client.get_folder(child)
        actual = str(folder.get('parent'))
        if actual != str(parent):
            raise NDExError('parent is %s, expected %s' % (actual, parent))
        return 'parent link correct'

    if child is not None:
        r.step('subfolder reports correct parent', check_parentage)

    r.step('rename parent folder',
           lambda: client.update_folder(parent,
                                        description='renamed by smoke test')
           or 'description updated')

    def check_listed():
        for folder in client.list_folders(limit=500):
            if str(folder.get('externalId')) == str(parent):
                return 'found in list'
        raise NDExError('parent folder missing from list_folders')

    r.step('folder appears in own folder list', check_listed)

    # ------------------------------------------------------------------
    r.section('Networks in folders')
    # ------------------------------------------------------------------

    net_id = r.step(
        'create network directly inside folder',
        lambda: client.save_new_cx2_network_in_folder(
            build_network(prefix + ' / network A'), folder_id=parent))
    if net_id is not None:
        r.networks.append(net_id)

    def check_folder_id():
        summary = client.get_network_summary(net_id)
        actual = str(summary.get('folderId'))
        if actual != str(parent):
            raise NDExError('folderId is %s, expected %s' % (actual, parent))
        return 'folderId matches'

    if net_id is not None:
        r.step('network summary reports folderId', check_folder_id)

        def check_in_folder():
            for item in client.list_folder_items(parent):
                if str(item.get('uuid')) == str(net_id):
                    return 'found in listing'
            raise NDExError('network missing from folder listing')

        r.step('network listed in folder contents', check_in_folder)

        r.step('folder child count reports the network',
               lambda: json.dumps(client.get_folder_child_count(parent)))

        r.step('filter folder listing by type=NETWORK',
               lambda: '%d network(s)' % len(client.list_folder_items(
                   parent, item_type=FileType.NETWORK)))

    # ------------------------------------------------------------------
    r.section('Moving, shortcuts and copies')
    # ------------------------------------------------------------------

    if net_id is not None and child is not None:
        def move_and_verify():
            client.move_networks_to_folder(child, [net_id])
            summary = client.get_network_summary(net_id)
            if str(summary.get('folderId')) != str(child):
                raise NDExError('folderId did not update after move')
            return 'moved into subfolder'

        r.step('move network into subfolder', move_and_verify)

        shortcut = r.step(
            'create shortcut to network in parent folder',
            lambda: client.create_shortcut(prefix + ' / shortcut to A',
                                           net_id, FileType.NETWORK,
                                           parent=parent))
        if shortcut is not None:
            r.shortcuts.append(shortcut)

            def check_target():
                actual = str(client.get_shortcut(shortcut).get('target'))
                if actual != str(net_id):
                    raise NDExError('shortcut target is %s, expected %s'
                                    % (actual, net_id))
                return 'target correct'

            r.step('shortcut resolves to the network', check_target)
            r.step('shortcut listed in own shortcut list',
                   lambda: '%d shortcut(s)' % len(client.list_shortcuts()))

        copy_id = r.step('copy network into parent folder',
                         lambda: client.copy_file(net_id, FileType.NETWORK,
                                                  parent))
        if copy_id is not None:
            r.networks.append(copy_id)

    # ------------------------------------------------------------------
    r.section('Visibility and sharing')
    # ------------------------------------------------------------------

    if net_id is not None:
        def publish_and_verify():
            client.make_network_public(net_id)
            vis = str(client.get_network_summary(net_id).get('visibility'))
            if vis.upper() != Visibility.PUBLIC:
                raise NDExError('visibility is %s after publish' % vis)
            return 'now PUBLIC'

        r.step('make_network_public via v3 batch endpoint',
               publish_and_verify)

        def unpublish_and_verify():
            client.make_network_private(net_id)
            vis = str(client.get_network_summary(net_id).get('visibility'))
            if vis.upper() != Visibility.PRIVATE:
                raise NDExError('visibility is %s after unpublish' % vis)
            return 'back to PRIVATE'

        r.step('make_network_private via v3 batch endpoint',
               unpublish_and_verify)

    keys = r.step('mint access key for parent folder',
                  lambda: client.share_files({parent: FileType.FOLDER}))
    access_key = None
    if isinstance(keys, dict):
        access_key = keys.get(str(parent)) or (
            list(keys.values())[0] if keys else None)

    if access_key:
        r.step('anonymous read of folder using access key',
               lambda: str(anon.get_folder(parent,
                                           access_key=access_key
                                           ).get('name'))[:40])
        r.step('access key retrievable via folder endpoint',
               lambda: json.dumps(client.get_folder_access_key(parent))[:50])
        r.step('folder appears in shared list',
               lambda: '%d shared item(s)' % len(client.list_shared_files()))
        r.step('revoke access key',
               lambda: client.unshare_files({parent: FileType.FOLDER})
               or 'revoked')

    if args.share_with_user and net_id is not None:
        r.step('grant READ to second user',
               lambda: json.dumps(client.update_network_user_permission(
                   args.share_with_user, net_id, Permissions.READ))[:60])
        r.step('list sharing members',
               lambda: json.dumps(client.list_sharing_members(
                   {net_id: FileType.NETWORK}))[:60])
    else:
        r.skipped.append('member sharing (pass --share-with-user to test)')

    # ------------------------------------------------------------------
    r.section('Search and queries')
    # ------------------------------------------------------------------

    def search_private():
        res = client.search_files(tag, visibility=Visibility.PRIVATE,
                                  size=50)
        return '%s hit(s) for run tag' % res.get('numFound')

    r.step('search own files by run tag', search_private)

    r.step('search filtered to folders only',
           lambda: '%s folder hit(s)' % client.search_files(
               tag, file_type=FileType.FOLDER,
               visibility=Visibility.PRIVATE).get('numFound'))

    if net_id is not None:
        r.step('batch network summary',
               lambda: '%d summary/summaries'
               % len(client.get_network_summaries([net_id])))
        r.step('list CX2 aspect metadata',
               lambda: '%d aspect(s)'
               % len(client.get_network_aspects(net_id)))
        r.step('neighborhood query returns CX2',
               lambda: '%d bytes' % len(client.query_network_as_cx2_stream(
                   net_id, 'ALPHA', search_depth=1).content))
        r.step('interconnect query returns CX2',
               lambda: '%d bytes'
               % len(client.interconnect_query_as_cx2_stream(
                   net_id, 'ALPHA BETA').content))
        r.step('node attribute filter',
               lambda: '%d bytes' % len(client.get_node_attributes(
                   net_id, attribute_names=['name']).content))
        r.step('export network as TSV',
               lambda: '%d bytes'
               % len(client.export_network_as_tsv(net_id).content),
               required_ok=False)

    # ------------------------------------------------------------------
    r.section('Trash and restore')
    # ------------------------------------------------------------------

    if net_id is not None and len(r.networks) > 1:
        victim = r.networks[-1]

        def trash_it():
            client.delete_network(victim)
            found = any(str(i.get('uuid')) == str(victim)
                        for i in client.list_trash())
            if not found:
                raise NDExError('network not present in trash after delete')
            return 'in trash'

        if r.step('soft delete network into trash', trash_it):
            def restore_it():
                client.restore_from_trash(networks=[victim])
                client.get_network_summary(victim)
                return 'restored'

            r.step('restore network from trash', restore_it)

    # ------------------------------------------------------------------
    r.section('Workspaces')
    # ------------------------------------------------------------------

    ws = r.step('create workspace',
                lambda: client.create_workspace(
                    prefix + ' / workspace',
                    network_ids=[net_id] if net_id else None))
    if ws is not None:
        r.workspaces.append(ws)
        r.step('rename workspace',
               lambda: client.rename_workspace(ws, prefix + ' / renamed')
               or 'renamed')
        r.step('read workspace back',
               lambda: str(client.get_workspace(ws).get('name'))[:40])
        if net_id is not None:
            r.step('replace workspace network list',
                   lambda: client.update_workspace_networks(ws, [net_id])
                   or 'updated')
        r.step('workspace listed for user',
               lambda: '%d workspace(s)'
               % len(client.get_workspaces_for_user(user_id)))

    # ------------------------------------------------------------------
    r.section('Rejections (these SHOULD fail)')
    # ------------------------------------------------------------------

    def expect_raises(label, fn, exc):
        def check():
            try:
                fn()
            except exc:
                return 'correctly rejected'
            raise NDExError('call unexpectedly succeeded')
        r.step(label, check)

    from ndex2.exceptions import NDExUnsupportedCallError
    from ndex2.exceptions import NDExInvalidParameterError

    expect_raises('networkset call raises NDExUnsupportedCallError',
                  lambda: client.create_networkset('x', 'y'),
                  NDExUnsupportedCallError)
    expect_raises('group call raises NDExUnsupportedCallError',
                  lambda: client.grant_networks_to_group('g', ['n']),
                  NDExUnsupportedCallError)
    expect_raises('UNLISTED search rejected client side',
                  lambda: client.search_files(visibility=Visibility.UNLISTED),
                  NDExInvalidParameterError)
    expect_raises('untyped file list rejected client side',
                  lambda: client.share_files(['not-a-typed-entry']),
                  NDExInvalidParameterError)

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
    print('    ├── sub/')
    if net_id:
        print('    │     └── network A            (3 nodes, 2 edges)')
    if r.shortcuts:
        print('    ├── shortcut to A             (shortcut)')
    if len(r.networks) > 1:
        print('    └── network A (copy)')
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
            print('  client.delete_network(%r, permanent=True)' % nid)
        for sid in r.shortcuts:
            print('  client.delete_shortcut(%r)' % sid)
        for fid in reversed(r.folders):
            print('  client.delete_folder(%r, force=True, permanent=True)'
                  % fid)
        for wid in r.workspaces:
            print('  client.delete_workspace(%r)' % wid)
    else:
        print('\nCleaning up...')
        for wid in r.workspaces:
            _quiet(client.delete_workspace, wid)
        for sid in r.shortcuts:
            _quiet(client.delete_shortcut, sid)
        for nid in r.networks:
            _quiet(client.delete_network, nid, permanent=True)
        for fid in reversed(r.folders):
            _quiet(client.delete_folder, fid, force=True, permanent=True)
        print('  done')

    return 0 if ok else 1


def _quiet(fn, *args, **kwargs):
    """
    Calls *fn*, reporting but not raising on failure.

    Cleanup should be best effort: one failed delete must not strand the
    remaining objects.
    """
    try:
        fn(*args, **kwargs)
        print('  removed %s' % (args[0] if args else ''))
    except Exception as e:
        print('  could not remove %s: %s' % (args[0] if args else '', e))


if __name__ == '__main__':
    sys.exit(main())
