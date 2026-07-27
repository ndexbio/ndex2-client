# Migrating from `Ndex2` to `Ndex3`

The v3 REST API replaces the flat *network set* model with a **file system**. Every
item a user owns is a file item of type `NETWORK`, `FOLDER` or `SHORTCUT`. Folders
nest arbitrarily; shortcuts let one item appear in several folders. Groups are gone
entirely — per-user sharing replaces them.

```python
from ndex2.client_v3 import Ndex3, FileType, Visibility, Permissions

client = Ndex3(host='https://www.ndexbio.org',
               username='bob', password='secret')
```

`Ndex3` subclasses `Ndex2`, so inherited CX2 network I/O still works. Methods with no
v3 equivalent raise `NDExUnsupportedCallError` on `Ndex3` and emit a
`DeprecationWarning` on `Ndex2`.

## Network sets become folders

| `Ndex2` (v2) | `Ndex3` (v3) |
| --- | --- |
| `create_networkset(name, description)` | `create_folder(name, description=..., parent=...)` |
| `get_networkset(id)` / `get_network_set(id)` | `get_folder(id)` plus `list_folder_items(id)` |
| `get_networksets_for_user_id(user_id)` | `list_folders()`, or `get_user_home(user_id)` to start at the root |
| `delete_networkset(id)` | `delete_folder(id, force=..., permanent=...)` |
| `add_networks_to_networkset(id, networks)` | `move_networks_to_folder(id, networks)` |
| `delete_networks_from_networkset(id, networks)` | `move_networks_to_folder(other_id, networks)` |

The last row is the one behavioural difference worth pausing on. A network belonged to
zero or more network sets, so removal was meaningful on its own. A network now lives in
exactly one folder, so there is nothing to remove it *to* except another folder. If you
relied on a network appearing in several sets, create a `SHORTCUT` in each additional
folder instead:

```python
folder_id = client.create_folder('My Pathways')
client.move_networks_to_folder(folder_id, [network_id])

# same network, second location
other = client.create_folder('Shared With Lab')
client.create_shortcut('BRCA pathway', network_id, FileType.NETWORK, parent=other)
```

You can also skip the move entirely and create the network in place:

```python
network_id = client.save_new_cx2_network_in_folder(cx, folder_id=folder_id)
```

## Groups become per-user sharing

| `Ndex2` (v2) | `Ndex3` (v3) |
| --- | --- |
| `update_network_group_permission(gid, nid, perm)` | `set_sharing_members({nid: FileType.NETWORK}, {user_id: perm})` |
| `grant_networks_to_group(gid, nids, perm)` | `set_sharing_members(nids, {user_id: perm}, default_type=FileType.NETWORK)` |
| `search_networks(..., include_groups=True)` | `search_files(...)` — no group concept |

There is no group object in v3, so a group grant has to be expanded into the individual
users who were members of that group. Enumerate them from the v2 API before you cut
over, or use folder-level sharing so a single grant covers everything inside:

```python
client.set_sharing_members({folder_id: FileType.FOLDER},
                           {alice_id: Permissions.WRITE,
                            bob_id: Permissions.READ})
```

Public access keys are separate from member permissions. `share_files` mints a key that
any holder can read with; the read methods accept it as `access_key`:

```python
keys = client.share_files({network_id: FileType.NETWORK})
summary = client.get_network_summary(network_id, access_key=keys[network_id])
```

## Search

`search_networks` and `find_networks` are replaced by `search_files`, which covers all
three file types and returns `{'numFound': ..., 'start': ..., 'files': [...]}`.

```python
res = client.search_files('BRCA', file_type=FileType.NETWORK,
                          visibility=Visibility.PUBLIC, start=0, size=50)
print(res['numFound'])
```

Note that `visibility=Visibility.UNLISTED` is rejected — the server treats it as a
400, and the client raises `NDExInvalidParameterError` before the request goes out.
A `PRIVATE` search requires credentials.

## Network queries moved and now return CX2

The v2 search routes were renamed from `/search/network/{id}/...` to
`/search/networks/{id}/...` — singular to plural. They still exist, but serve CX2
rather than CX, so the CX-named methods raise rather than silently handing back a
different format under a name that promises CX.

| `Ndex2` (v2) | `Ndex3` (v3) |
| --- | --- |
| `get_neighborhood_as_cx_stream(...)` | `query_network_as_cx2_stream(...)` |
| `get_neighborhood(...)` | `query_network_as_cx2_stream(...)` |
| `get_interconnectquery_as_cx_stream(...)` | `interconnect_query_as_cx2_stream(...)` |
| `get_interconnectquery(...)` | `interconnect_query_as_cx2_stream(...)` |
| `search_network_nodes(...)` | `get_node_attributes(...)` |

The request bodies are unchanged, so porting is mostly a rename:

