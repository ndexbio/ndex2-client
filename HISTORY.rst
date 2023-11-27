=======
History
=======

3.6.0 (2023-11-14)
-------------------

* Enhancements
    * Added ``CX2Network`` class under ``cx2.py`` module to represent networks `CX2 format <https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)/>`__
    * Added ``RawCX2NetworkFactory`` class under ``cx2.py`` to create ``CX2Network`` objects
    * Added ``NoStyleCXToCX2NetworkFactory`` class under ``cx2.py`` to convert ``NiceCXNetwork`` to ``CX2Network``

* Bug fixes
    * Fixed SyntaxWarnings `Issue #92 <https://github.com/ndexbio/ndex2-client/issues/92>`__

3.5.1 (2023-04-11)
-------------------

* Bug fixes
    * Fixed bug where ``ndex2.create_nice_cx_from_networkx()`` fails with numpy version 1.24
      `Issue #96 <https://github.com/ndexbio/ndex2-client/issues/96>`__
    * Updated post and put calls in ``client.py`` to only pass credentials if they are
      set. This change is to accommodate changes in upcoming version 3 of requests library

3.5.0 (2022-06-28)
-------------------

* Enhancements
    * Added **skip_version_check** parameter to ``Ndex2()`` constructor to let caller
      optionally bypass NDEx server call to see if **v2** endpoint is supported

    * Added the following *CX2* methods to ``Ndex2()`` client:
      ``get_network_as_cx2_stream()``, ``get_network_aspect_as_cx2_stream()``,
      ``save_cx2_stream_as_new_network()``,
      ``save_new_cx2_network()``, and ``update_cx2_network()``
      `Issue #87 <https://github.com/ndexbio/ndex2-client/issues/87>`__

    * In ``Ndex2()`` client, methods that raise ``NDExError`` exceptions from calls
      to NDEx server will now raise the more specific ``NDExUnauthorizedError``
      subclass when the response from NDEx server is a 401 aka unauthorized.

    * Added new parameters **dataconverter** and **include_attributes** to ``NiceCXNetwork.to_pandas_dataframe()``.
      **dataconverter** parameter specifies data type conversion and **include_attributes** parameter lets
      caller specify whether all node/edge attributes are added to the resulting DataFrame

    * Added new parameter to ``ndex2.create_nice_cx_from_server()`` named **ndex_client**
      that lets caller specify ``NDex2()`` client object to use.

    * Passing ``None`` for the **server** positional parameter into ``ndex2.create_nice_cx_from_server(None, uuid='XXXX')`` will default to the production
      NDEx server

* Bug fixes
    * Fixed bug where creation of `NiceCXNetwork` from networkx via ``ndex2.create_nice_cx_from_networkx()``
      incorrectly set the data type for boolean values to integer.
      Issue `#83 <https://github.com/ndexbio/ndex2-client/issues/83>`__

    * Fixed bug where converting `NiceCXNetwork` to networkx and back does not handle
      name attribute correctly. `Issue #84 <https://github.com/ndexbio/ndex2-client/issues/84>`__

    * Fixed bug where `@context` was lost if it was set as aspect in CX format and loaded
      into NiceCXNetwork object.
      `Issue #88 <https://github.com/ndexbio/ndex2-client/issues/88>`__

    * Fixed bug where creation of `NiceCXNetwork` from networkx via ``ndex2.create_nice_cx_from_networkx()``
      incorrectly set the data type for empty list to string.
      Issue `#90 <https://github.com/ndexbio/ndex2-client/issues/90>`__

    * Fixed bug where Y coordinates of nodes would be inverted when converting to/from
      networkx from `NiceCXNetwork`. This was due to differences in coordinate systems
      between networkx and `NiceCXNetwork`

    * `DefaultNetworkXFactory` networkx converter (used by ``NiceCXNetwork.to_networkx(mode='default')``)
      no longer converts edge attributes that are of type list into strings delimited by
      commas

    * Fixed bug where ``ndex2.create_nice_cx_from_server()`` failed on networks
      with `provenanceHistory` aspect

* Removals
    * Removed unused test methods from internal class `NiceCXBuilder`:
      ``load_aspect()``, ``stream_aspect()``, ``stream_aspect_raw()``

    * Removed the following deprecated methods from `NiceCXNetwork`:
      ``add_node()``, ``add_edge()``, ``get_edge_attribute_object()``,
      ``get_node_attribute_objects()``, ``get_edge_attribute_objects()``,
      ``add_metadata()``, ``get_provenance()``, ``set_provenance()``,
      ``__merge_node_attributes()``, ``create_from_pandas()``,
      ``create_from_networkx()``, ``create_from_server()``, ``upload_new_network_stream()``, &
      ``create_from_cx()``


3.4.0 (2021-05-06)
-------------------

* Added **offset** and **limit** parameters to `Ndex2.get_network_ids_for_user()` to enable
  retrieval of all networks for a user.
  `Issue #78 <https://github.com/ndexbio/ndex2-client/issues/78>`__

* Switched `NiceCXNetwork.upload_to()` to named arguments and added **client** parameter.
  `Issue #80 <https://github.com/ndexbio/ndex2-client/issues/80>`__

* Switched `NiceCXNetwork.update_to()` to named arguments and added **client** parameter.
  `Issue #81 <https://github.com/ndexbio/ndex2-client/issues/81>`__

* Fixed documentation `NiceCXNetwork.update_to()` to correctly state method returns empty
  string upon success.
  `Issue #82 <https://github.com/ndexbio/ndex2-client/issues/82>`__

