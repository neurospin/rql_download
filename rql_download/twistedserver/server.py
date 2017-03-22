#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import os
import re
import os.path as osp
import logging
import json
import stat
import posix
from collections import namedtuple

# Define the logger
logger = logging.getLogger(__name__)

# Twisted import
from twisted.conch.ls import lsLine
from twisted.conch.unix import (
    SSHSessionForUnixConchUser, SFTPServerForUnixConchUser, UnixConchUser)
from twisted.python import components
from twisted.cred.portal import Portal, IRealm
from twisted.cred.credentials import IUsernamePassword
from twisted.cred.checkers import ICredentialsChecker
from twisted.cred.error import UnauthorizedLogin
from twisted.conch.interfaces import ISFTPServer, ISFTPFile
from twisted.conch.ssh import factory, keys, session
from twisted.internet import defer
from zope.interface import implements

# CW import
from cubicweb import cwconfig
from cubicweb.server.repository import Repository
from cubicweb.server.utils import TasksManager
from cubes.rql_download.fuse.fuse_mount import get_cw_connection


# Define a mapping between cw export vid and file extension
VID_TO_EXT = {
    "csvexport": ".csv",
    "jsonexport": ".json",
    "ecsvexport": ".csv",
    "ejsonexport": ".json"
}

# Define the virtual path structure
VirtualPath = namedtuple('VirtualPath', ('search_name', 'search_relpath',
                                         'search_basedir', 'search_instance'))


