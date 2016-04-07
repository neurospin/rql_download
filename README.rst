============
RQL_download
============

Summary
=======

Cube to download a complete subset of data via SFTP (two strategies proposed) and remotely query the database.
Check `this link <https://neurospin.github.io/rql_download/>`_ for the complete
documentation.

Content
=======

CW_Browser
----------

This module allows remote quering in the database. It's available on pypi:

- |latest_version|
- |Development_Status|
- |License|

It provides meethods to script requests to a cubicweb database and inherits from the rql_download cube.

.. |latest_version| image:: https://pypip.in/version/cwbrowser/badge.png
                        :target: https://pypi.python.org/pypi/cwbrowser/
                        :alt: Latest Version
    
.. |Development_Status| image:: https://pypip.in/status/cwbrowser/badge.png
                            :target: https://pypi.python.org/pypi/cwbrowser/
                            :alt: Development Status

.. |License| image:: https://pypip.in/license/cwbrowser/badge.png
                 :target: https://pypi.python.org/pypi/cwbrowser/
                 :alt: License


RQL_download
------------

This module allows to setup a SFTP service on the server hosting your database. Thus, all query results are accessible (we use the python_fuse_ package or Twisted_ to build the filesystem) through a predefinite SFTP repository. Users can then access and download their data using the SFTP protocol.

.. _Twisted: https://pypi.python.org/pypi/Twisted
.. _python_fuse: https://pypi.python.org/pypi/fuse-python
