Quick Tutorial
================

Download network from `NDEx <https://ndexbio.org>`__
-------------------------------------------------------

The code blocks below uses the `NDEx2 Python client <https://pypi.org/ndex2-client>`_ to download
`BioGRID: Protein-Protein Interactions (SARS-CoV) <http://ndexbio.org/viewer/networks/669f30a3-cee6-11ea-aaef-0ac135e8bacf>`_
network from `NDEx <https://ndexbio.org>`_ as a `NiceCXNetwork <https://ndex2.readthedocs.io/en/latest/ndex2.html#nicecxnetwork>`_.

The number of nodes and edges are then printed out and the network is converted to `Networkx <https://networkx.org>`__
object.


.. code-block:: python

    import json
    import ndex2


    # Create NDEx2 python client
    client = ndex2.client.Ndex2()

    # Download BioGRID: Protein-Protein Interactions (SARS-CoV) from NDEx
    # http://ndexbio.org/viewer/networks/669f30a3-cee6-11ea-aaef-0ac135e8bacf
    client_resp = client.get_network_as_cx_stream('669f30a3-cee6-11ea-aaef-0ac135e8bacf')

    # Convert downloaded network to NiceCXNetwork object
    net_cx = ndex2.create_nice_cx_from_raw_cx(json.loads(client_resp.content))

    # Display information about network and output 1st 100 characters of CX
    print('Name: ' + net_cx.get_name())
    print('Number of nodes: ' + str(len(list(net_cx.get_nodes()))))
    print('Number of nodes: ' + str(len(list(net_cx.get_edges()))))
    print(json.dumps(net_cx.to_cx())[0:100])

    # Create Networkx network
    g = net_cx.to_networkx(mode='default')

    print('Name: ' + str(g))
    print('Number of nodes: ' + str(g.number_of_nodes()))
    print('Number of edges: ' + str(g.number_of_edges()))
    print('Network annotations: ' + str(g.graph))


More Tutorials and Examples
-------------------------------------------------

*  Basic Use of the NDEx2 Python Client:  `NDEx2 Client v2.0
   Tutorial <https://github.com/ndexbio/ndex-jupyter-notebooks/blob/master/notebooks/NDEx2%20Client%20v2.0%20Tutorial.ipynb>`__
*  Working with the NiceCX Network Class: `NiceCX v2.0
   Tutorial <https://github.com/ndexbio/ndex-jupyter-notebooks/blob/master/notebooks/NiceCX%20v2.0%20Tutorial.ipynb>`__

To use these tutorials or if Github isn't showing the above notebooks in the browser, clone the `ndex-jupyter-notebooks
repository <https://github.com/ndexbio/ndex-jupyter-notebooks>`__ to
your local machine and start Jupyter Notebooks in the project directory.

For information on installing and using Jupyter Notebooks, go to
`jupyter.org <http://jupyter.org/>`__

* `Click here <https://github.com/ndexcontent/ndexncipidloader>`__ for example code to load content into `NDEx`_