class VirtualPathTranslator(object):
    """ Responsible to translate virtual path into real one.

    Suppose to be called from 'CubicWebConchUser' through the following methods:

    * openDirectory
    * getAttrs
    * realPath
    * openFile
    """
    INSTANCE_NAMES = None
    BASE_REAL_DIR = '/'
    file_perm = 0b1000000100100100
    dir_perm = 0b100001101101101
    file_entity_re = re.compile(r'(request_result)|.+_(\d+)$')

    def __init__(self, search_request):
        """ Initialize the 'VirtualPathTranslator' class.

        Parameters
        ----------
        search_request: Search (mandatory)
            An in memory user CWSearch.
        """
        self.search_request = search_request

    def list_directory(self, path):
        """ Method to list a virtual folder.

        Virtual folders have a common root organization:

        ::

            instance name
                |
                ---- CWSearch name
                            |
                            ---- ...

        Parameters
        ----------
        path: string (mandatory)
            the virtual path we want to access.

        Returns
        -------
        out: iterator
            an iterator containing virtual folder description. Each iterator
            item is a 3-uplet of the form (basename, longname, stat).
        """
        # Create/update an association between cw rset and db name
        self.rset_map = dict((key.lstrip("/"), value) for key, value in zip(
            self.INSTANCE_NAMES, self.search_request.get_searches()))
        self.all_cw_search_names = []
        for name, rset in self.rset_map.iteritems():
            self.all_cw_search_names.extend(
                [r[0].encode("utf-8") for r in rset])

        # Check we are dealing with a path
        assert path.startswith('/')
        # print "LIST::", path

        # Construct root folder
        if path == "/":
            if self.INSTANCE_NAMES is not None:
                root_virtual_folders = [r.encode("utf-8")
                                        for r in self.INSTANCE_NAMES]
            else:
                root_virtual_folders = self.cw_search_names
            for name in root_virtual_folders:
                s = self.stat("/{0}".format(name))
                yield (name,
                       lsLine(name, s),
                       self.attrs_from_stat(s))

        # Construct search folders if root contains instances
        elif (self.INSTANCE_NAMES is not None and
              path.lstrip("/") in self.INSTANCE_NAMES):
            # Get the proper rset
            rset = self.rset_map[path.lstrip("/")]
            cw_search_names = [r[0].encode("utf-8") for r in rset]
            for name in cw_search_names:
                s = self.stat('/%s' % name)
                yield (name,
                       lsLine(name, s),
                       self.attrs_from_stat(s))

        # Otherwise the build the tree based on the file path contained in cw
        else:
            virtpath = self.split_virtual_path(path)
            session_index = self.INSTANCE_NAMES.index(virtpath.search_instance)
            for filepath, rset_file in self.dir_content(virtpath,
                                                        session_index):

                if not rset_file:
                    s = self.stat(filepath, path_is_real=True)
                else:
                    # retrieve rset binary from database
                    rset = self.search_request.get_file_data(
                        file_eid=None, rset_file=True,
                        search_name=virtpath.search_name,
                        session_index=session_index)
                    s = self.stat_file_entity(rset.len)
                basename = osp.basename(filepath).encode('utf-8')
                longname = lsLine(basename, s)
                yield (basename, longname, self.attrs_from_stat(s))

    def real_path(self, virtpath):
        """ Get the real path from a virtual path.

        Simply concatenate the search basedir set in the configuration file
        with the search relpath.

        Parameters
        ----------
        virtpath: VirtualPath (mandatory)
            a virtual path.

        Returns
        -------
        out: string
            the real path on the server.
        """
        return osp.join(virtpath.search_basedir, virtpath.search_relpath)

    def get_attrs(self, path, followlinks=0):
        """ Return the file state.

        Parameters
        ----------
        binary_len: int (mandatory)
            the size of the file.

        Returns
        -------
        out: stat_result
            the same structure returned by a stat or lstat.
        """
        virtpath = self.split_virtual_path(path)
        if self.is_file_entity(virtpath):
            s = self.stat_file_entity()
        else:
            s = self.stat(path, followlinks)
        return self.attrs_from_stat(s)

    def stat_file_entity(self, binary_len=0):
        """ Return the file state.

        Parameters
        ----------
        binary_len: int (mandatory)
            the size of the file.

        Returns
        -------
        out: posix.stat_result
            the same structure returned by a stat or lstat.
        """
        return posix.stat_result((
            self.file_perm,
            0,  # st_ino
            0,  # st_dev
            0,  # st_nlink
            0,  # st_uid
            0,  # st_gid
            binary_len,  # st_size
            0,  # st_atime
            0,  # st_mtime
            0,  # st_ctime
        ))

    def get_attrs_file_entity(self, binary):
        """ Get statistical information of a Binary field.

        Parameters
        ----------
        binary: a Binary entity field (mandatory)
            a Binary object.

        Returns
        -------
        out: dict
            a dictionary summarizing the input statistic structure: size -
            uid - gid - mtime - atime - permissions.
        """
        s = self.stat_file_entity(binary.len)
        return self.attrs_from_stat(s)

    def is_file_entity(self, virtpath):
        """ Check if the file is virtual, ie. a Binary cubicweb file.

        Parameters
        ----------
        virtpath: VirtualPath  (mandatory)
            a virtual path of the form (search name, search relpath,
            search basedir, search instance).

        Returns
        -------
        out: bool
            True if the virtualpath point to a cubicweb file,
            False otherwise.
        """
        m = self.file_entity_re.search(virtpath.search_relpath)
        if m:
            self.matched_entity_file_eid = None
            self.matched_rset_file = False
            if m.group(1):
                self.matched_rset_file = True
            elif m.group(2):
                self.matched_entity_file_eid = m.group(2)
            return True
        return False

    def open_cw_file(self, virtpath):
        """ Method used to open a virtual cubicweb file.

        Parameters
        ----------
        virtpath: VirtualPath  (mandatory)
            a virtual path of the form (search name, search relpath,
            search basedir, search instance).

        Returns
        -------
        out: CubicwebFile
            a virtual file containing the Binary field data.
        """
        session_index = self.INSTANCE_NAMES.index(virtpath.search_instance)
        data = self.search_request.get_file_data(
            file_eid=self.matched_entity_file_eid,
            rset_file=self.matched_rset_file,
            search_name=virtpath.search_name,
            session_index=session_index)
        attrs = self.get_attrs_file_entity(data)
        return CubicwebFile(data, attrs)

    def stat(self, path, followlinks=0, path_is_real=False):
        """ Method to access a path state.

        Parameters
        ----------
        path: str (mandatory)
            a path from which we want to get the associated statistics.
        followlinks: int (optional, default 0)
            if True the system will follow the symbolic links with the 'os.stat'
            method,
            otherwise the 'os.lstat' method is used.
        path_is_real: bool (optional, default False)
            if True the path really exists on the file system,
            otherwise we have a virtual cubicweb path.

        Returns
        -------
        out: posix.stat_result
            the same structure returned by a stat or lstat.
        """
        if not path_is_real:

            # Create the association between cw rset and db name
            if not hasattr(self, "all_cw_search_names"):
                self.rset_map = dict((key.lstrip("/"), value) for key, value in zip(
                    self.INSTANCE_NAMES, self.search_request.get_searches()))
                self.all_cw_search_names = []
                for name, rset in self.rset_map.iteritems():
                    self.all_cw_search_names.extend(
                        [r[0].encode("utf-8") for r in rset])

            virtpath = self.split_virtual_path(path)
            if (virtpath.search_name != '' and
               virtpath.search_name not in (self.all_cw_search_names +
                                            self.INSTANCE_NAMES)):
                # raise OSError like os.stat does
                raise OSError('No such file or directory: "%s"' % path)
            if virtpath.search_relpath == '/' or virtpath.search_relpath == '':
                return posix.stat_result((
                    self.dir_perm,
                    0,  # st_ino
                    0,  # st_dev
                    0,  # st_nlink
                    0,  # st_uid
                    0,  # st_gid
                    4096,  # st_size
                    0,  # st_atime
                    0,  # st_mtime
                    0,  # st_ctime
                ))
            real_path = self.real_path(virtpath)
        else:
            real_path = path
        if followlinks:
            s = os.stat(real_path)
        else:
            s = os.lstat(real_path)
        if stat.S_ISDIR(s.st_mode):
            mode = self.dir_perm
        elif stat.S_ISREG(s.st_mode):
            mode = self.file_perm
        return posix.stat_result((mode,) + s[1:])

    def attrs_from_stat(self, s):
        """ Convert a 'posix.stat_result' to python dictionary.

        Parameters
        ----------
        s: posix.stat_result (mandatory)
            the same structure returned by a stat or lstat.

        Returns
        -------
        out: dict
            a dictionary summarizing the input statistic structure: size -
            uid - gid - mtime - atime - permissions.
        """
        return {'size': s.st_size,
                'uid': s.st_uid,
                'gid': s.st_gid,
                'mtime': s.st_mtime,
                'atime': s.st_atime,
                'permissions': s.st_mode}

    def dir_content(self, virtpath, session_index):
        """ Get complete file paths of files located in a virtual directory.

        Parameters
        ----------
        virtpath: VirtualPath  (mandatory)
            a virtual path of the form (search name, search relpath,
            search basedir, search instance).
        session_index: int (mandatory)
            an index pointing to the instance of interest.

        Returns
        -------
        out: iterator
            each item is 2-uplet of the form (file path, associated rset).
        """
        # print "--", virtpath

        # Do not consider the first level ie. instance level
        #if virtpath.search_name == self.INSTANCE_NAME:
        #    return self.cw_search_names

        files = self.search_request.get_files(virtpath, session_index)
        if files is None:
            return []
        return self.filter_files(files, self.real_path(virtpath))

    def split_virtual_path(self, path):
        """ Extract the name of a Search Entity from path.

        This name is expected to be the first part of path if no instance name
        are given, second one otherwise.

        Parameters
        ----------
        path: string (mandatory)
            the virtual path we want to split.

        Returns
        -------
        out: VirtualPath
            the virtual path built from the input path, ie. a 4-uplet of the
            form (search name, search relpath, search basedir, search instance).
        """
        # Check we are dealing with a path
        assert path.startswith(os.path.sep)

        # Split the path
        parts = path.lstrip(os.path.sep).split(os.path.sep)

        # No instance name provided or initialization of the other case
        if self.INSTANCE_NAMES is None or len(parts) == 1:
            return VirtualPath(
                parts[0], "/".join(parts[1:]), self.BASE_REAL_DIR, None)

        # Instance name provided: one extra level in the virtual tree
        else:
            return VirtualPath(
                parts[1], "/".join(parts[2:]), self.BASE_REAL_DIR, parts[0])

    def filter_files(self, files, path):
        """ Extract files which are located in a directory defined by path.

        Parameters
        ----------
        files: list of 2-uplet (mandatory)
            a list of files formated in a 2-uplet of the form (path, is_virtual).
        path: string (mandatory)
            the associated dir real path.

        Returns
        -------
        out: iterator
            each item is 2-uplet of the form (file path, associated rset).
        """
        if not path.endswith(os.path.sep):
            path += os.path.sep
        res = set()
        for f, rset_file in files:
            if f.startswith(path):
                filepath = path + f[len(path):].split('/', 1)[0]
                if filepath not in res:
                    yield filepath, rset_file
                    res.add(filepath)


