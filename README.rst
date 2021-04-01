**NDEx2 Python Client**
=========================

.. _NDEx: http://ndexbio.org
.. _NDEx REST Server API: http://www.home.ndexbio.org/using-the-ndex-server-api

.. image:: https://img.shields.io/travis/ndexbio/ndex2-client.svg
        :target: https://travis-ci.org/ndexbio/ndex2-client.svg?branch=master

.. image:: https://img.shields.io/pypi/v/ndex2.svg
        :target: https://pypi.python.org/pypi/ndex2

.. image:: https://coveralls.io/repos/github/ndexbio/ndex2-client/badge.svg?branch=master
        :target: https://coveralls.io/github/ndexbio/ndex2-client?branch=master

.. image:: https://readthedocs.org/projects/ndex2/badge/?version=latest
        :target: https://ndex2.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


**Overview**
--------------

The NDEx2 Python Client provides methods to access NDEx_ via
the `NDEx REST Server API`_. As well as methods for common operations on
networks via the NiceCXNetwork class.

**Dependencies**
---------------------

* `six <https://pypi.org/project/six>`__
* `ijson <https://pypi.org/project/ijson>`__
* `requests <https://pypi.org/project/requests>`__
* `requests_toolbelt <https://pypi.org/project/requests_toolbelt>`__
* `networkx <https://pypi.org/project/networkx>`__
* `urllib3 <https://pypi.org/project/urllib3>`__
* `pandas <https://pypi.org/project/pandas>`__
* `enum34 <https://pypi.org/project/enum34>`__ (Python < 3.4)
* `numpy <https://pypi.org/project/numpy>`__
* `enum <https://pypi.org/project/enum>`__ (Python 2.6 & 2.7)

**Compatibility**
-----------------------

Python 2.7+

.. note::

    Python 2.7 may have some issues, Python 3.6+ is preferred

**Installation**
--------------------------------------

The NDEx2 Python Client module can be installed from the Python Package
Index (PyPI) repository using PIP:

::

    pip install ndex2

If you already have an older version of the ndex2 module installed, you
can use this command instead:

::

    pip install --upgrade ndex2


**License**
--------------------------------------

See `LICENSE.txt <https://github.com/ndexbio/ndex2-client/blob/master/LICENSE.txt>`_