```python
res = client.query_network_as_cx2_stream(network_id, 'BRCA1',
                                        search_depth=2, edge_limit=1000)
cx2 = res.json()
```

## Calls that carry over unchanged

These keep their v2 names and signatures on `Ndex3` — they are reimplemented
against v3 endpoints, so existing code needs no edit:

| Method | Now goes through |
| --- | --- |
| `make_network_public` / `make_network_private` | `POST /v3/batch/files/setvisibility` |
| `update_network_user_permission` | `POST /v3/files/sharing/members` |
| `grant_networks_to_user` | `POST /v3/files/sharing/members`, one batched request |
| `grant_network_to_user_by_username` | user lookup, then the above |
| `get_id_for_user` | `GET /v3/users?username=` |

## Calls with no v3 equivalent

These raise `NDExUnsupportedCallError`. The v3 API serves no replacement
endpoint, so these need a design decision rather than a rename:

| Method | Situation |
| --- | --- |
| `get_network_as_cx_stream`, `get_network_aspect_as_cx_stream`, `save_cx_stream_as_new_network`, `save_new_network`, `update_cx_network` | v3 is CX2-only; use the `_cx2_` equivalents |
| `get_task_by_id` | no task service in v3 |
| `get_provenance`, `set_provenance` | provenance aspect dropped |
| `get_sample_network`, `set_network_sample` | no sample endpoint; `get_network_summary` still reports `hasSample` |
| `set_read_only` | reported by `get_network_summary`, not settable |
| `set_network_system_properties` | visibility via `set_file_visibility`; `showcase`, `index_level`, `readOnly` have no equivalent |
| `set_network_properties`, `update_network_profile` | v3 updates a network by replacing its CX2; use `update_cx2_network` |
| `get_user_by_id` | v3 looks users up by account name |
| `get_user_network_summaries`, `get_network_summaries_for_user`, `get_network_ids_for_user` | use `get_user_home` or `search_files(account_name=...)` |

## Network creation returns a UUID, not a URL

`Ndex2.save_new_cx2_network` and `Ndex2.save_cx2_stream_as_new_network` return the
full URL of the new network. On `Ndex3` all three CX2 save methods return the
**UUID** instead, since that is what every other call wants as input. Pass
`return_url=True` for the old behaviour.

```python
uuid = client.save_new_cx2_network(cx)                    # 'abc-123-...'
url  = client.save_new_cx2_network(cx, return_url=True)   # 'https://.../v3/networks/abc-123-...'

# saves a round trip if you already know the destination folder
uuid = client.save_new_cx2_network_in_folder(cx, folder_id=folder_id)
```

If you have code doing `save_new_cx2_network(cx).split('/')[-1]`, drop the split.

## Deletion is now soft by default

`delete_network` and `delete_folder` move items to a trash the user can inspect and
restore from. Pass `permanent=True` to bypass it.

```python
client.delete_network(network_id)             # recoverable
client.restore_from_trash(networks=[network_id])
client.delete_network(network_id, permanent=True)   # not recoverable
```

`delete_folder` also refuses to delete a folder that still has children unless you pass
`force=True`.

## Passing file items to the sharing and visibility calls

Any method that takes a `files` argument accepts three shapes. Pick whichever reads
best at the call site:

```python
client.share_files({nid: FileType.NETWORK, fid: FileType.FOLDER})   # explicit map
client.share_files([(nid, FileType.NETWORK), (fid, FileType.FOLDER)])  # pairs
client.share_files([nid, other_nid], default_type=FileType.NETWORK)    # uniform type
```

Omitting the type with no `default_type` set raises `NDExInvalidParameterError` rather
than guessing.

## Authentication

Basic auth still works against v3. An OAuth/Keycloak id token is also accepted:

```python
client = Ndex3(host=host, bearer_token=id_token)
# or, to exchange a token and fetch the user record in one step
client = Ndex3(host=host)
user = client.signin(id_token)
```

## Walking a user's content

There is no single "list everything" call. Start at the home directory, which returns
the items with no parent, then recurse:

```python
def walk(client, items, depth=0):
    for item in items:
        print('  ' * depth + item['name'] + ' [' + item['type'] + ']')
        if item['type'] == FileType.FOLDER:
            walk(client, client.list_folder_items(item['uuid']), depth + 1)

user = client.get_user_by_username('bob')
walk(client, client.get_user_home(user['externalId']))
```

## Verifying against a live server

`scripts/v3_smoke_test.py` exercises the whole surface against a real NDEx v3
server — folders, nesting, network placement, moves, shortcuts, copies,
visibility, access keys, search, queries, trash and workspaces. It names
everything with a timestamped `zz-v3-smoke` prefix and pauses before cleanup so
the result can be checked in the web UI.

```bash
export NDEX_USER=your_account
export NDEX_PASS=your_password
python scripts/v3_smoke_test.py --host https://dev3.ndex.ucsd.edu/rest
```