class CubicWebConchUser(UnixConchUser):
    """ Class to create a cubicweb user.
    """
    def __init__(self, unix_username, cw_session_ids, login, cw_instance_names,
                 cw_repositories, base_dir):
        """ Initialize the CubicWebConchUser class.

        Parameters
        ----------
        unix_username: str (mandatory)
            the sftp server will read file system with the permission
            associated to this user.
        cw_session_ids: list of str (mandatory)
            the cubicweb sessions identifiers.
        login: str (mandatory)
            the cubicweb user login.
        cw_instance_names: list of str (mandatory)
            the cubicweb instance names.
        cw_repositories: cubicweb.server.repository.Repository (mandatory)
            internal cubicweb connections.
        base_dir: str (mandatory)
            base directory in which file are stored (it acts as
            mask, so every files outside this base_dir will be
            invisible).
        """
        # Inheritance
        UnixConchUser.__init__(self, unix_username)

        # Class parameters
        self.login = login

        # create the session associated to each repository
        self.cw_sessions = []
        self.cw_users = []
        self.instance_names = []
        for cnt, item in enumerate(
                zip(cw_session_ids, cw_repositories, cw_instance_names)):

            # Unpack items
            sessionid, repo, instance_name = item

            # Get the corresponding cw session
            session = repo._get_session(sessionid)
            #session.set_cnxset()
            self.cw_sessions.append(session)

            # Get the user entity eid
            cw_connection = get_cw_connection(instance_name)
            with cw_connection:
                login_eid = cw_connection.execute(
                    "Any X WHERE X is CWUser, X login '{0}'".format(login))
            self.cw_users.append(login_eid[0][0])

            # Store the instance name: assume the name is unique
            self.instance_names.append(instance_name)

        # Create a Search object that provides tools to filter the CWSearch
        # elements
        search_filter = Search(self.cw_sessions, cwusers=self.cw_users)

        # Create an object to translate the paths contained in the CWSearch
        # elements
        self.path_translator = VirtualPathTranslator(search_filter)
        self.path_translator.BASE_REAL_DIR = base_dir
        self.path_translator.INSTANCE_NAMES = self.instance_names

    def logout(self):
        """ Method to close all the user sessions.
        """
        for cwsession in self.cw_sessions:
            cwsession.close()
        logger.info("'{0}' logout!".format(self.login))

    def _runAsUser(self, f, *args, **kw):
        """ Method to logged-in a user.
        """
        user_is_root = os.getuid() == 0  # for tests
        if user_is_root:
            euid = os.geteuid()
            egid = os.getegid()
            groups = os.getgroups()
            uid, gid = self.getUserGroupId()
            os.setegid(0)
            os.seteuid(0)
            os.setgroups(self.getOtherGroups())
            os.setegid(gid)
            os.seteuid(uid)
        try:
            f = iter(f)
        except TypeError:
            f = [(f, args, kw)]
        try:
            for i in f:
                func = i[0]
                args = len(i) > 1 and i[1] or ()
                kw = len(i) > 2 and i[2] or {}
                r = func(*args, **kw)
        finally:
            if user_is_root:
                os.setegid(0)
                os.seteuid(0)
                os.setgroups(groups)
                os.setegid(egid)
                os.seteuid(euid)
        return r


