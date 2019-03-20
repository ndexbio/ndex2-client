=======
History
=======

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
