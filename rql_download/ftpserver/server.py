import os
import re
import os.path as osp
import logging
import json
import stat
import posix
from collections import namedtuple

from twisted.conch.ls import lsLine
from twisted.conch.unix import (SSHSessionForUnixConchUser,
                                SFTPServerForUnixConchUser, UnixConchUser)
from twisted.python import components

from twisted.cred.portal import Portal, IRealm
from twisted.cred.credentials import IUsernamePassword
from twisted.cred.checkers import ICredentialsChecker
from twisted.cred.error import UnauthorizedLogin
from twisted.conch.interfaces import ISFTPServer, ISFTPFile
from twisted.conch.ssh import factory, keys, session
from twisted.internet import defer
from zope.interface import implements


from cubicweb import cwconfig
from cubicweb.server.repository import Repository
from cubicweb.server.utils import TasksManager


VirtualPath = namedtuple('VirtualPath', ('search_name', 'search_relpath',
                                         'search_basedir'))


class VirtualPathTranslator(object):
    """responsible to translate virtual path into real one.
    Suppose to be called from CubicWebConchUser through the following methods:
        - openDirectory
        - getAttrs
        - realPath
        - openFile
    """
    BASE_REAL_DIR = '/'
    file_perm = 0b1000000100100100
    dir_perm = 0b100001101101101
    file_entity_re = re.compile(r'(rset)|.+_(\d+)$')

    def __init__(self, search_request):
        self.search_request = search_request

    def list_directory(self, path):
        assert path.startswith('/')
        if path == '/':
            searches = self.search_request.get_searches()
            for (name,) in searches:
                name = name.encode('utf-8')
                s = self.stat('/%s' % name)
                yield (name,
                       lsLine(name, s),
                       self.attrs_from_stat(s))
        else:
            virtpath = self.split_virtual_path(path)
            for filepath, rset_file in self.dir_content(virtpath):
                if not rset_file:
                    s = self.stat(filepath, path_is_real=True)
                else:
                    # retrieve rset binary from database
                    rset = self.search_request.get_file_data(file_eid=None,
                                                             rset_file=True,
                                                             search_name=virtpath.search_name)
                    s = self.stat_file_entity(rset.len)
                basename = osp.basename(filepath).encode('utf-8')
                longname = lsLine(basename, s)
                yield (basename, longname, self.attrs_from_stat(s))

    def real_path(self, virtpath):
        return osp.join(virtpath.search_basedir, virtpath.search_relpath)

    def get_attrs(self, path, followlinks=0):
        virtpath = self.split_virtual_path(path)
        if self.is_file_entity(virtpath):
            s = self.stat_file_entity()
        else:
            s = self.stat(path, followlinks)
        return self.attrs_from_stat(s)

    def stat_file_entity(self, binary_len=0):
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
        s = self.stat_file_entity(binary.len)
        return self.attrs_from_stat(s)

    def is_file_entity(self, virtpath):
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
        data = self.search_request.get_file_data(file_eid=self.matched_entity_file_eid,
                                                 rset_file=self.matched_rset_file,
                                                 search_name=virtpath.search_name)
        attrs = self.get_attrs_file_entity(data)
        return CubicwebFile(data, attrs)

    def stat(self, path, followlinks=0, path_is_real=False):
        if not path_is_real:
            virtpath = self.split_virtual_path(path)
            if (virtpath.search_name != '' and
                virtpath.search_name not in [r[0] for r in
                                             self.search_request.get_searches()]):
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
        return  {'size': s.st_size,
                 'uid': s.st_uid,
                 'gid': s.st_gid,
                 'mtime': s.st_mtime,
                 'atime': s.st_atime,
                 'permissions': s.st_mode}

    def dir_content(self, virtpath):
        """get complete filepath  of files located in
        virtual directory (i.e. starting with a search name) defined by path"""
        files = self.search_request.get_files(virtpath)
        if files is None:
            return []
        return self.filter_files(files, self.real_path(virtpath))

    def split_virtual_path(self, path):
        """Extract the name of a Search Entity from path. This name is expected to
        be the first part of path"""
        assert path.startswith('/')
        parts = path.lstrip('/').split('/')
        return VirtualPath(parts[0], '/'.join(parts[1:]), self.BASE_REAL_DIR)

    def filter_files(self, files, path):
        """Extract files which are located in a directory defined by path"""
        if not path.endswith('/'):
            path += '/'
        res = set()
        for f, rset_file in files:
            if f.startswith(path):
                filepath = path + f[len(path):].split('/', 1)[0]
                if filepath not in res:
                    yield filepath, rset_file
                    res.add(filepath)