class Search(object):
    """ Class to access all the file paths associated to a specific user
    CWSearch searches.
    """
    def __init__(self, sessions, cwusers):
        """ Initilaize the Search class.

        Parameters
        ----------
        sessions: list of cubicweb sessions (mandatory)
            a list of cubicweb sessions.
        cwusers: list of int (mandatory)
            a list of user eids.
        """
        self.cwsessions = sessions
        self.cwusers = cwusers

    def get_files(self, virtpath, session_index):
        """ Return a list of file associated to CWSearch named 'search_name'
        including rset file which is a pure virtual file.

        Parameters
        ----------
        virtpath: VirtualPath  (mandatory)
            a virtual path of the form (search name, search relpath,
            search basedir, search instance).
        session_index: int (mandatory)
            an index pointing to the instance of interest.

        Returns
        -------
        filepaths: list of 2-uplet (mandatory)
            a list of files formated in a 2-uplet of the form (path, is_virtual).
        """
        # Get the selected session and user
        session = self.cwsessions[session_index]
        cwuser = self.cwusers[session_index]

        # Create the connection
        with session.new_cnx() as cnx:

            # Get all the user CWSearch entities
            rset = cnx.execute('Any D WHERE S is CWSearch, S title %(title)s, '
                               'S owned_by %(cwuser)s, '
                               'S result F, F data D',
                               {'title': virtpath.search_name,
                                'cwuser': cwuser})

            # Reorganize the file paths
            filepaths = map(lambda x: (x, False),
                            json.loads(rset[0][0].getvalue())["files"])

            # Add the rset to the build tree, add the appropriate
            # file extension
            rset = cnx.execute('Any T WHERE S is CWSearch, S title %(title)s, '
                               'S rset_type T',
                               {'title': virtpath.search_name})
            fext = VID_TO_EXT[rset[0][0]]
            filepaths.append((osp.join(virtpath.search_basedir,
                              u"request_result" + fext), True))

        return filepaths

    def get_searches(self):
        """ Method to get for each user the result set with the name of the
        associated CWSearch entities.

        Returns
        -------
        rsets: list of rset
            the search names related to each user.
        """
        rsets = []
        for cwsession, cwuser in zip(self.cwsessions, self.cwusers):
            with cwsession.new_cnx() as cnx:
                rsets.append(
                    cnx.execute('Any SN WHERE X is CWSearch, X title SN, '
                                'X owned_by %(cwuser)s ',
                                {'cwuser': cwuser}))
        return rsets

    def get_file_data(self, file_eid, rset_file, session_index,
                      search_name=None):
        """ Get the Binary data contain in an entity.

        Parameters
        ----------
        file_eid: int (mandatory)
            the eid of the entity containing a 'data' Binary attribute.
        rset_file: bool (mandatory)
            True if we want the rset virtual file associated to the CWSearch,
            False otherwise.
        session_index: int (mandatory)
            an index pointing to the instance of interest.
        search_name: string (optional, default None)

        Returns
        -------
        out: Binary or None
            the desired Binary data object.
        """
        # Get the selected session and user
        session = self.cwsessions[session_index]
        cwuser = self.cwusers[session_index]

        if rset_file:
            with session.new_cnx() as cnx:
                rset = cnx.execute('Any D WHERE F is File, '
                                   'S is CWSearch, S title %(title)s, '
                                   'S owned_by %(cwuser)s, S rset F, '
                                   'F data D',
                                   {'title': search_name,
                                    'cwuser': cwuser})
        else:
            with session.new_cnx() as cnx:
                rset = cnx.execute('Any D WHERE F is File, '
                                   'F eid %(eid)s, F data D',
                                   {'eid': file_eid})
        if rset:
            return rset[0][0]


