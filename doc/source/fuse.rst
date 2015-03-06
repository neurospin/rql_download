:orphan:

####################
Fuse virtual folders
####################

The exact API of the modules that can be used to create virtual folders exposing
search result sets of a cubicweb instance.

.. _fuse_how_to:

User Guide
==========


During the rql download instanciation or in your instance all-in-one.conf file,
set the following options to activate the Fuse virtual folders creation from
CW searches:

::

    [RQL_DOWNLOAD]
    # specifies expiration delay of CWSearch (in days)
    default_expiration_delay=1

    # base directory in which files are stored (this option is given to the ftp
    # server and fuse processes)
    basedir=/tmp

    # base directory in which fuse will mount the user virtual directoies
    mountdir=/home/toto/tmp/fuse

    # if true cubicweb will start automatically a fuse mount per user when the user
    # has some CWSearch entities.
    start_user_fuse=yes

In the 'mountdir' you have to create a hierarchy for each cw user of the form:

::

    -- cw user name
            |
            -- rql_download
                    |
                    -- instance_name

Each CW user have to be unix user too (you can use ldap with CW to simplify this
step). 


.. _fuse_ref:

:mod:`rql_download.fuse`: Fuse virtual folders
==============================================


.. currentmodule:: rql_download

Hooks
------

.. autosummary::
    :toctree: generated/twisted/
    :template: class.rst

    hooks.CWSearchFuseMount
    hooks.ServerStartupFuseMount
    hooks.ServerStartupFuseZombiesLoop


Operations
----------

.. autosummary::
    :toctree: generated/twisted/
    :template: class.rst

    hooks.PostCommitFuseOperation


.. currentmodule:: rql_download.fuse

Fuse
----

.. autosummary::
    :toctree: generated/twisted/
    :template: class.rst

    fuse_mount.VirtualDirectory
    fuse_mount.FuseRset

.. autosummary::
    :toctree: generated/twisted/
    :template: function.rst

    fuse_mount.get_cw_connection
    fuse_mount.get_cw_option


