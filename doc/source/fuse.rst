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
    mountdir=/chroot

    # if true cubicweb will start automatically a fuse mount per user when the user
    # has some CWSearch entities.
    start_user_fuse=yes

In the 'mountdir' you have to create a hierarchy for each cw user of the form:

::

    -- cw_user_name
            |
            -- instance_name

.. warning::

    Each CW user has to be unix user too (you can use LDAP with CW to
    simplify this step).

Then change the mountdir directory rights, in our example:

::

    sudo chown root:root /chroot
    sudo chown root:root /chroot/cw_user_name
    sudo chmod 755 /chroot
    sudo chown 755 /chroot/cw_user_name

Configure the ssh service of your machine by editing the '/etc/ssh/sshd_config'
configuration file:

::

    Subsystem sftp internal-sftp #/usr/lib/openssh/sftp-server
    Match Group sftp
        ChrootDirectory /chroot/%u
        ForceCommand internal-sftp
        AllowTcpForwarding no
        X11Forwarding no

.. warning::
    
    Sshd will reject SFTP connections from accounts that are set to chroot into
    any directory where ownership/permissions are considered insecure by sshd.

Restart the ssh service:

::

    sudo service ssh restart

If you experience any login issue, check the logs:

::

    tail -20 /var/log/auth.log


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


