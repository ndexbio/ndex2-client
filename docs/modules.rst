Reference
=========

The NDEx2 Python Client can be broken into three parts:

#. :py:class:`~ndex2.nice_cx_network.NiceCXNetwork` provides a data model for
   working networks in `CX format`_

#. :py:class:`~ndex2.cx2.CX2Network` provides a data model for working with
   networks in `CX2 format`_

#. :py:class:`~ndex2.client.Ndex2` REST client provides provides methods to
   interact with `NDEx`_ via the `NDEx REST Service`_

.. note::

   All networks on NDEx_ can be retrieved in newer `CX2 format`_ via
   the `NDEx REST Service`_ and loaded via newer preferred data model
   :py:class:`~ndex2.cx2.CX2Network`

.. toctree::
   :maxdepth: 2

   cx2
   createcx2
   convertcx2
   ndex2
   createnicecx
   convertnicecx
   ndex2client
   miscref

.. _NDEx: http://www.ndexbio.org
.. _`CX format`: https://cytoscape.org/cx/specification/cytoscape-exchange-format-specification-(version-1)
.. _`CX2 format`: https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)
.. _`NDEx REST Service`: https://home.ndexbio.org/using-the-ndex-server-api