class CubicWebCredentialsChecker:
    """ Check user credentials on a cubicweb instance
    """
    credentialInterfaces = IUsernamePassword,
    implements(ICredentialsChecker)

    def __init__(self, cw_repositories):
        """ Initialize the 'CubicWebCredentialsChecker' class.

        Parameters
        ----------
        cw_repositories: cubicweb.server.repository.Repository (mandatory)
            internal cubicweb connections.
        """
        self.cw_repositories = cw_repositories

    def requestAvatarId(self, credentials):
        """ Get the avatar id.

        Parameters
        ----------
        credentials: (mandatory)
            something which implements one of the interfaces in
            self.credentialInterfaces.

        Returns
        -------
        out:
            a Deferred which will fire a string which identifies an avatar,
            an empty tuple to specify an authenticated anonymous user
            (provided as checkers.ANONYMOUS) or fire a
            Failure(UnauthorizedLogin). Alternatively, return the result itself.
        """
        try:
            session_ids = []
            for repo in self.cw_repositories:
                session_ids.append(repo.connect(credentials.username,
                                                password=credentials.password))
        except:
            logging.exception("Failed to get connection for user {0}".format(
                credentials.username))
            return defer.fail(UnauthorizedLogin("Invalid user/password"))
        else:
            return defer.succeed((credentials.username, session_ids))


