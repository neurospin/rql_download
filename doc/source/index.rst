..  NSAp documentation master file, created by
    sphinx-quickstart on Wed Sep  4 12:18:01 2013.
    You can adapt this file completely to your liking, but it should at least
    contain the root `toctree` directive.


Rql Download
============

Summary
-------
* Add capability to supply a saved rset via an sftp server. 
* Propose a tool the send RQL request via a Python script.


Description
-----------
This cube provides an :ref:`action button <views_ref>` which shows up if current
rset is adaptable in IFSetAdapter or IEntityAdapter (adpaters also provided by this cube).
This button creates a :ref:`CWSearch <schema_ref>` entity to store filepath 
computed by the adapter from the entities in result set.

Then another process (that can be started automatically by Cubicweb) can
retrieve these CWSearch entities and show the stored filepaths via :ref:`sftp
protocol and twisted server <twisted_ref>`. The authentication in this
process is delegated to Cubicweb.

Another strategy consists of :ref:`Fuse virtual folders's <fuse_ref>` creation
to retrieve these CWSearch entities and show the stored filepaths. After some
system administration, such virtual folders can be accessed through a classical
server SFTP service. The authentication in this case is delegated to the
system.

Finally, a Python module is proposed to :ref:`script the RQL requests <cwbrowser_ref>`. 


Contents
--------
.. toctree::
    :maxdepth: 1

    installation
    documentation


Search
------

:ref:`search`





