=======
History
=======

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

* Fixed bug where if server version is not 2.0 exactly then Ndex2() object incorrectly falls back to version of 1.3 of REST calls
  `Issue #40 <https://github.com/ndexbio/ndex2-client/issues/40>`_

* Fixed bug in NiceCXNetwork.add_network_attribute() method where type not properly reset when adding duplicate attribute
  `Issue #50 <https://github.com/ndexbio/ndex2-client/issues/50>`_

* Added delete_networksets() method to Ndex2 client to allow deletion of networksets `Issue #59 <https://github.com/ndexbio/ndex2-client/issues/59>`_


3.2.0 (2019-04-23)
------------------

* Verify consistent conversion of cx for networkx 1.11 and 2.0+
  `Issue #30 <https://github.com/ndexbio/ndex2-client/issues/30>`_

* NiceCXNetwork.get_nodes(), NiceCXNetwork.get_edges(), NiceCXNetwork.get_metadata() needs to make correct iterator call in Python 2
  `Issue #44 <https://github.com/ndexbio/ndex2-client/issues/44>`_

* Add NiceCXNetwork.get_network_attribute_names() function enhancement
  `Issue #45 <https://github.com/ndexbio/ndex2-client/issues/45>`_

* NiceCXNetwork.create_edge fails to correctly create edge when node dict passed in
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
