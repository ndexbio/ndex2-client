# -*- coding: utf-8 -*-

"""
The ``files`` namespace, reached as ``client.files``.

The v3 API organizes user content as a file system. Every item a user owns
is a **file item** with one of three types
(:py:class:`~ndex2.constants.FileType`): ``NETWORK``, ``FOLDER`` or
``SHORTCUT``. Folders nest arbitrarily, and a shortcut lets a single item
appear in more than one folder.

Everything in this namespace is served by ``/v3``.

.. versionadded:: 3.12.0
"""

from ndex2.api._validators import require_enum
from ndex2.api._validators import require_id
from ndex2.api._validators import require_id_list
from ndex2.api._validators import require_str
from ndex2.api._validators import to_file_map
from ndex2.constants import FileType
from ndex2.constants import Visibility
from ndex2.constants import Permissions
from ndex2.exceptions import NDExInvalidParameterError

FOLDERS = '/files/folders'
SHORTCUTS = '/files/shortcuts'
FILES = '/files'
BATCH_FILES = '/batch/files'
SEARCH_FILES = '/search/files'

HOME = 'home'
"""
Special folder identifier accepted in place of a UUID, denoting the top
level of the authenticated user's home.
"""


class FilesAPI(object):
    """
    Folders, shortcuts, trash, sharing and file search.

    Not instantiated directly. Reached as ``client.files`` on
    :py:class:`~ndex2.client.Ndex2`.

    .. versionadded:: 3.12.0

    :param http: Shared transport, supplied by the client
    :type http: :py:class:`~ndex2.transport.HttpTransport`
    """

    def __init__(self, http):
        self._http = http

    # ------------------------------------------------------------------
    # folders
    # ------------------------------------------------------------------

    def create_folder(self, name, parent=None, description=None,
                      visibility=None):
        """
        Creates a folder.

        ``POST /v3/files/folders/``

        .. versionadded:: 3.12.0

        :param name: Name of the new folder
        :type name: str
        :param parent: UUID of the parent folder. Omit to create the
                       folder at the top level of the user's home.
        :type parent: str
        :param description: Optional description
        :type description: str
        :param visibility: One of :py:class:`~ndex2.constants.Visibility`.
                           Defaults to the server default of ``PRIVATE``.
        :type visibility: str
        :raises NDExInvalidParameterError: For invalid arguments
        :raises NDExUnauthorizedError: If no credentials are set, or write
                                       access to *parent* is denied
        :raises NDExError: For other server errors
        :return: UUID of the new folder
        :rtype: str
        """
        self._http.require_auth()
        require_str(name, 'name')
        body = {'name': name}
        if parent is not None:
            body['parent'] = str(parent)
        if description is not None:
            body['description'] = description
        vis = require_enum(visibility, Visibility.ALL, 'visibility')
        if vis is not None:
            body['visibility'] = vis
        response = self._http.post(FOLDERS + '/', json_body=body,
                                   return_response=True)
        return self._http.uuid_from_created(response)

    def get_folder(self, folder_id, access_key=None):
        """
        Retrieves a folder.

        ``GET /v3/files/folders/{folderid}``

        Because a network set is stored as a folder, a network set UUID is
        accepted here as well.

        .. versionadded:: 3.12.0

        :param folder_id: UUID of the folder
        :type folder_id: str
        :param access_key: Access key granting read access to a folder the
                           caller does not own
        :type access_key: str
        :raises NDExInvalidParameterError: For an invalid *folder_id*
        :raises NDExNotFoundError: If no such folder exists
        :raises NDExUnauthorizedError: If read access is denied
        :return: Folder, with keys including ``externalId``, ``name``,
                 ``parent``, ``description``, ``owner``, ``owner_id``,
                 ``visibility``, ``creationTime`` and ``modificationTime``
        :rtype: dict
        """
        require_str(folder_id, 'folder_id')
        return self._http.get(FOLDERS + '/' + str(folder_id),
                              params={'accesskey': access_key})

    def update_folder(self, folder_id, name=None, parent=None,
                      description=None, visibility=None):
        """
        Updates a folder. Setting *parent* moves it.

        ``PUT /v3/files/folders/{folderid}``

        .. versionadded:: 3.12.0

        :param folder_id: UUID of the folder to update
        :type folder_id: str
        :param name: New name
        :type name: str
        :param parent: UUID of the new parent folder
        :type parent: str
        :param description: New description
        :type description: str
        :param visibility: One of :py:class:`~ndex2.constants.Visibility`
        :type visibility: str
        :raises NDExInvalidParameterError: If no field to update is given,
                                           or a value is invalid
        :raises NDExNotFoundError: If no such folder exists
        :raises NDExUnauthorizedError: If write access is denied
        :return: ``None``
        """
        self._http.require_auth()
        require_str(folder_id, 'folder_id')
        body = {}
        if name is not None:
            body['name'] = require_str(name, 'name')
        if parent is not None:
            body['parent'] = str(parent)
        if description is not None:
            body['description'] = description
        vis = require_enum(visibility, Visibility.ALL, 'visibility')
        if vis is not None:
            body['visibility'] = vis
        if len(body) == 0:
            raise NDExInvalidParameterError('At least one of name, parent, '
                                            'description or visibility must '
                                            'be set')
        return self._http.put(FOLDERS + '/' + str(folder_id), json_body=body)

    def delete_folder(self, folder_id, force=False, permanent=False):
        """
        Deletes a folder.

        ``DELETE /v3/files/folders/{folderid}``

        By default the folder is moved to the trash and can be restored
        with :py:meth:`restore`, and the server refuses to delete a folder
        that still has children.

        .. versionadded:: 3.12.0

        :param folder_id: UUID of the folder
        :type folder_id: str
        :param force: If ``True``, delete the folder even when it still
                      contains items
        :type force: bool
        :param permanent: If ``True``, bypass the trash and delete
                          irrecoverably
        :type permanent: bool
        :raises NDExInvalidParameterError: For an invalid *folder_id*
        :raises NDExNotFoundError: If no such folder exists
        :raises NDExUnauthorizedError: If delete access is denied
        :return: ``None``
        """
        self._http.require_auth()
        require_str(folder_id, 'folder_id')
        return self._http.delete(
            FOLDERS + '/' + str(folder_id),
            params={'force': str(bool(force)).lower(),
                    'permanent': str(bool(permanent)).lower()})

    def list_folder_items(self, folder_id=HOME, item_type=None,
                          format='update', access_key=None):
        """
        Lists the direct children of a folder.

        ``GET /v3/files/folders/{folderid}/list``

        Called with no arguments this lists the top level of the
        authenticated user's home, because *folder_id* defaults to the
        special identifier ``home`` rather than a UUID. That is the
        starting point for walking a user's own content:

        .. code-block:: python

            for item in client.files.list_folder_items():
                print(item.get('name', '<NA>'), item['type'])

        To list another user's home, use
        :py:meth:`~ndex2.api.users.UsersAPI.home` with their UUID.

        .. versionadded:: 3.12.0

        :param folder_id: UUID of the folder, or the special value
                          :py:const:`~ndex2.api.files.HOME` to list the
                          authenticated user's home. Defaults to ``home``.
        :type folder_id: str
        :param item_type: Restrict results to one
                          :py:class:`~ndex2.constants.FileType`. Omit for
                          all types.
        :type item_type: str
        :param format: ``update`` for the full item summary, ``compact``
                       for a reduced one
        :type format: str
        :param access_key: Access key granting read access
        :type access_key: str
        :raises NDExInvalidParameterError: For invalid arguments
        :raises NDExNotFoundError: If no such folder exists
        :raises NDExUnauthorizedError: If read access is denied, or if
                                       *folder_id* is ``home`` and no
                                       credentials are set
        :return: File item summaries. ``uuid`` and ``type`` are always
                 present. Other keys, including ``name``, are omitted rather
                 than reported as null when the server has no value, so a
                 network created without a ``name`` network attribute has no
                 ``name`` key. Which fields are populated also varies with
                 *format*.
        :rtype: list
        """
        require_str(folder_id, 'folder_id')
        if str(folder_id) == HOME:
            # the server cannot resolve 'home' without knowing who is asking
            self._http.require_auth()
        params = {'format': format,
                  'accesskey': access_key,
                  'type': require_enum(item_type, FileType.ALL,
                                       'item_type')}
        result = self._http.get(FOLDERS + '/' + str(folder_id) + '/list',
                                params=params)
        return [] if result is None else result

    def folder_child_count(self, folder_id, access_key=None):
        """
        Counts the direct children of a folder, by type.

        ``GET /v3/files/folders/{folderid}/count``

        .. versionadded:: 3.12.0

        :param folder_id: UUID of the folder
        :type folder_id: str
        :param access_key: Access key granting read access
        :type access_key: str
        :raises NDExNotFoundError: If no such folder exists
        :return: Counts keyed by ``network``, ``folder`` and ``shortcut``
        :rtype: dict
        """
        require_str(folder_id, 'folder_id')
        return self._http.get(FOLDERS + '/' + str(folder_id) + '/count',
                              params={'accesskey': access_key})

    def folder_access_key(self, folder_id):
        """
        Retrieves the access key of a shared folder.

        ``GET /v3/files/folders/{folderid}/accesskey``

        Use :py:meth:`share` to create one.

        .. versionadded:: 3.12.0

        :param folder_id: UUID of the folder
        :type folder_id: str
        :raises NDExNotFoundError: If no such folder exists
        :raises NDExUnauthorizedError: If the caller is not the owner
        :return: Map containing the access key
        :rtype: dict
        """
        self._http.require_auth()
        require_str(folder_id, 'folder_id')
        return self._http.get(FOLDERS + '/' + str(folder_id) + '/accesskey')

    # ------------------------------------------------------------------
    # shortcuts
    # ------------------------------------------------------------------

    def create_shortcut(self, name, target, target_type, parent=None,
                        visibility=None):
        """
        Creates a shortcut pointing at another file item.

        ``POST /v3/files/shortcuts/``

        A shortcut lets one network or folder appear in several folders
        without being copied.

        .. versionadded:: 3.12.0

        :param name: Name of the shortcut
        :type name: str
        :param target: UUID of the item the shortcut points at
        :type target: str
        :param target_type: Type of *target*, one of
                            :py:class:`~ndex2.constants.FileType`
        :type target_type: str
        :param parent: UUID of the folder holding the shortcut. Omit for
                       the top level of the user's home.
        :type parent: str
        :param visibility: One of :py:class:`~ndex2.constants.Visibility`
        :type visibility: str
        :raises NDExInvalidParameterError: For invalid arguments
        :raises NDExUnauthorizedError: If no credentials are set, or
                                       access to *target* is denied
        :return: UUID of the new shortcut
        :rtype: str
        """
        self._http.require_auth()
        require_str(name, 'name')
        require_id(target, 'target')
        body = {'name': name,
                'target': str(target),
                'targetType': require_enum(target_type, FileType.ALL,
                                           'target_type',
                                           allow_none=False)}
        if parent is not None:
            body['parent'] = str(parent)
        vis = require_enum(visibility, Visibility.ALL, 'visibility')
        if vis is not None:
            body['visibility'] = vis
        response = self._http.post(SHORTCUTS + '/', json_body=body,
                                   return_response=True)
        return self._http.uuid_from_created(response)

    def get_shortcut(self, shortcut_id):
        """
        Retrieves a shortcut.

        ``GET /v3/files/shortcuts/{shortcutid}``

        .. versionadded:: 3.12.0

        :param shortcut_id: UUID of the shortcut
        :type shortcut_id: str
        :raises NDExNotFoundError: If no such shortcut exists
        :raises NDExUnauthorizedError: If read access is denied
        :return: Shortcut, with keys including ``externalId``, ``name``,
                 ``parent``, ``target``, ``targetType``, ``owner`` and
                 ``visibility``
        :rtype: dict
        """
        require_str(shortcut_id, 'shortcut_id')
        return self._http.get(SHORTCUTS + '/' + str(shortcut_id))

    def update_shortcut(self, shortcut_id, name=None, parent=None,
                        target=None, target_type=None, visibility=None):
        """
        Updates a shortcut.

        ``PUT /v3/files/shortcuts/{shortcutid}``

        .. versionadded:: 3.12.0

        :param shortcut_id: UUID of the shortcut to update
        :type shortcut_id: str
        :param name: New name
        :type name: str
        :param parent: UUID of the new parent folder
        :type parent: str
        :param target: UUID of the new target
        :type target: str
        :param target_type: Type of *target*, one of
                            :py:class:`~ndex2.constants.FileType`
        :type target_type: str
        :param visibility: One of :py:class:`~ndex2.constants.Visibility`
        :type visibility: str
        :raises NDExInvalidParameterError: If no field to update is given,
                                           or a value is invalid
        :raises NDExNotFoundError: If no such shortcut exists
        :raises NDExUnauthorizedError: If write access is denied
        :return: ``None``
        """
        self._http.require_auth()
        require_str(shortcut_id, 'shortcut_id')
        body = {}
        if name is not None:
            body['name'] = require_str(name, 'name')
        if parent is not None:
            body['parent'] = str(parent)
        if target is not None:
            body['target'] = str(target)
        t_type = require_enum(target_type, FileType.ALL, 'target_type')
        if t_type is not None:
            body['targetType'] = t_type
        vis = require_enum(visibility, Visibility.ALL, 'visibility')
        if vis is not None:
            body['visibility'] = vis
        if len(body) == 0:
            raise NDExInvalidParameterError('At least one of name, parent, '
                                            'target, target_type or '
                                            'visibility must be set')
        return self._http.put(SHORTCUTS + '/' + str(shortcut_id),
                              json_body=body)

    def delete_shortcut(self, shortcut_id):
        """
        Deletes a shortcut. Its target is left untouched.

        ``DELETE /v3/files/shortcuts/{shortcutid}``

        .. versionadded:: 3.12.0

        :param shortcut_id: UUID of the shortcut
        :type shortcut_id: str
        :raises NDExNotFoundError: If no such shortcut exists
        :raises NDExUnauthorizedError: If delete access is denied
        :return: ``None``
        """
        self._http.require_auth()
        require_str(shortcut_id, 'shortcut_id')
        return self._http.delete(SHORTCUTS + '/' + str(shortcut_id))

    # ------------------------------------------------------------------
    # trash
    # ------------------------------------------------------------------

    def list_trash(self):
        """
        Lists the authenticated user's trashed items.

        ``GET /v3/files/trash``

        .. versionadded:: 3.12.0

        :raises NDExUnauthorizedError: If no credentials are set
        :return: File item summaries for trashed items
        :rtype: list
        """
        self._http.require_auth()
        result = self._http.get(FILES + '/trash')
        return [] if result is None else result

    def restore(self, networks=None, folders=None, shortcuts=None):
        """
        Restores items from the trash to their previous location.

        ``POST /v3/files/trash/restore``

        .. versionadded:: 3.12.0

        :param networks: UUIDs of networks to restore
        :type networks: list
        :param folders: UUIDs of folders to restore
        :type folders: list
        :param shortcuts: UUIDs of shortcuts to restore
        :type shortcuts: list
        :raises NDExInvalidParameterError: If all three arguments are
                                           omitted, or a list is empty
        :raises NDExUnauthorizedError: If no credentials are set
        :return: ``None``
        """
        self._http.require_auth()
        body = {}
        if networks is not None:
            body['networks'] = require_id_list(networks, 'networks')
        if folders is not None:
            body['folders'] = require_id_list(folders, 'folders')
        if shortcuts is not None:
            body['shortcuts'] = require_id_list(shortcuts, 'shortcuts')
        if len(body) == 0:
            raise NDExInvalidParameterError('At least one of networks, '
                                            'folders or shortcuts must be '
                                            'set')
        return self._http.post(FILES + '/trash/restore', json_body=body)

    def clear_trash(self):
        """
        Permanently deletes everything in the trash. Cannot be undone.

        ``DELETE /v3/files/trash``

        .. versionadded:: 3.12.0

        :raises NDExUnauthorizedError: If no credentials are set
        :return: ``None``
        """
        self._http.require_auth()
        return self._http.delete(FILES + '/trash')

    def delete_permanently(self, item_id):
        """
        Permanently deletes one trashed item. Cannot be undone.

        ``DELETE /v3/files/trash/{uuid}``

        .. versionadded:: 3.12.0

        :param item_id: UUID of the trashed item
        :type item_id: str
        :raises NDExNotFoundError: If the item is not in the trash
        :raises NDExUnauthorizedError: If the caller is not the owner
        :return: ``None``
        """
        self._http.require_auth()
        require_str(item_id, 'item_id')
        return self._http.delete(FILES + '/trash/' + str(item_id))

    # ------------------------------------------------------------------
    # sharing
    # ------------------------------------------------------------------

    def share(self, files, default_type=None):
        """
        Generates public access keys for file items.

        ``POST /v3/files/sharing/share``

        Anyone holding a returned key can read the item by passing it as
        the ``access_key`` argument of the read methods.

        .. versionadded:: 3.12.0

        :param files: Items to share. A ``{uuid: type}`` map, a list of
                      ``(uuid, type)`` pairs, or a list of UUIDs when
                      *default_type* is set.
        :type files: dict or list or str
        :param default_type: :py:class:`~ndex2.constants.FileType` applied
                             to entries that do not carry one
        :type default_type: str
        :raises NDExInvalidParameterError: For invalid arguments
        :raises NDExUnauthorizedError: If the caller does not own an item
        :return: Map of item UUID to its new access key
        :rtype: dict
        """
        self._http.require_auth()
        body = {'files': to_file_map(files, default_type=default_type)}
        return self._http.post(FILES + '/sharing/share', json_body=body)

    def unshare(self, files, default_type=None):
        """
        Revokes the public access keys of file items.

        ``POST /v3/files/sharing/unshare``

        .. versionadded:: 3.12.0

        :param files: Items to unshare, in any form accepted by
                      :py:meth:`share`
        :type files: dict or list or str
        :param default_type: :py:class:`~ndex2.constants.FileType` applied
                             to entries that do not carry one
        :type default_type: str
        :raises NDExInvalidParameterError: For invalid arguments
        :raises NDExUnauthorizedError: If the caller does not own an item
        :return: ``None``
        """
        self._http.require_auth()
        body = {'files': to_file_map(files, default_type=default_type)}
        return self._http.post(FILES + '/sharing/unshare', json_body=body)

    def set_members(self, files, members, default_type=None):
        """
        Grants or changes per-user permissions on file items.

        ``POST /v3/files/sharing/members``

        Granting on a folder covers the items inside it, which is usually
        preferable to granting on each network individually.

        .. versionadded:: 3.12.0

        :param files: Items to share, in any form accepted by
                      :py:meth:`share`
        :type files: dict or list or str
        :param members: Map of user UUID to one of
                        :py:class:`~ndex2.constants.Permissions`
        :type members: dict
        :param default_type: :py:class:`~ndex2.constants.FileType` applied
                             to entries that do not carry one
        :type default_type: str
        :raises NDExInvalidParameterError: For invalid arguments
        :raises NDExUnauthorizedError: If the caller is not authorized to
                                       share an item
        :return: Server response describing the resulting permissions
        :rtype: dict
        """
        self._http.require_auth()
        if not isinstance(members, dict) or len(members) == 0:
            raise NDExInvalidParameterError('members must be a non-empty '
                                            'dict of user UUID to '
                                            'permission')
        member_map = {}
        for user_id, permission in members.items():
            member_map[str(user_id)] = require_enum(str(permission),
                                                    Permissions.ALL,
                                                    'permission',
                                                    allow_none=False)
        body = {'files': to_file_map(files, default_type=default_type),
                'members': member_map}
        return self._http.post(FILES + '/sharing/members', json_body=body)

    def list_members(self, files, default_type=None):
        """
        Lists the users a set of file items is shared with.

        ``POST /v3/files/sharing/members/list``

        .. versionadded:: 3.12.0

        :param files: Items to inspect, in any form accepted by
                      :py:meth:`share`
        :type files: dict or list or str
        :param default_type: :py:class:`~ndex2.constants.FileType` applied
                             to entries that do not carry one
        :type default_type: str
        :raises NDExInvalidParameterError: For invalid arguments
        :raises NDExUnauthorizedError: If the caller is not authorized
        :return: Membership records for the requested items
        :rtype: list
        """
        self._http.require_auth()
        body = to_file_map(files, default_type=default_type)
        result = self._http.post(FILES + '/sharing/members/list',
                                 json_body=body)
        return [] if result is None else result

    def list_shared(self, limit=100):
        """
        Lists file items the authenticated user has shared.

        ``GET /v3/files/sharing/list``

        .. versionadded:: 3.12.0

        :param limit: Maximum number of items to return
        :type limit: int
        :raises NDExUnauthorizedError: If no credentials are set
        :return: File item summaries for shared items
        :rtype: list
        """
        self._http.require_auth()
        result = self._http.get(FILES + '/sharing/list',
                                params={'limit': limit})
        return [] if result is None else result

    # ------------------------------------------------------------------
    # copy, count, visibility, search
    # ------------------------------------------------------------------

    def copy(self, file_id, file_type, target_id, access_key=None):
        """
        Copies a network or shortcut into a folder.

        ``POST /v3/files/copy``

        .. versionadded:: 3.12.0

        :param file_id: UUID of the item to copy
        :type file_id: str
        :param file_type: Type of the item, ``NETWORK`` or ``SHORTCUT``
        :type file_type: str
        :param target_id: UUID of the destination folder
        :type target_id: str
        :param access_key: Access key granting read access to *file_id*
        :type access_key: str
        :raises NDExInvalidParameterError: For invalid arguments
        :raises NDExUnauthorizedError: If access to the source or
                                       destination is denied
        :raises NDExError: If the copy fails, for example on exceeding the
                           disk quota
        :return: UUID of the new copy
        :rtype: str
        """
        self._http.require_auth()
        require_id(file_id, 'file_id')
        require_id(target_id, 'target_id')
        body = {'fileId': str(file_id),
                'type': require_enum(file_type, FileType.ALL, 'file_type',
                                     allow_none=False),
                'targetId': str(target_id)}
        response = self._http.post(FILES + '/copy',
                                   params={'accesskey': access_key},
                                   json_body=body, return_response=True)
        return self._http.uuid_from_created(response)

    def count(self):
        """
        Counts all file items owned by the authenticated user, by type.

        ``GET /v3/files/count``

        .. versionadded:: 3.12.0

        :raises NDExUnauthorizedError: If no credentials are set
        :return: Counts keyed by ``network``, ``folder`` and ``shortcut``
        :rtype: dict
        """
        self._http.require_auth()
        return self._http.get(FILES + '/count')

    def set_visibility(self, visibility, files, default_type=None):
        """
        Sets the visibility of many file items in one request.

        ``POST /v3/batch/files/setvisibility``

        Accepts networks, folders and shortcuts alike, which is why this
        lives here rather than on ``client.networks``.

        .. versionadded:: 3.12.0

        :param visibility: One of :py:class:`~ndex2.constants.Visibility`
        :type visibility: str
        :param files: Items to update, in any form accepted by
                      :py:meth:`share`
        :type files: dict or list or str
        :param default_type: :py:class:`~ndex2.constants.FileType` applied
                             to entries that do not carry one
        :type default_type: str
        :raises NDExInvalidParameterError: For invalid arguments
        :raises NDExUnauthorizedError: If write access is denied
        :return: ``None``
        """
        self._http.require_auth()
        body = {'visibility': require_enum(visibility, Visibility.ALL,
                                           'visibility',
                                           allow_none=False),
                'files': to_file_map(files, default_type=default_type)}
        return self._http.post(BATCH_FILES + '/setvisibility',
                               json_body=body)

    def search(self, search_string='', account_name=None, permission=None,
               file_type=None, visibility=None, start=0, size=100):
        """
        Searches file items.

        ``POST /v3/search/files``

        Covers folders and shortcuts as well as networks, and is the v3
        counterpart to :py:meth:`~ndex2.client.Ndex2.search_networks`.

        .. versionadded:: 3.12.0

        :param search_string: Query text. An empty string matches
                              everything.
        :type search_string: str
        :param account_name: Restrict results to items owned by this
                             account
        :type account_name: str
        :param permission: Restrict results to items on which the caller
                           holds this
                           :py:class:`~ndex2.constants.Permissions` value
        :type permission: str
        :param file_type: Restrict results to one
                          :py:class:`~ndex2.constants.FileType`
        :type file_type: str
        :param visibility: ``PUBLIC`` or ``PRIVATE``. Defaults to
                           ``PUBLIC`` on the server. ``PRIVATE`` requires
                           credentials. ``UNLISTED`` is rejected.
        :type visibility: str
        :param start: Zero-based index of the first result
        :type start: int
        :param size: Maximum number of results
        :type size: int
        :raises NDExInvalidParameterError: For invalid arguments,
                                           including a *visibility* of
                                           ``UNLISTED``
        :raises NDExUnauthorizedError: For a ``PRIVATE`` search with no
                                       credentials
        :return: Results with keys ``numFound``, ``start`` and ``files``
        :rtype: dict
        """
        vis = require_enum(visibility, Visibility.ALL, 'visibility')
        if vis == Visibility.UNLISTED:
            raise NDExInvalidParameterError('visibility of UNLISTED is not a '
                                            'valid search mode; use PUBLIC '
                                            'or PRIVATE')
        if vis == Visibility.PRIVATE:
            self._http.require_auth()

        body = {'searchString': search_string
                if search_string is not None else ''}
        if account_name is not None:
            body['accountName'] = account_name
        perm = require_enum(permission, Permissions.ALL, 'permission')
        if perm is not None:
            body['permission'] = perm
        f_type = require_enum(file_type, FileType.ALL, 'file_type')
        if f_type is not None:
            body['type'] = f_type

        return self._http.post(SEARCH_FILES,
                               params={'visibility': vis,
                                       'start': start,
                                       'size': size},
                               json_body=body)
