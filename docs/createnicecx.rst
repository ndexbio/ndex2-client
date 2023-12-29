Creating NiceCXNetwork objects
-------------------------------------------------

.. note::

    Using the newer data model :py:class:`~ndex2.cx2.CX2Network`
    is encouraged since all networks on NDEx_ can be retrieved in newer `CX2 format`_ via
    the `NDEx REST Service`_


.. automodule:: ndex2
    :members: create_nice_cx_from_raw_cx, create_nice_cx_from_file, create_nice_cx_from_server

`Networkx <https://networkx.org/>`__
=======================================

.. automodule:: ndex2
    :members: create_nice_cx_from_networkx
    :noindex:

`Pandas <https://pandas.pydata.org>`__
============================================

.. automodule:: ndex2
    :members: create_nice_cx_from_pandas
    :noindex:

.. _NDEx: https://www.ndexbio.org
.. _`CX format`: https://cytoscape.org/cx/specification/cytoscape-exchange-format-specification-(version-1)
.. _CX: https://cytoscape.org/cx/specification/cytoscape-exchange-format-specification-(version-1)
.. _`CX2 format`: https://cytoscape.org/cx/cx2/specification/cytoscape-exchange-format-specification-(version-2)
.. _`NDEx REST Service`: https://home.ndexbio.org/using-the-ndex-server-api