* Fixed bug in `NiceCXNetwork.set_opaque_aspect()` where passing `None` in the **aspect_elements**
  parameter raised an error instead of removing the aspect

* Added `Ndex2.get_user_by_id()` method to get user information by NDEx user Id.

* Added `Ndex2.get_id_for_user()` method to get NDEx user Id by username.

* Added `Ndex2.get_networksets_for_user_id()` to get Network Sets for a given user Id.
  `Issue #61 <https://github.com/ndexbio/ndex2-client/issues/61>`__

* Improved documentation by adding intersphinx to provide links to python documentation for
  python objects.

3.3.3 (2021-04-22)
-------------------

* Fixed bug where `NiceCXNetwork.to_networkx()` fails with `ValueError` when installed
  networkx version has X.Y.Z format (example: 2.5.1)
  `Issue #79 <https://github.com/ndexbio/ndex2-client/issues/79>`_

3.3.2 (2021-04-13)
-------------------

* Fixed bug where `NiceCXNetwork.create_node()` and `.create_edge()` overwrote existing nodes/edges.
  `Issue #60 <https://github.com/ndexbio/ndex2-client/issues/60>`_

* Fixed bug where `enum34` package would be unnecessarily installed on versions of Python 3.4 and newer.
  `Issue #76 <https://github.com/ndexbio/ndex2-client/issues/76>`_

* Improved documentation for `Ndex2.set_network_properties()` method.
  `Issue #77 <https://github.com/ndexbio/ndex2-client/issues/77>`_

3.3.1 (2019-09-23)
-------------------

* Added `MANIFEST.in` file to include `README.rst, HISTORY.rst, and LICENSE.txt` files as well as documentation and tests so `python setup.py install` will work properly on distribution of this client on PyPI. Thanks to Ben G. for catching this. `Issue #62 <https://github.com/ndexbio/ndex2-client/pull/62>`_

* Minor updates to `README.rst`

3.3.0 (2019-09-11)
------------------

* Fixed bug where if server version is not 2.0 exactly then `Ndex2()` object incorrectly falls back to version of 1.3 of REST calls
  `Issue #40 <https://github.com/ndexbio/ndex2-client/issues/40>`_

* Fixed bug in `NiceCXNetwork.add_network_attribute()` method where type not properly reset when adding duplicate attribute
  `Issue #50 <https://github.com/ndexbio/ndex2-client/issues/50>`_

* Added `delete_networksets()` method to Ndex2 client to allow deletion of networksets `Issue #59 <https://github.com/ndexbio/ndex2-client/issues/59>`_


3.2.0 (2019-04-23)
------------------

* Verify consistent conversion of CX for networkx 1.11 and 2.0+
  `Issue #30 <https://github.com/ndexbio/ndex2-client/issues/30>`_

* `NiceCXNetwork.get_nodes()`, `NiceCXNetwork.get_edges()`, `NiceCXNetwork.get_metadata()` needs to make correct iterator call in Python 2
  `Issue #44 <https://github.com/ndexbio/ndex2-client/issues/44>`_

* Add `NiceCXNetwork.get_network_attribute_names()` function enhancement
  `Issue #45 <https://github.com/ndexbio/ndex2-client/issues/45>`_

* `NiceCXNetwork.create_edge()` fails to correctly create edge when node dict passed in
  `Issue #46 <https://github.com/ndexbio/ndex2-client/issues/46>`_

3.1.0a1 (2019-03-20)
--------------------

* Add method to ndex2 python client to apply style from one NiceCXNetwork 
  to another NiceCXNetwork
  `Issue #43 <https://github.com/ndexbio/ndex2-client/issues/43>`_

3.0.0a1 (2019-02-11)
--------------------

* In NiceCXNetwork class ability to add to User-Agent for calls to NDEx service
  `Issue #36 <https://github.com/ndexbio/ndex2-client/issues/36>`_

* Methods in `ndex2/client.py` should raise an NDExError for invalid credentials
  `Issue #39 <https://github.com/ndexbio/ndex2-client/issues/39>`_

* Add timeout flag to all web request calls
  `Issue #33 <https://github.com/ndexbio/ndex2-client/issues/33>`_

* Update `User-Agent` to reflect actual version of software
  `Issue #35 <https://github.com/ndexbio/ndex2-client/issues/35>`_

* `NiceCXNetwork.set_node_attribute()` incorrectly handles duplicate attributes
  `Issue #41 <https://github.com/ndexbio/ndex2-client/issues/41>`_

* `NiceCXNetwork.set_node_attribute()` fails if node object passed to it
  `Issue #42 <https://github.com/ndexbio/ndex2-client/issues/42>`_

* Passing None to user_agent parameterin `Ndex2()` constructor raises TypeError
  `Issue #34 <https://github.com/ndexbio/ndex2-client/issues/34>`_

* `Ndex2()` constructor does not properly handle invalid json from server
  `Issue #28 <https://github.com/ndexbio/ndex2-client/issues/28>`_

* Eliminate circular import between ndex2 and ndex2cx/nice_cx_builder.py
  `Issue #31 <https://github.com/ndexbio/ndex2-client/issues/31>`_

* Replace print statements with logging calls in `ndex2/client.py`
  `Issue #32 <https://github.com/ndexbio/ndex2-client/issues/32>`_


2.0.1 (2019-01-03)
------------------

* Fixed bug where logs directory is created within
  the package installation directory. 
  `Issue #26 <https://github.com/ndexbio/ndex2-client/issues/26>`_
