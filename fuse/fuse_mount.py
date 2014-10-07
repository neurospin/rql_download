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
import stat
import json
import time
import pwd
import logging
import datetime

# Define the logger
logger = logging.getLogger("fuse.log-mixin")

# CW import
from cubicweb.cwconfig import CubicWebConfiguration as cwcfg

# Fuse import
from cubes.rql_download.fuse.fuse import (FUSE,
                                          FuseOSError,
                                          Operations,
                                          ENOENT,
                                          ENOTDIR,
                                          EROFS,
                                          ENOTSUP)

# The following import can be used to help debugging but is dangerous because
# the content of all fuse actions (even the binary content of files) is
# printed on the log. In order to debug is also necessary to add LoggingMixIn
# to FuseRset below.
# from cubes.rql_download.fuse.fuse import LoggingMixIn


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


def get_cw_option(instance_name, cw_option):
    """ Get a cw option.

    Parameters
    ----------
    instance_name: str (mandatory)
        the name of the cw instance we want to connect.
    cw_option: str (mandatory)
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
                if name == cw_option:
                    return value

    # If the basedir parameter is nor found raise an exception
    raise Exception("No '{0}' option has been declared in the '{1}' "
                    "configuration file.".format(cw_option, config_file))


class VirtualDirectory(object):
    """ Build an internal representation of a full virtual directory to allow
    easy and fast usge of this directory with fuse.
    """
    def __init__(self, root_data_dir):
        """ Creates an empty virtual directory.

        The virtual directory can be populated with make_directory()
        and add_file().
        Its content can be accessed with stat(), listdir() and get_real_path().

        Parameters
        ----------
        root_data_dir: str (mandatory)
            parameter used to mask a part of the file path.
        """
        # Class parameters
        self.root_data_dir = root_data_dir
        self.content = {}

    def make_directory(self, path, uid, gid, time):
        """ Create a virtual directory.

        The parent directory must have been created before.
        The new directory will be owned by the given uid and
        gid.
        Its access mode will be 0500 (read and executable for user only).
        At each access, a modification times will be set to the given time.

        Parameters
        ----------
        path: str (mandatory)
            the virtual path we want to create.
        uid: str (mandatory)
            the user identifier.
        gid: str (mandatory)
            the user group identifier.
        time: str (mandatory)
            the create time that will be set to the created path.
        """
        # Try to get the path informations: get something if the
        # the path has already been created
        path_info = self.content.get(path)
        
        # Create a special mask for the root element in irder to be able to
        # update fuse as the cw master
        mask = 0500
        if path == "/":
            mask = 0555

        # If the path is already created, check the that the path information
        # are correct
        if path_info is not None:
            if path_info[1:] != (uid, gid, mask, time):
                raise ValueError(
                    "Virtual directory '{0}' already exists".format(path))

        # Otherwise, create a new virtual path
        else:
            # Path creation
            self.content[path] = ([], uid, gid, mask, time)

            # Link the current path to the global tree
            # > get the parent directory name and current directory name
            if path == "/":
                parentdir_name = None
                currentdir_name = "/"
            else:
                parentdir_name, currentdir_name = os.path.split(path)
            # > get the parant path informations
            parentpath_info = self.content.get(parentdir_name)
            # > add the current path to the parent info structure
            if parentpath_info:
                parentpath_info[0].append(currentdir_name)

    def add_file(self, path, real_path, uid, gid):
        """ Create a virtual file 'pointing to' a real file.

        The parent directory must have been created before.
        The virtual file will be owned by the given uid and gid.
        Its access mode will be the same as the real file without write access.

        Parameters
        ----------
        path: str (mandatory)
            the virtual file path we want to create.
        real_path: str (mandatory)
            the real file location, where the virtual file point to.
        uid: str (mandatory)
            the user identifier.
        gid: str (mandatory)
            the user group identifier.
        """
        # Try to get the file informations: get something if the
        # the file has already been created
        path_info = self.content.get(path)

        # If the file is already created, check the that the file information
        # are correct
        if path_info is not None:
            if path_info != (real_path, uid, gid, None, None):
                raise ValueError(
                    "Virtual file '{0}' already exists".format(path))

        # Otherwise, create a new virtual file pointing to a real one
        else:
            # File creation: point to the real file
            self.content[path] = (real_path, uid, gid, None, None)

            # Link the current file to the global tree
            # > get the parent directory name and current file name
            parentdir_name, file_name = os.path.split(path)
            # > get the parant path informations
            parentpath_info = self.content.get(parentdir_name)
            # > add the current file to the parent info structure
            if parentpath_info:
                parentpath_info[0].append(file_name)
            else:
                raise ValueError(
                    "Virtual directory '{0}' does not exist".format(
                        parentdir_name))

    def stat(self, path):
        """ Return a dictionary similar to the result of os.fstat for the
        given virtual path.

        .. note::
            raise a 'FuseOSError' exception if the path does not exist.

        Parameters
        ----------
        path: str (mandatory)
            a virtual path we want to check.
        """
        # Try to get the path informations: get something if the
        # the path exists
        path_info = self.content.get(path)

        # If the path does not exist, raise a 'FuseOSError' exception
        if path_info is None:
            raise FuseOSError(ENOENT)

        # Unpack path information
        real_path, uid, gid, mode, ctime = path_info

        # Initilaize the output
        result = dict(st_uid=uid, st_gid=gid)

        # Path link to a real file
        if isinstance(real_path, basestring):
            st = os.lstat(real_path)
            # TODO: Remove write access on st_mode
            result.update(
                dict((key, getattr(st, key))
                     for key in ("st_atime", "st_ctime", "st_mode",
                                 "st_mtime", "st_nlink", "st_size")))
        # Path is a virtual directory
        else:
            result["st_mode"] = stat.S_IFDIR + mode
            result["st_atime"] = ctime
            result["st_ctime"] = ctime
            result["st_mtime"] = ctime
            # st_nlinks is the number of reference to the directory a:
            # the number of sub folders in a pointing to a +
            # a has a referece to itself and the parent directory has
            # a reference to a.
            result["st_nlink"] = len(real_path) + 2
            result["st_size"] = 4096

        return result

    def listdir(self, path):
        """ Return a generator yielding the content of a virtual directory.

        Behave much like os.listdir() but the result also contains '.' and
        '..' at the begining.

        .. note::
            raise a 'FuseOSError' exception if the path does not exist or
            the path is not a directory.

        Parameters
        ----------
        path: str (mandatory)
            a virtual path we want to list.
        """
        # Try to get the path informations: get something if the
        # the path exists
        path_info = self.content.get(path)

        # If the path does not exist, raise a 'FuseOSError' exception
        if path_info is None:
            raise FuseOSError(ENOENT)

        # Unpack path information
        real_path, uid, gid, mode, ctime = path_info

        # Path is a virtual directory
        if isinstance(real_path, list):
            yield "."
            yield ".."
            for path in real_path:
                yield path
        # Otherwise raise an exception
        else:
            raise FuseOSError(ENOTDIR)

    def get_real_path(self, path):
        """ For a file, returns the real path for a given virtual path.

        .. note::
            raise a 'FuseOSError' exception if the path does not exist or
            the path is not a file.

        Parameters
        ----------
        path: str (mandatory)
            a virtual file from which we want to extract his real path.
        """
        # Try to get the file informations: get something if the
        # the path exists
        path_info = self.content.get(path)

        # If the path does not exist, raise a 'FuseOSError' exception
        if path_info is None:
            raise FuseOSError(ENOENT)

        # Unpack path information
        real_path, uid, gid, mode, ctime = path_info

        # Path is a virtual file
        if isinstance(real_path, basestring):
            return real_path
        # Otherwise raise an exception
        else:
            raise FuseOSError(ENOTDIR)


# If debug is necessary, add LoggingMixIn to FuseRset base classes
# class FuseRset(LoggingMixIn, Operations):
class FuseRset(Operations):
    """ Class that create a mount point containing virtual path representing
    the CWSearch entities of a cw user.
    """
    def __init__(self, instance, login):
        """ Initilize the FuseRset class.

        .. note::
            a user with 'login' login must exist on the system through ldap
            or the adduser command.

        Parameters
        ----------
        instance: str (mandatory)
            the cw instance name we want to connect
        login: str (mandatory)
            the cw login
        """
        # Class parameters
        self.instance = instance
        self.login = login
        self.vdir = None  # the virtual directory object

        # Get the directory where to generate the user acces log
        # Check the permissions
        log_dir = get_cw_option(self.instance, "rql_download_log")
        self.generate_log = (os.access(log_dir, os.F_OK) and
                     os.access(log_dir, os.W_OK))
        if self.generate_log:
            self.log_file = open(os.path.join(
                log_dir, "rql_download_{0}.log".format(self.login)), "a")


        # Get the user uid and gid
        try:
            pw = pwd.getpwnam(self.login)
        except KeyError:
            raise Exception("Unknown user '{0}'. A user with 'login' login "
                            "must exist on the system through ldap or the "
                            "adduser command.".format(login))
        self.uid = pw.pw_uid
        self.gid = pw.pw_gid
        logger.debug("! login = {0}; uid = {1}; gid = {2}".format(
            self.login, self.uid, self.gid))

        # Create the virtual directory
        self.update()

    def update(self):
        """ Method that create a virtual directory from a user CWSearch
        entities results.
        """

        # Message
        logger.debug("! starting virtual direcotry update")

        # Get a Cubicweb in memory connection
        cw_connection = get_cw_connection(self.instance)

        try:
            # Get the cw session to execute rql requests
            cw_session = cw_connection.session

            # From the cw configuration file, get the mask we will apply
            # on the virtual tree
            data_root_dir = get_cw_option(self.instance, "basedir")

            # Create an empty virtual directory
            self.vdir = VirtualDirectory(data_root_dir)

            # Get the current time for virtual directories times
            now = time.time()

            # Go through all the user CWSearch entities
            rql = ("Any S, N WHERE S is CWSearch, S name N, S owned_by U, "
                   "U login '{0}'".format(self.login))
            for cwsearch_eid, cwsearch_name in cw_session.execute(rql):

                # Message
                logger.debug(
                    "! Processing CWSearch '{0}'".format(cwsearch_name))

                # Get the files associated to the current CWSearch
                rql = "Any D WHERE S eid '{0}', S result F, F data D".format(
                    cwsearch_eid)
                files_data = cw_session.execute(rql)[0]

                # Get the downloadable files path from the json
                files = json.load(files_data[0])["files"]
                logger.debug("! Found {0} valid files for '{1}'".format(
                    len(files), cwsearch_name))

                # Go through all files and create the virtual direcotry
                for fname in files:

                    # RApply the mask: rmove 'data_root_dir' from the
                    # begining of the path
                    if fname.startswith(data_root_dir):
                        path = fname[len(data_root_dir):]

                    # Add the CWSearch name to the path
                    if os.path.isabs(path):
                        path = os.path.join(cwsearch_name, path[1:])
                    else:
                        path = os.path.join(cwsearch_name, path)

                    # Paths send by fuse are absolute => adds os.path.sep at
                    # the begining
                    virtual_path = path.split(os.path.sep)
                    virtual_path.insert(0, os.path.sep)

                    # Make sure all parent virtual directories are created
                    for i in range(1, len(virtual_path)):
                        dir_full_path = os.path.join(*virtual_path[:i])
                        self.vdir.make_directory(
                            dir_full_path, self.uid, self.gid, now)

                    # Add the file to the fuse virtual tree
                    self.vdir.add_file(
                        os.path.join(*virtual_path), fname, self.uid, self.gid)

        # Shut down the cw connection
        finally:
            cw_connection.shutdown()

        # Message
        logger.debug("! update done")

    ########################################################################
    # Filesystem methods
    ########################################################################

    # access is not called if 'default_permissions' mount option is used
    # def access(self, path, mode):
    #    return 0

    def getattr(self, path, fh=None):
        """ Return a dict with stats on the given virtual path.

        .. note::
            when the stat method is called on the '/.isalive' fake folder,
            the method return a fake folder stat but do not raise an exception.
            This in turns unables us to check if the fuse process is running.

        .. note::
            when the stat method is called on the '/.update' fake folder,
            the virtual direcotry is recreated and the process may not be
            available during this operation.

        Parameters
        ----------
        path: str (mandatory)
            a virtual path
        """
        # Create a fake folder stat
        fstat = {
            "st_ctime": 1.,
            "st_mtime": 1.,
            "st_nlink": 1,
            "st_mode": 16704,
            "st_size": 4096,
            "st_gid": 5009,
            "st_uid": 5009,
            "st_atime": 1.
        }

        # Check if the fuse mount is alive
        if path == "/.isalive":
            return fstat

        # Start the fuse update: the process is not avalaible during the update
        elif path == "/.update":
            self.update()
            return fstat

        return self.vdir.stat(path)

    def opendir(self, path):
        """ Tis method is useless here because the path is always given to
        readdir().
        Always return 0.
        """
        return 0

    def readdir(self, path, fh):
        """ List the content of a directory.

        Parameters
        ----------
        path: str (mandatory)
            a virtual path
        """
        return self.vdir.listdir(path)

    def releasedir(self, path, fh):
        """ As for opendir, we do not use releasedir.
        """
        return 0

    ########################################################################
    # Implemented file methods
    ########################################################################

    def open(self, path, flags):
        # Update the log file if requested
        if self.generate_log:
            self.log_file.write(" ".join(
                [str(datetime.datetime.now()), self.instance, self.login,
                 path, str(os.path.isfile(path))]))
            self.log_file.write("\n")
            self.log_file.flush()
                
        print "OPEN::", path
        if flags & (os.O_RDWR + os.O_WRONLY):
            raise FuseOSError(EROFS)
        return os.open(self.vdir.get_real_path(path), flags)

    def read(self, path, length, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def release(self, path, fh):
        return os.close(fh)

    ########################################################################
    # Forbidden methods
    ########################################################################

    def chmod(self, path, mode):
        raise FuseOSError(EROFS)

    def chown(self, path, uid, gid):
        raise FuseOSError(EROFS)

    def create(self, path, mode, fi=None):
        raise FuseOSError(EROFS)

    def flush(self, path, fh):
        raise FuseOSError(ENOTSUP)

    def fsync(self, path, datasync, fh):
        raise FuseOSError(ENOTSUP)

    def fsyncdir(self, path, datasync, fh):
        raise FuseOSError(ENOTSUP)

    def link(self, target, source):
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
        raise FuseOSError(ENOTSUP)

    def symlink(self, target, source):
        raise FuseOSError(EROFS)

    def truncate(self, path, length, fh=None):
        raise FuseOSError(EROFS)

    def unlink(self, path):
        raise FuseOSError(EROFS)

    def utimens(self, path, times=None):
        raise FuseOSError(ENOTSUP)

    def write(self, path, data, offset, fh):
        raise FuseOSError(EROFS)

# Setup the logger: cubicweb change the logging config and thus
# we setup en axtra stream handler
# ToDo: fix it
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

# Command line parameters
instance_name = sys.argv[1]
login = sys.argv[2]
mount_base = get_cw_option(instance_name, "mountdir")
mount_point = os.path.join(mount_base, instance_name, login)
logger.debug("Command line parameters: instance name = {0}, login = {1} fuse "
             "mount point = {2}".format(instance_name, login, mount_point))

# Check if the user fuse mount point is available
isalive = True
try:
    os.stat(os.path.join(mount_point, ".isalive"))
except:
    isalive = False

# Add the new search to the user fuse mount point:
# if the process is already created, just start the update,
# otherwise create a fuse loop
if isalive:
    os.stat(os.path.join(mount_point, ".update"))
else:
    # Create the fuse mount point
    FUSE(FuseRset(instance_name, login),
         mount_point,
         foreground=True,
         allow_other=True,
         default_permissions=True)