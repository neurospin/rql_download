
.. _install_guid:

=========================
Installing `Rql Download`
=========================

This tutorial will walk you through the process of intalling Rql Download...

  * :ref:`Install an official release <install_release>`: this
    is the best approach for users who want a stable version.
  * :ref:`Install the latest development version
    <install_development>`. This is best for users who want to contribute
    to the project.


.. _install_release:

Installing a stable version
==============================

Install the python package with *pip*
-------------------------------------

**Install the package without the root privilege**

>>> pip install --user cwbrowser

**Install the package with the root privilege**

>>> sudo pip install cwbrowser


.. _install_development:

Installing the current version
===============================

Install from *githib*
---------------------

**Clone the project**

>>> cd CLONE_DIR
>>> git clone https://github.com/neurospin/rql_download.git

**Update your PYTHONPATH**

>>> export PYTHONPATH=$CLONE_DIR/rql_download:$PYTHONPATH




