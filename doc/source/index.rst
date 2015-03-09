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
This button allows to create a :ref:`CWSearch <schema_ref>` entity responsible to store filepath 
computed by the adapter from the entities in rset.

Then another process (which can be started automatically by cubicweb) can
retrieve these CWSearch entities and show the stored filepaths via :ref:`sftp
protocol and twisted server <twisted_ref>`. The authentication in this
process is delegated to cubicweb.

An other strategy consists in creating :ref:`Fuse virtual folders <fuse_ref>`
to retrieve these CWSearch entities and show the stored filepaths. after some
system administration, Such virtual folders can be accessed through classical
server SFTP service. The authentication in this case is delegated to the
system.

Finally, a Python module is proposed to :ref:`script the RQL requests <cwbrowser_ref>`. 

How to use
----------
To use this cube implement the adapter ``IFilePath`` for the entity you want to
expose via the sftp server. The adapter should implement the method
``get_paths`` as a generator (or as an iterator). ``get_paths`` yields a pair in
a tuple. The first element is a filepath as a string and the second element is
boolean which tells if the filepath exists or not (which is translated in the
hook: "if the filepath should be added in the result or not"). As shortcut
``get_paths`` can also just yields a filepath as a string which is directly
added to the result.

An example for File entity could be (with assumption that File entities are
stored on filesystem and not in database):


class FileIFilePathAdapter(BaseIFilePathAdapter):
    __select__ = BaseIFilePathAdapter.__select__ & is_instance('File')

    def get_paths(self):
        storage = self._cw.repo.system_source.storage('File', 'data')
        yield storage.current_fs_path(self.entity, 'data')


(others examples can be found in test/data/entities.py)

To enable automatic launched of sftp server at cubicweb startup, set
``start_sftp_server`` to ``yes`` in all-in-one.conf file.

To use a common base directory set ``sftp_server_basedir`` in all-in-one.conf.


See also ftpserver/doc/main.txt, to configure sftp server

Cube to download data from a cubicweb database using the CWSearch mechanism.
Methods to access the database content from a python script.


Contents
========
.. toctree::
    :maxdepth: 1

    installation
    documentation


Search
=======

:ref:`search`





