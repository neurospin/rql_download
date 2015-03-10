:orphan:

###################
Twisted SFTP server
###################

.. _twisted_ref:

Description
-----------
In order to expose the content of CWSearch entities, a process (which can be 
started  automatically by cubicweb) can shows the stored file paths via sftp
protocol. The authentication in this process is delegated to cubicweb.


.. _twisted_how_to:

How to use
----------
To use this cube implement an :ref:`adapter <views_api>` derived from the
'BaseIDownloadAdapter' for the entity you want to expose via the sftp server. 

During the rql download instanciation or in your instance all-in-one.conf file,
set the following options to activate the Twister SFTP server that will expose
the content of each CW search:

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

Execute the 'main.py' script of the 'twistedserver' module if you decide to
start the server manually. 

This latter can be parametrized from the command line or from a file with the
following syntax:

::

    [rsetftp]
    cubicweb-instance=instance_name1:instance_name2
    port=9191
    private−key=$HOME/ssh/idrsa
    public−key=$HOME/ssh/idrsa.pub
    unix−username=me

This configuration file default location is '~/.config/rsetftp' but can be
set explicitely via the 'config-file' option.

All the 'main.py' script options are:

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
on the files he wants to transfer through the sftp server.


.. _twisted_api:

:mod:`rql_download.twistedserver`: SFTP server
----------------------------------------------


.. currentmodule:: rql_download.twistedserver

Main
~~~~

.. autosummary::
    :toctree: generated/twisted/
    :template: class_private.rst

    main.RsetSFTPCommand

Twisted
~~~~~~~

.. autosummary::
    :toctree: generated/twisted/
    :template: class_private.rst

    server.VirtualPathTranslator
    server.CubicWebConchUser
    server.Search
    server.CubicWebCredentialsChecker
    server.CubicWebSFTPRealm
    server.CubicWebSSHdFactory
    server.CubicWebProxiedSFTPServer
    server.CubicwebFile


.. currentmodule:: rql_download

Hooks
~~~~~

.. autosummary::
    :toctree: generated/twisted/
    :template: class_private.rst

    hooks.LaunchTwistedFTPServer



