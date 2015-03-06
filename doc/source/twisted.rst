:orphan:

###################
Twisted SFTP server
###################

The exact API of the modules that can be used to create a SFTP server to access
search result sets of a cubicweb instance.

.. _twisted_how_to:

User Guide
==========

During the rql download instanciation or in your instance all-in-one.conf file,
set the following options to activate the Twister SFTP server that will expose
the content of each CW searche:

::

    [RQL_DOWNLOAD]
    # specifies expiration delay of CWSearch (in days)
    default_expiration_delay=1

    # base directory in which files are stored (this option is given to the ftp
    # server and fuse processes)
    basedir=/tmp

    # if true cubicweb will start automatically sftp server (you need to set
    # properly the configuration file: see the documentation)
    start_sftp_server=yes

Execute the 'main.py' script of the 'twistedserver' module. This script can
be parametrized from the command line or from a file with the following synthax:

::

    [rsetftp]
    cubicweb-instance=instance_name1:instance_name2
    port=9191

This configuration file default location is '~/.config/rsetftp' but can be
tuned via the 'config-file' option.

All the script options are:

- cubicweb-instance: the name of the instance (or instances separated by ':')
  the ftp server will connect. This instance must inherit from the rql_download
  schema.
- unix-username: the name of a valid unix user.
- private-key: the path to a private key file as generated with ssh-keygen.
- public-key: the path to a public key file as generated with ssh-keygen.
- passphrase: the password associated with the previous public/provate key.
- port: the server listening port.
- config-file: the path to a configuration file.

The user who lunch the 'main.py' script needs to have at least the read access
on the files we want to transfer through the ftp server.

.. _twisted_ref:

:mod:`rql_download.twistedserver`: SFTP server
===============================================


.. currentmodule:: rql_download

Hooks
------

.. autosummary::
    :toctree: generated/twisted/
    :template: class.rst

    hooks.LaunchTwistedFTPServer


.. currentmodule:: rql_download.twistedserver

Twisted
--------

.. autosummary::
    :toctree: generated/twisted/
    :template: class.rst

    server.VirtualPathTranslator
    server.CubicWebConchUser
    server.Search
    server.CubicWebCredentialsChecker
    server.CubicWebSFTPRealm
    server.CubicWebSSHdFactory
    server.CubicWebProxiedSFTPServer
    server.CubicwebFile
