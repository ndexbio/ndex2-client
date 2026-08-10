v3 API namespaces
=================

.. versionadded:: 3.12.0

The v3 `NDEx REST Service`_ organizes user content as a file system. Every item
a user owns is a **file item** with one of three types
(:py:class:`~ndex2.constants.FileType`): ``NETWORK``, ``FOLDER`` or
``SHORTCUT``. Folders nest arbitrarily, and a shortcut lets a single item appear
in more than one folder.

These endpoints are reached through namespace attributes on
:py:class:`~ndex2.client.Ndex2`, so there is one client to build and one set of
credentials regardless of which API version serves a given call:

.. code-block:: python

    from ndex2.client import Ndex2
    from ndex2.constants import FileType, Permissions

    client = Ndex2(username='bob', password='secret',
                   skip_version_check=True)

    # a small CX2 network. Give it a name via networkAttributes, otherwise
    # the network has none and the field is absent everywhere it is reported.
    cx2 = [{'CXVersion': '2.0', 'hasFragments': False},
           {'networkAttributes': [{'name': 'BRCA pathway'}]},
           {'nodes': [{'id': 1, 'v': {'name': 'ALPHA'}}]},
           {'status': [{'success': True}]}]

    # create a folder and a network inside it
    folder = client.files.create_folder('My Pathways')
    net_url = client.save_new_cx2_network(cx2, folder_id=folder)
    net_id = net_url.rstrip('/').split('/')[-1]

    # list what is in the folder
    for item in client.files.list_folder_items(folder):
        print(item.get('name', '<NA>'), item['type'])

    # share the folder, which covers everything inside it
    alice_id = client.users.get('alice')['externalId']
    client.files.set_members({folder: FileType.FOLDER},
                             {alice_id: Permissions.WRITE})

.. note::

   Network creation is not on ``client.networks``. Use
   :py:meth:`~ndex2.client.Ndex2.save_new_cx2_network` or
   :py:meth:`~ndex2.client.Ndex2.save_cx2_stream_as_new_network`, both of which
   already target v3 and accept a ``folder_id``.

Some namespace methods overlap a flat method on
:py:class:`~ndex2.client.Ndex2` where the v3 endpoint offers more than its v2
counterpart. Both remain available:

.. list-table::
   :header-rows: 1
   :widths: 35 35 30

   * - Flat method (v2)
     - Namespace method (v3)
     - What v3 adds
   * - :py:meth:`~ndex2.client.Ndex2.get_network_summary`
     - :py:meth:`~ndex2.api.networks.NetworksAPI.get_summary`
     - v3 ``NetworkSummaryV3`` field set
   * - :py:meth:`~ndex2.client.Ndex2.delete_network`
     - :py:meth:`~ndex2.api.networks.NetworksAPI.delete`
     - trash, restorable
   * - ``Ndex2.search_network_nodes()``
     - :py:meth:`~ndex2.api.networks.NetworksAPI.get_node_attributes`
     - renamed route, CX2
   * - :py:meth:`~ndex2.client.Ndex2.get_neighborhood_as_cx_stream`
     - :py:meth:`~ndex2.api.networks.NetworksAPI.query`
     - CX2 instead of CX
   * - :py:meth:`~ndex2.client.Ndex2.search_networks`
     - :py:meth:`~ndex2.api.files.FilesAPI.search`
     - folders and shortcuts too

Walking a user's content
------------------------

There is no single call that lists everything. Start at the home directory,
which returns the items with no parent folder, then recurse:

.. code-block:: python

    from ndex2.constants import FileType

    def walk(client, items, depth=0):
        for item in items:
            print('  ' * depth + item.get('name', '<NA>') + ' [' + item['type'] + ']')
            if item['type'] == FileType.FOLDER:
                walk(client, client.files.list_folder_items(item['uuid']),
                     depth + 1)

    user = client.users.get('bob')
    walk(client, client.users.home(user['externalId']))

.. note::

   A file item summary omits any field the server has no value for, rather than
   reporting it as null. A network created without a ``name`` network attribute
   therefore has no ``name`` key at all, so code walking arbitrary content may
   want :py:meth:`dict.get`. ``uuid`` and ``type`` are always present.

Network sets appear in this listing, because a network set is stored as a
folder on the server. ``client.files.get_folder()`` accepts a network set UUID.

client.files
------------

Folders, shortcuts, trash, sharing and file search.

.. autoclass:: ndex2.api.files.FilesAPI
    :members:

.. autodata:: ndex2.api.files.HOME

client.networks
---------------

Network summaries, aspects, queries, export and ownership.

.. autoclass:: ndex2.api.networks.NetworksAPI
    :members:

client.users
------------

User lookup, home directory listing and token sign-in.

.. autoclass:: ndex2.api.users.UsersAPI
    :members:

client.admin
------------

Server status.

.. autoclass:: ndex2.api.admin.AdminAPI
    :members:

Constants
---------

:py:class:`~ndex2.constants.FileType`,
:py:class:`~ndex2.constants.Visibility` and
:py:class:`~ndex2.constants.Permissions` hold the values these methods accept.
See :doc:`miscref`.

.. _NDEx: http://www.ndexbio.org
.. _`NDEx REST Service`: https://home.ndexbio.org/using-the-ndex-server-api
