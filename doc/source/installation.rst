
.. _install_guid:

=========================
Installing `Rql Download`
=========================

This tutorial will walk you through the process of intalling Rql Download:
   
    * **CWBrowser**: a pure Python module.
    * **rql_download**: a cube that can only be instanciated
      if `cubicweb is installed <https://docs.cubicweb.org/admin/setup>`_.

Have a look at the :ref:`twisted SFTP server <twisted_how_to>` and :ref:`fuse virtual folders <fuse_how_to>` configurations 


.. _install_cwbrowser:

Installing CWBrowser
====================

Installing a stable version
---------------------------

This is the best approach for users who want a stable version.


Install the python package with *pip*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Install the package without the root privilege**

>>> pip install --user cwbrowser

**Install the package with the root privilege**

>>> sudo pip install cwbrowser


Installing the current version
------------------------------

Install from *github*
~~~~~~~~~~~~~~~~~~~~~

**Clone the project**

>>> cd $CLONEDIR
>>> git clone https://github.com/neurospin/rql_download.git

**Update your PYTHONPATH**

>>> export PYTHONPATH=$CLONE_DIR/rql_download:$PYTHONPATH



.. _install_rqldownload:

Installing rql_download
=======================

Installing the current version
------------------------------

Install from *github*
~~~~~~~~~~~~~~~~~~~~~

**Clone the project**

>>> cd $CLONEDIR
>>> git clone https://github.com/neurospin/rql_download.git

**Update your CW_CUBES_PATH**

>>> export CW_CUBES_PATH=$CLONE_DIR/rql_download:$CW_CUBES_PATH




