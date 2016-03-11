
.. _install_guid:

=========================
Installing `Rql Download`
=========================

This tutorial will walk you through the process of intalling Rql Download:
   
    * **CWBrowser**: a pure Python module.
    * **rql_download**: a cube that can only be instanciated
      if `Cubicweb is installed <https://docs.cubicweb.org/admin/setup>`_.

Have a look at the :ref:`twisted SFTP server <twisted_how_to>` and
:ref:`fuse virtual folders <fuse_how_to>` configurations.


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

Make sure the cube is in CubicWeb's path
----------------------------------------

>>> cubicweb-ctl list

Create an instance of the cube
------------------------------

>>> cubicweb-ctl create rql_download toy_instance

You can then run the instance in debug mode:

>>> cubicweb-ctl start -D toy_instance

The last line of the prompt will indicate which url the 
instance can be reached by:

>>> (cubicweb.twisted) INFO: instance started on http://url:port/

Change configuration
--------------------

The configuration file is stored on your system:

>>> ...etc/cubicweb.d/toy_instance/all-in-one.conf