class CubicWebConchUser(UnixConchUser):

    def __init__(self, unix_username, cw_sessionid, login, repo, base_dir):
        UnixConchUser.__init__(self, unix_username)
        self.session = repo._get_session(cw_sessionid) # XXX private method
        self.session.set_cnxset()
        login_eid = self.session.execute('Any X WHERE X is CWUser, '
                                         'X login %(login)s', {'login': login})
        s = Search(self.session, cwuser=login_eid[0][0])
        self.path_translator = VirtualPathTranslator(s)
        self.path_translator.BASE_REAL_DIR = base_dir

    def logout(self):
        self.session.close()
        print 'logout !'

    def _runAsUser(self, f, *args, **kw):
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

    def __init__(self, session, cwuser):
        self.session = session
        self.cwuser = cwuser

    def get_files(self, virtpath):
        """ return a list of file associated to CWSearch named ``search_name``
        including ``rset`` file"""
        rset = self.session.execute('Any D WHERE S is CWSearch, S title %(name)s, '
                                    'S owned_by %(cwuser)s, '
                                    'S result F, F data D',
                                    {'name': virtpath.search_name,
                                     'cwuser': self.cwuser})
        filepaths = map(lambda x: (x, False),
                        json.loads(rset[0][0].getvalue())['files'])
        filepaths.append((osp.join(virtpath.search_basedir, u'rset'), True))
        return filepaths

    def get_searches(self):
        rset = self.session.execute('Any SN WHERE X is CWSearch, X title SN, '
                                    'X owned_by %(cwuser)s ',
                                    {'cwuser': self.cwuser})
        return rset

    def get_file_data(self, file_eid, rset_file, search_name=None):
        if rset_file:
            rset = self.session.execute('Any D WHERE F is File, '
                                        'S is CWSearch, S title %(name)s, '
                                        'S owned_by %(cwuser)s, S rset F, '
                                        'F data D',
                                        {'name': search_name,
                                         'cwuser': self.cwuser})
        else:
            rset = self.session.execute('Any D WHERE F is File, '
                                        'F eid %(eid)s, F data D',
                                        {'eid': file_eid})
        if rset:
            return rset[0][0]


class CubicWebCredentialsChecker:
    """check user credentials on a cubicweb instance
    """
    credentialInterfaces = IUsernamePassword,
    implements(ICredentialsChecker)

    def __init__(self, repo):
        self.repo = repo

    def requestAvatarId(self, credentials):
        try:
            sessionid = self.repo.connect(credentials.username,
                                          password=credentials.password)
        except Exception, exc:
            logging.exception('failed to get connection for user %s',
                              credentials.username)
            return defer.fail(UnauthorizedLogin("invalid password"))
        else:
            return defer.succeed((credentials.username, sessionid))


class CubicWebSFTPRealm:
    implements(IRealm)

    def __init__(self, repo, conf):
        self.conf = conf
        self.repo = repo

    def requestAvatar(self, identity, mind, *interfaces):
        unix_username = self.conf.get('unix-username')
        user = CubicWebConchUser(unix_username,
                                 cw_sessionid=identity[1],
                                 login=identity[0],
                                 repo=self.repo,
                                 base_dir=self.conf.get('base-dir'))
        return interfaces[0], user, user.logout