class CubicWebSFTPRealm:
    """ A Realm corresponds to an application domain and is in charge of
    avatars, which are network-accessible business logic objects.

    To connect this to an authentication database, a top-level object called
    a Portal stores a realm, and a number of credential checkers.
    """
    implements(IRealm)

    def __init__(self, cw_instance_names, cw_repositories, conf):
        """ Initilaize the 'CubicWebSFTPRealm' class.

        Parameters
        ----------
        cw_instance_names: list of str (mandatory)
            the cubicweb instance names.
        cw_repositories: cubicweb.server.repository.Repository (mandatory)
            the internal cubicweb connections.
        conf: logilab.common.configuration.Configuration (mandatory)
            the server configuration options.
        """
        self.conf = conf
        self.cw_instance_names = cw_instance_names
        self.cw_repositories = cw_repositories

    def requestAvatar(self, identity, mind, *interfaces):
        """ This method will typically be called from 'Portal.login'.

        The 'identity' is the one returned by a CredentialChecker.

        Parameters
        ----------
        identity, mind, interfaces: objects (mandatory)
            see 'twisted.cred.portal.IRealm.requestAvatar'.

        Returns
        -------
        out: tuple
            a 3-uplet of the form (interface, avatarAspect, logout).
        """
        #print "INNNN::", identity, self.cw_repositories
        cw_session_ids = identity[1]
        unix_username = self.conf.get('unix-username')
        user = CubicWebConchUser(unix_username,
                                 cw_session_ids=cw_session_ids,
                                 login=identity[0],
                                 cw_instance_names=self.cw_instance_names,
                                 cw_repositories=self.cw_repositories,
                                 base_dir=self.conf.get('base-dir'))
        return interfaces[0], user, user.logout


class CubicWebSSHdFactory(factory.SSHFactory):
    """ Define a factory for SSH servers.
    """
    def __init__(self, conf):
        """ Initialize the 'CubicWebSSHdFactory' class.

        Parameters
        ----------
        conf: logilab.common.configuration.Configuration (mandatory)
            the server configuration options.
        """
        self._init_keys(conf)

        # Deal with multiple instances
        cw_instance_names = conf.get("cubicweb-instance").split(":")
        cw_repositories = []
        for instance_name in cw_instance_names:
            config = cwconfig.instance_configuration(cw_instance_names[0])
            cw_repositories.append(
                Repository(config, TasksManager(), vreg=None))

        # A Portal associates one Realm with a collection of CredentialChecker
        # instances.
        portal = Portal(
            CubicWebSFTPRealm(cw_instance_names, cw_repositories, conf))
        portal.registerChecker(CubicWebCredentialsChecker(cw_repositories))
        self.portal = portal

    def _init_keys(self, config):
        """ Method to set the public and private keys (as generated by
        ssh-keygen).

        The pass phrase and the path to the public/private key files are
        defined in the instance configuration file.

        Parameters
        ----------
        config: logilab.common.configuration.Configuration (mandatory)
            the server configuration options.
        """
        passwd = config.get('passphrase')
        self.publicKeys = {
            'ssh-rsa': keys.Key.fromFile(config.get('public-key'))
        }
        self.privateKeys = {
            'ssh-rsa': keys.Key.fromFile(config.get('private-key'),
                                         passphrase=passwd)
        }


def unauthorized(func):
    def _unauthorized(self, *args, **kwargs):
        # XXX find appropriate exception + log username
        logging.warning('user %s tried to access to method %s',
                        self.avatar, func.__name__)
        raise Exception('method %s is unauthorized' % func.__name__)
    return _unauthorized


