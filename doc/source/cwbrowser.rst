:orphan:

#########
CWBROWSER
#########

.. _cwbrowser_ref:

A Python module is proposed to script the RQL requests. It enables us to
access information stored in a CubicWeb database, through two methods 'execute'
and 'execute_with_sync'. The first method simply executes a RQL from the script
while the second one creates a :ref:`search <views_ref>`, then it contacts the
server where the CW instance is running through the sftp protocol using
paramiko in order to download the search associated dataset. This second method
assumes that the :ref:`Twisted server <twisted_ref>` solution or the
:ref:`Fuse virtual folders <fuse_ref>` solution has been deployed on the server.

.. warning::

    If you use fuse to retrieve the search associated dataset (using the
    'execute_with_sync' method), the CW user must have specific rights
    (ie. must be a simple user).

.. _cwbrowser_api:


.. currentmodule:: cwbrowser

:mod:`cwbrowser`: cw_connection
-------------------------------

Connection definition
~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: generated/cwbrowser/
    :template: class_private.rst

    cw_connection.CWInstanceConnection

Exporter
~~~~~~~~

.. autosummary::
    :toctree: generated/cwbrowser/
    :template: function.rst

    cw_connection.load_csv