class CubicWebSSHdFactory(factory.SSHFactory):

    def __init__(self, conf):
        self._init_keys(conf)
        config = cwconfig.instance_configuration(conf.get('cubicweb-instance'))
        repo = Repository(config, TasksManager(), vreg=None)
        portal = Portal(CubicWebSFTPRealm(repo, conf))
        portal.registerChecker(CubicWebCredentialsChecker(repo))
        self.portal = portal

    def _init_keys(self, config):
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
    implements(ISFTPServer)

    def openFile(self, filename, flags, attrs):
        """
        Called when the clients asks to open a file.

        @param filename: a string representing the file to open.

        @param flags: an integer of the flags to open the file with, ORed together.
        The flags and their values are listed at the bottom of this file.

        @param attrs: a list of attributes to open the file with.  It is a
        dictionary, consisting of 0 or more keys.  The possible keys are::

            size: the size of the file in bytes
            uid: the user ID of the file as an integer
            gid: the group ID of the file as an integer
            permissions: the permissions of the file with as an integer.
            the bit representation of this field is defined by POSIX.
            atime: the access time of the file as seconds since the epoch.
            mtime: the modification time of the file as seconds since the epoch.
            ext_*: extended attributes.  The server is not required to
            understand this, but it may.

        NOTE: there is no way to indicate text or binary files.  it is up
        to the SFTP client to deal with this.

        This method returns an object that meets the ISFTPFile interface.
        Alternatively, it can return a L{Deferred} that will be called back
        with the object.
        """
        t = self.avatar.path_translator
        virtpath = t.split_virtual_path(filename)
        if t.is_file_entity(virtpath):
            return t.open_cw_file(virtpath)
        filepath = t.real_path(virtpath)
        return SFTPServerForUnixConchUser.openFile(self, filepath, flags, attrs)

    @unauthorized
    def removeFile(self, filename):
        """
        Remove the given file.

        This method returns when the remove succeeds, or a Deferred that is
        called back when it succeeds.

        @param filename: the name of the file as a string.
        """

    @unauthorized
    def renameFile(self, oldpath, newpath):
        """
        Rename the given file.

        This method returns when the rename succeeds, or a L{Deferred} that is
        called back when it succeeds. If the rename fails, C{renameFile} will
        raise an implementation-dependent exception.

        @param oldpath: the current location of the file.
        @param newpath: the new file name.
        """

    @unauthorized
    def makeDirectory(self, path, attrs):
        """
        Make a directory.

        This method returns when the directory is created, or a Deferred that
        is called back when it is created.

        @param path: the name of the directory to create as a string.
        @param attrs: a dictionary of attributes to create the directory with.
        Its meaning is the same as the attrs in the L{openFile} method.
        """

    @unauthorized
    def removeDirectory(self, path):
        """
        Remove a directory (non-recursively)

        It is an error to remove a directory that has files or directories in
        it.

        This method returns when the directory is removed, or a Deferred that
        is called back when it is removed.

        @param path: the directory to remove.
        """

    def openDirectory(self, path):
        """
        Open a directory for scanning.

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
        logname is an expanded format of the filename.  The recommended format
        is:
        -rwxr-xr-x   1 mjos     staff      348911 Mar 25 14:29 t-filexfer
        1234567890 123 12345678 12345678 12345678 123456789012

        The first line is sample output, the second is the length of the field.
        The fields are: permissions, link count, user owner, group owner,
        size in bytes, modification time.

        attrs is a dictionary in the format of the attrs argument to openFile.

        @param path: the directory to open.
        """
        return self.avatar.path_translator.list_directory(path)

    def getAttrs(self, path, followLinks):
        """
        Return the attributes for the given path.

        This method returns a dictionary in the same format as the attrs
        argument to openFile or a Deferred that is called back with same.

        @param path: the path to return attributes for as a string.
        @param followLinks: a boolean.  If it is True, follow symbolic links
        and return attributes for the real path at the base.  If it is False,
        return attributes for the specified path.
        """
        # path parameter comes from realPath method
        return self.avatar.path_translator.get_attrs(path, followLinks)

    @unauthorized
    def setAttrs(self, path, attrs):
        """
        Set the attributes for the path.

        This method returns when the attributes are set or a Deferred that is
        called back when they are.

        @param path: the path to set attributes for as a string.
        @param attrs: a dictionary in the same format as the attrs argument to
        L{openFile}.
        """

    @unauthorized
    def readLink(self, path):
        """
        Find the root of a set of symbolic links.

        This method returns the target of the link, or a Deferred that
        returns the same.

        @param path: the path of the symlink to read.
        """

    @unauthorized
    def makeLink(self, linkPath, targetPath):
        """
        Create a symbolic link.

        This method returns when the link is made, or a Deferred that
        returns the same.

        @param linkPath: the pathname of the symlink as a string.
        @param targetPath: the path of the target of the link as a string.
        """

    def realPath(self, path):
        """
        Convert any path to an absolute path.

        This method returns the absolute path as a string, or a Deferred
        that returns the same.

        @param path: the path to convert as a string.
        """
        if path == '.':
            return '/'
        return osp.abspath(path) # handle /toto/..

    @unauthorized
    def extendedRequest(self, extendedName, extendedData):
        """
        This is the extension mechanism for SFTP.  The other side can send us
        arbitrary requests.

        If we don't implement the request given by extendedName, raise
        NotImplementedError.

        The return value is a string, or a Deferred that will be called
        back with a string.

        @param extendedName: the name of the request as a string.
        @param extendedData: the data the other side sent with the request,
        as a string.
        """


class CubicwebFile:
    implements(ISFTPFile)

    def __init__(self, cw_binary, attrs):
        self.binary = cw_binary
        self.attrs = attrs

    def close(self):
        """
        Close the file.

        This method returns nothing if the close succeeds immediately, or a
        Deferred that is called back when the close succeeds.
        """
        self.binary.close()

    def readChunk(self, offset, length):
        """
        Read from the file.

        If EOF is reached before any data is read, raise EOFError.

        This method returns the data as a string, or a Deferred that is
        called back with same.

        @param offset: an integer that is the index to start from in the file.
        @param length: the maximum length of data to return.  The actual amount
        returned may less than this.  For normal disk files, however,
        this should read the requested number (up to the end of the file).
        """
        self.binary.seek(offset)
        return self.binary.read(length)

    @unauthorized
    def writeChunk(self, offset, data):
        """
        Write to the file.

        This method returns when the write completes, or a Deferred that is
        called when it completes.

        @param offset: an integer that is the index to start from in the file.
        @param data: a string that is the data to write.
        """

    def getAttrs(self):
        """
        Return the attributes for the file.

        This method returns a dictionary in the same format as the attrs
        argument to L{openFile} or a L{Deferred} that is called back with same.
        """
        return self.attrs

    @unauthorized
    def setAttrs(self, attrs):
        """
        Set the attributes for the file.

        This method returns when the attributes are set or a Deferred that is
        called back when they are.

        @param attrs: a dictionary in the same format as the attrs argument to
        L{openFile}.
        """


components.registerAdapter(CubicWebProxiedSFTPServer, CubicWebConchUser, ISFTPServer)
components.registerAdapter(SSHSessionForUnixConchUser, CubicWebConchUser, session.ISession)
