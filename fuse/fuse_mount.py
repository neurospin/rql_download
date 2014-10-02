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
import sys

# CW import
from cubicweb.cwconfig import CubicWebConfiguration as cwcfg
from logilab.common.configuration import Configuration


def get_cw_connection(instance_name):
    """ Connect to a local instance using an in memory connection.

    Parameters
    ----------
    instance_name: str (mandatory)
        the name of the cw instance we want to connect.

    Returns
    -------
    mih: cubicweb.server.migractions.ServerMigrationHelper
        the server migration object that contains a 'session' and 'shutdown'
        attributes.
    """
    # Parse/configure the all in one configuration
    config = cwcfg.config_for(instance_name)
    sources = ("all",)
    config.set_sources_mode(sources)
    config.repairing = False

    # Create server migration helper
    mih = config.migration_handler()

    return mih


def get_cw_basedir(instance_name, basedir_alias="basedir"):
    """ Get the instance 'basedir' parameter.

    Parameters
    ----------
    instance_name: str (mandatory)
        the name of the cw instance we want to connect.
    basedir_alias: str (optional, default 'basedir')
        the cw option name.

    Returns
    -------
    basedir: str
        part of the image path to hide in the virtual fs.
    """
    # Get the configuration file
    config = cwcfg.config_for(instance_name)
    config_file = os.path.join(
        os.path.dirname(config.sources_file()), "all-in-one.conf")

    # Parse the configuration file and retrive the basedir
    with open(config_file) as open_file:
        for line in open_file.readlines():
            match = re.match(r"^(\w+)=(\S*)$", line)
            if match:
                name, value = match.groups()
                if name == basedir_alias:
                    return value

    # If the basedir parameter is nor found raise an exception
    raise Exception("No 'basedir' option has been declared in the '{0}' "
                    "configuration file.".format(config_file))

class VirtualDirectory(object):
    """
    Build an internal representation of a full virtual directory to allow
    easy and fast usge of this directory with fuse.
    """
    def __init__(self, root_data_dir):
        """
        Creates an empty virtual directory. The virtual directory can be
        populated with make_directory() and add_file(). Its content can be
        accessed with stat(), listdir() and get_real_path().
        """
        self.root_data_dir = root_data_dir
        now = time.time()
        self.content = {}
        self.content['/'] = ([], 0, 0, 0555, now)
    
    def make_directory(self, path, uid, gid, time):
        """
        Create a virtual directory. The parent directory must have been
        created before. The new directory will be owned by the given uid and
        gid. Its access mode will be 0500 (read and axecutable for user only).
        All access an modification times will be set to the given time.
        """
        path_info = self.content.get(path)
        if path_info is not None:
            if path_info[1:] != (uid, gid, 0500, time):
                raise ValueError('Virtual directory %s already exists' % path)
        self.content[path] = ([], uid, gid, 0500, time)
        parent, dir = os.path.split(path)
        info = self.content.get(parent)
        if info:
            info[0].append(dir)
    
    def add_file(self, path, real_path, uid, gid):
        """
        Create a virtual file "pointing to" a real file. The parent directory
        must have been created before. The virtual file will be owned by the
        given uid and gid. Its access mode will be the same as the real file
        without write access.
        """
        path_info = self.content.get(path)
        if path_info is not None:
            if path_info != (real_path, uid, gid, None, None):
                raise ValueError('Virtual file %s already exists' % path)
        else:
            self.content[path] = (real_path, uid, gid, None, None)
            parent, file = os.path.split(path)
            info = self.content.get(parent)
            if info:
                info[0].append(file)
            else:
                raise ValueError('Virtual directory %s does not exist' % parent)

    
    def stat(self, path):
        """
        Return a dictionary similar to the result of os.fstat for the given
        virtual path.
        """
        info = self.content.get(path)
        if info is None:
            raise FuseOSError(ENOENT)
        real_path, uid, gid, mode, time = info
        result = dict(st_uid=uid, st_gid=gid)
        if isinstance(real_path, basestring):
            # path is a real file
            st = os.lstat(real_path)
            # TODO: Remove write access on st_mode
            result.update(dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                                'st_mode', 'st_mtime', 'st_nlink', 'st_size')))
            
        else:
            # path is a virtual directory
            result['st_mode'] = stat.S_IFDIR + mode
            result['st_atime'] = time
            result['st_ctime'] = time
            result['st_mtime'] = time
            # I do not know exactly what is st_nlinks. I decided to set it to
            # the number of entries returned by self.readdir(path)
            result['st_nlink'] = len(real_path)+2
            result['st_size'] = 4096
        return result

    
    def listdir(self, path):
        """
        Return a generator yielding the content of a virtual directory. Behave
        much like os.listdir() but the result also contains '.' and '..' at
        the begining.
        """
        info = self.content.get(path)
        if info is None:
            raise FuseOSError(ENOENT)
        real_path, uid, gid, mode, time = info
        if isinstance(real_path, list):
            yield '.'
            yield '..'
            for path in real_path:
                yield path
        else:
            raise FuseOSError(ENOTDIR)
    
    
    def get_real_path(self, path):
        """
        For a file, returns the real path for a given virtual path.
        """
        info = self.content.get(path)
        if info is None:
            raise FuseOSError(ENOENT)
        real_path, uid, gid, mode, time = info
        return real_path


