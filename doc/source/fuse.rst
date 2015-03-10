:orphan:

####################
Fuse virtual folders
####################

.. _fuse_ref:

Description
-----------

In order to expose the content of CWSearch entities, a process (which can be 
started  automatically by cubicweb) can create a virtual folder with the the
content of the result set associated to the search. The creation of such a
virtual folder requires the cubicweb and system accounts to be the same
(to ease this step, cubicweb is able to work with LDAP).

.. _fuse_how_to:

How to use
----------

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

.. warning::

    Each CW user have to be unix user too (you can use LDAP with CW to
    simplify this step). 


.. _fuse_api:

:mod:`rql_download.fuse`: Fuse virtual folders
----------------------------------------------


Fuse
~~~~

.. currentmodule:: rql_download.fuse

.. autosummary::
    :toctree: generated/twisted/
    :template: class_private.rst

    fuse_mount.VirtualDirectory
    fuse_mount.FuseRset

.. autosummary::
    :toctree: generated/twisted/
    :template: function.rst

    fuse_mount.get_cw_connection
    fuse_mount.get_cw_option


Hooks
~~~~~

.. currentmodule:: rql_download

.. autosummary::
    :toctree: generated/twisted/
    :template: class_private.rst

    hooks.CWSearchFuseMount
    hooks.ServerStartupFuseMount
    hooks.ServerStartupFuseZombiesLoop


Operations
~~~~~~~~~~

.. autosummary::
    :toctree: generated/twisted/
    :template: class_private.rst

    hooks.PostCommitFuseOperation