class CubicWebProxiedSFTPServer(SFTPServerForUnixConchUser):
    """ Implements the authorized actions on the sftp server.
    """
    implements(ISFTPServer)

    def openFile(self, filename, flags, attrs):
        """ Called when the clients asks to open a file.

        .. note::

            There is no way to indicate text or binary files. It is up
            to the SFTP client to deal with this.

        Parameters
        ----------
        filename: str (mandatory)
            a string representing the file to open.
        flags: int (mandatory)
            an integer of the flags to open the file with, ORed together.
            The flags and their values are listed at the bottom of this file.
        attrs: list (mandatory)
            a list of attributes to open the file with.  It is a dictionary,
            consisting of 0 or more keys. The possible keys are:

            * size: the size of the file in bytes
            * uid: the user ID of the file as an integer
            * gid: the group ID of the file as an integer
            * permissions: the permissions of the file with as an integer.
            * the bit representation of this field is defined by POSIX.
            * atime: the access time of the file as seconds since the epoch.
            * mtime: the modification time of the file as seconds since the
              epoch.
            * ext_*: extended attributes.  The server is not required to
              understand this, but it may.

        Returns
        -------
        out: object
            an object that meets the ISFTPFile interface. Alternatively,
            it can return a L{Deferred} that will be called back with the object.
        """
        t = self.avatar.path_translator
        virtpath = t.split_virtual_path(filename)
        if t.is_file_entity(virtpath):
            return t.open_cw_file(virtpath)
        filepath = t.real_path(virtpath)
        return SFTPServerForUnixConchUser.openFile(self, filepath, flags,
                                                   attrs)

    @unauthorized
    def removeFile(self, filename):
        """ Remove the given file.

        This method returns when the remove succeeds, or a Deferred that is
        called back when it succeeds.

        .. warning::

            Unauthorized method.

        Parameters
        ----------
        filename: str (mandatory)
            the name of the file as a string.
        """

    @unauthorized
    def renameFile(self, oldpath, newpath):
        """ Rename the given file.

        This method returns when the rename succeeds, or a L{Deferred} that is
        called back when it succeeds. If the rename fails, C{renameFile} will
        raise an implementation-dependent exception.

        .. warning::

            Unauthorized method.

        Parameters
        ----------
        oldpath: str  (mandatory)
            the current location of the file.
        newpath: str  (mandatory)
            the new file name.
        """

    @unauthorized
    def makeDirectory(self, path, attrs):
        """ Make a directory.

        This method returns when the directory is created, or a Deferred that
        is called back when it is created.

        Parameters
        ----------
        path: str  (mandatory)
            the name of the directory to create as a string.
        attrs: dict  (mandatory)
            a dictionary of attributes to create the directory with.
            Its meaning is the same as the attrs in the L{openFile} method.
        """

    @unauthorized
    def removeDirectory(self, path):
        """ Remove a directory (non-recursively).

        It is an error to remove a directory that has files or directories in
        it.

        This method returns when the directory is removed, or a Deferred that
        is called back when it is removed.

        .. warning::

            Unauthorized method.

        Parameters
        ----------
        path: str  (mandatory)
            the directory to remove.
        """

    def openDirectory(self, path):
        """ Open a directory for scanning.

        This method returns an iterable object that has a close() method,
        or a Deferred that is called back with same.

        The close() method is called when the client is finished reading
        from the directory.  At this point, the iterable will no longer
        be used.

        The iterable should return triples of the form (filename,
        longname, attrs) or Deferreds that return the same.  The
        sequence must support __getitem__, but otherwise may be any
        'sequence-like' object.

        filename is the name of the file relative to the directory.
        logname is an expanded format of the filename. The recommended format
        is:
        -rwxr-xr-x   1 mjos     staff      348911 Mar 25 14:29 t-filexfer
        1234567890 123 12345678 12345678 12345678 123456789012

        The first line is sample output, the second is the length of the field.
        The fields are: permissions, link count, user owner, group owner,
        size in bytes, modification time.

        attrs is a dictionary in the format of the attrs argument to openFile.

        Parameters
        ----------
        path: str  (mandatory)
            the directory to open.
        """
        return self.avatar.path_translator.list_directory(path)

    def getAttrs(self, path, followLinks):
        """ Return the attributes for the given path.

        This method returns a dictionary in the same format as the attrs
        argument to openFile or a Deferred that is called back with same.

        Parameters
        ----------
        path: str  (mandatory)
            the path to return attributes for as a string.
        followLinks: bool  (mandatory)
            If it is True, follow symbolic links.

        Returns
        -------
        out: dict
            If it 'followLinks' is True, follow symbolic links and return
            attributes for the real path at the base.
            If it is False, return attributes for the specified path.
        """
        # path parameter comes from realPath method
        return self.avatar.path_translator.get_attrs(path, followLinks)

    @unauthorized
    def setAttrs(self, path, attrs):
        """ Set the attributes for the path.

        This method returns when the attributes are set or a Deferred that is
        called back when they are.

        .. warning::

            Unauthorized method.

        Parameters
        ----------
        path: str  (mandatory)
            the path to set attributes for as a string.
        attrs: dict  (mandatory)
            a dictionary in the same format as the attrs argument to
            L{openFile}.
        """

    @unauthorized
    def readLink(self, path):
        """ Find the root of a set of symbolic links.

        This method returns the target of the link, or a Deferred that
        returns the same.

        .. warning::

            Unauthorized method.

        Parameters
        ----------
        path: str  (mandatory)
            the path of the symlink to read.
        """

    @unauthorized
    def makeLink(self, linkPath, targetPath):
        """ Create a symbolic link.

        This method returns when the link is made, or a Deferred that
        returns the same.

        .. warning::

            Unauthorized method.

        Parameters
        ----------
        linkPath: str  (mandatory)
            the pathname of the symlink as a string.
        targetPath: str  (mandatory)
            the path of the target of the link as a string.
        """

    def realPath(self, path):
        """
        Convert any path to an absolute path.

        This method returns the absolute path as a string, or a Deferred
        that returns the same.

        Parameters
        ----------
        path: str  (mandatory)
            the path to convert as a string.
        """
        if path == '.':
            return '/'
        return osp.abspath(path)  # handle /toto/..

    @unauthorized
    def extendedRequest(self, extendedName, extendedData):
        """ This is the extension mechanism for SFTP.  The other side can send
        us arbitrary requests.

        If we don't implement the request given by extendedName, raise
        NotImplementedError.

        The return value is a string, or a Deferred that will be called
        back with a string.

        .. warning::

            Unauthorized method.

        Parameters
        ----------
        extendedName: str  (mandatory)
            the name of the request as a string.
        extendedData: str  (mandatory)
            the data the other side sent with the request
        """