class FuseRset(LoggingMixIn, Operations):
    def __init__(self, instance, login):
        self.instance = instance
        self.login = login
        try:
            pw = getpwnam(self.login)
        except KeyError:
            print >> sys.stderr, 'ERROR: unknown user %s' % login
            sys.exit(1)
        self.uid = pw.pw_uid
        self.gid = pw.pw_gid
        print '! login =', self.login, 'uid =', self.uid, 'gid =', self.gid
        self.vdir = None
        self.update()
        
        
    self.update(self):
        print '! starting update'
        # Get a connection to Cubicweb
        cw_connection = get_cw_connection(self.instance)
        try:
            cw_session = cw_connection.session
            data_root_dir = get_cw_basedir(self.instance)
            
            # Create an empty virtual directory
            self.vdir = VirtualDirectory(data_root_dir)
            # Get the current time for virtual directories times
            now = time.time()
            for cwsearch, cwsearch_name in cw_session.execute('Any S, N WHERE S is CWSearch, S name N, S owned_by U, U login "%s"' % self.login):
                print '! Processing CWSearch "%s"' % cwsearch_name
                files_data = cw_session.execute('Any D WHERE S is CWSearch, S eid %(eid)s, S result F, F data D', dict(eid=cwsearch))[0]
                files = json.load(files_data[0])['files']
                print '! Found %d valid files for "%s"' % (len(files), cwsearch_name)
                for file in files:
                    # Remove data_root_dir from the begining of the path
                    if file.startswith(data_root_dir):
                        path = file[len(data_root_dir):]
                    # Adds CWSearch name to path
                    if os.path.isabs(path):
                        path = os.path.join(cwsearch_name, path[1:])
                    else:
                        path = os.path.join(cwsearch_name, path)
                    # Make sure all parent virtual directories are created
                    virtual_path = path.split(os.path.sep)
                    # Paths send by fuse are absolute => adds op.path.sep at
                    # the begining
                    virtual_path.insert(0, os.path.sep)
                    for i in xrange(1, len(virtual_path)):
                        dir_full_path = os.path.join(*virtual_path[:i])
                        self.make_directory(dir_full_path, uid, gid, now)
                    self.add_file(path, file, uid, gid)
        finally:
            cw_connection.shutdown()
        print '! update done'


        
    # Filesystem methods
    # ==================

    # access is not called if 'default_permissions' mount option is used
    #def access(self, path, mode):
        #return 0
        
    def getattr(self, path, fh=None):
        return self.vdir.stat(path)
    
    
    def opendir(self, path):
        """
        opendir is useless here because the path is always given to readdir().
        Always return 0.
        """
        return 0


    def readdir(self, path, fh):
        return self.vdir.listdir(path)


    def releasedir(self, path, fh):
        """
        As for opendir, we do not use releasedir.
        """
        return 0


    # File methods
    # ============

    def open(self, path, flags):
        if flags & (os.O_RDWR + os.O_WRONLY):
            raise FuseOSError(EROFS)
        return os.open(self.vdir.get_real_path(path), flags)

    def read(self, path, length, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def release(self, path, fh):
        return os.close(fh)


    # Forbidden methods
    #==================


    def chmod(self, path, mode):
        raise FuseOSError(EROFS)

    def chown(self, path, uid, gid):
        raise FuseOSError(EROFS)

    def create(self, path, mode, fi=None):
        '''
        When raw_fi is False (default case), fi is None and create should
        return a numerical file handle.

        When raw_fi is True the file handle should be set directly by create
        and return 0.
        '''
        raise FuseOSError(EROFS)

    def flush(self, path, fh):
        raise FuseOSError(ENOTSUP)

    def fsync(self, path, datasync, fh):
        raise FuseOSError(ENOTSUP)

    def fsyncdir(self, path, datasync, fh):
        raise FuseOSError(ENOTSUP)

    def link(self, target, source):
        'creates a hard link `target -> source` (e.g. ln source target)'
        raise FuseOSError(EROFS)

    def mkdir(self, path, mode):
        raise FuseOSError(EROFS)

    def mknod(self, path, mode, dev):
        raise FuseOSError(EROFS)

    def readlink(self, path):
        raise FuseOSError(ENOTSUP)

    def removexattr(self, path, name):
        raise FuseOSError(ENOTSUP)

    def rename(self, old, new):
        raise FuseOSError(EROFS)

    def rmdir(self, path):
        raise FuseOSError(EROFS)

    def setxattr(self, path, name, value, options, position=0):
        raise FuseOSError(ENOTSUP)

    def statfs(self, path):
        '''
        Returns a dictionary with keys identical to the statvfs C structure of
        statvfs(3).

        On Mac OS X f_bsize and f_frsize must be a power of 2
        (minimum 512).
        '''
        raise FuseOSError(ENOTSUP)

    def symlink(self, target, source):
        'creates a symlink `target -> source` (e.g. ln -s source target)'
        raise FuseOSError(EROFS)

    def truncate(self, path, length, fh=None):
        raise FuseOSError(EROFS)

    def unlink(self, path):
        raise FuseOSError(EROFS)

    def utimens(self, path, times=None):
        'Times is a (atime, mtime) tuple. If None use current time.'
        raise FuseOSError(ENOTSUP)

    def write(self, path, data, offset, fh):
        raise FuseOSError(EROFS)


# To tune parameters
instance_name = sys.argv[1]
login = sys.argv[2]
print instance_name, login

# Get the CWSreach names owned by the user
mih = get_cw_connection(instance_name)
rset = mih.session.execute("Any SN WHERE X is CWSearch, X name SN")
print rset
mih.shutdown()

# Get the rql_download basedir
print get_cw_basedir(instance_name, "sftp_server_basedir")


