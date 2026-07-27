Ndex3 REST client (v3 API)
--------------------------------

The :py:class:`~ndex2.client_v3.Ndex3` class interfaces with the **v3**
`NDEx REST Server API`_. The v3 API replaces the flat *network set* model with
a file system: every item a user owns is a file item of type ``NETWORK``,
``FOLDER`` or ``SHORTCUT``. Folders nest arbitrarily, and shortcuts let one
item appear in several folders. Groups were removed; per-user sharing replaces
them.

See ``MIGRATION_V3.md`` in the source distribution for a mapping from
:py:class:`~ndex2.client.Ndex2` calls to their v3 equivalents.

    Example creating anonymous connection:

        .. code-block:: python

            from ndex2.client_v3 import Ndex3
            anon_ndex = Ndex3()

    Example creating connection with username and password:

        .. code-block:: python

            from ndex2.client_v3 import Ndex3
            my_ndex = Ndex3('https://www.ndexbio.org',
                            username='your account',
                            password='your password')

    Example authenticating with an OAuth/Keycloak id token:

        .. code-block:: python

            from ndex2.client_v3 import Ndex3
            my_ndex = Ndex3('https://www.ndexbio.org',
                            bearer_token='your id token')

    Example creating a folder and a network inside it:

        .. code-block:: python

            from ndex2.client_v3 import Ndex3, FileType

            client = Ndex3(username='bob', password='secret')
            folder_id = client.create_folder('My Pathways')
            net_id = client.save_new_cx2_network_in_folder(
                cx, folder_id=folder_id)

            for item in client.list_folder_items(folder_id):
                print(item['name'], item['type'])

.. note::

    Methods inherited from :py:class:`~ndex2.client.Ndex2` that rely on
    endpoints the v3 API does not serve raise
    :py:class:`~ndex2.exceptions.NDExUnsupportedCallError` naming their
    replacement. This includes all network set and group calls, CX (version 1)
    network I/O, tasks, provenance, sample networks and system properties.

.. autoclass:: ndex2.client_v3.Ndex3
    :members: clear_trash, copy_file, create_folder, create_shortcut, create_workspace, delete_folder, delete_network, delete_shortcut, delete_trashed_item, delete_workspace, export_network_as_tsv, get_file_count, get_folder, get_folder_access_key, get_folder_child_count, get_network_aspects, get_network_summaries, get_network_summary, get_node_attributes, get_shortcut, get_user_by_username, get_user_home, get_workspace, get_workspaces_for_user, grant_network_to_user_by_username, grant_networks_to_user, interconnect_query_as_cx2_stream, list_folder_items, list_folders, list_shared_files, list_sharing_members, list_shortcuts, list_trash, make_network_private, make_network_public, mint_doi, move_networks_to_folder, query_network_as_cx2_stream, rename_workspace, restore_from_trash, save_new_cx2_network_in_folder, search_files, set_file_visibility, set_sharing_members, share_files, signin, transfer_network_ownership, unshare_files, update_folder, update_network_user_permission, update_shortcut, update_status, update_workspace, update_workspace_networks, get_network_as_cx2_stream, get_network_aspect_as_cx2_stream, save_cx2_stream_as_new_network, save_new_cx2_network, update_cx2_network, get_id_for_user

Constants
~~~~~~~~~

.. autoclass:: ndex2.client_v3.FileType
    :members:

.. autoclass:: ndex2.client_v3.Visibility
    :members:

.. autoclass:: ndex2.client_v3.Permissions
    :members:

.. _NDEx REST Server API: https://home.ndexbio.org/using-the-ndex-server-api
.. _NDEx: https://ndexbio.org