class CubicwebFile:
    """ A virtual cubicweb file.
    """
    implements(ISFTPFile)

    def __init__(self, cw_binary, attrs):
        self.binary = cw_binary
        self.attrs = attrs

    def close(self):
        """ Close the file.

        This method returns nothing if the close succeeds immediately, or a
        Deferred that is called back when the close succeeds.
        """
        self.binary.close()

    def readChunk(self, offset, length):
        """ Read from the file.

        If EOF is reached before any data is read, raise EOFError.

        This method returns the data as a string, or a Deferred that is
        called back with same.

        Parameters
        ----------
        offset: int
            an integer that is the index to start from in the file.
        length: int:
            the maximum length of data to return. The actual amount
            returned may be less than this. For normal disk files, however,
            this should read the requested number (up to the end of the file).

        Returns
        -------
        data: object
            the requested chunk of data.
        """
        self.binary.seek(offset)
        return self.binary.read(length)

    @unauthorized
    def writeChunk(self, offset, data):
        """ Write to the file.

        This method returns when the write completes, or a Deferred that is
        called when it completes.

        .. warning::

            Unauthorized method.

        Parameters
        ----------
        offset: int
            an integer that is the index to start from in the file.
        data: str
            a string that is the data to write.
        """

    def getAttrs(self):
        """
        Return the attributes for the file.

        This method returns a dictionary in the same format as the attrs
        argument to L{openFile} or a L{Deferred} that is called back with same.

        Returns
        -------
        out: object
            a dictionary in the same format as the attrs argument to
            L{openFile} or a L{Deferred} that is called back with same.
        """
        return self.attrs

    @unauthorized
    def setAttrs(self, attrs):
        """
        Set the attributes for the file.

        This method returns when the attributes are set or a Deferred that is
        called back when they are.

        .. warning::

            Unauthorized method.

        Parameters
        ----------
        attrs: dict
            a dictionary in the same format as the attrs argument to
            L{openFile}.
        """


components.registerAdapter(CubicWebProxiedSFTPServer, CubicWebConchUser,
                           ISFTPServer)
components.registerAdapter(SSHSessionForUnixConchUser, CubicWebConchUser,
                           session.ISession)
