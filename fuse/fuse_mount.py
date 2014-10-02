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



# To tune parameters
instance_name = "test"

# Get the CWSreach names owned by the user
mih = get_cw_connection(instance_name)
rset = mih.session.execute("Any SN WHERE X is CWSearch, X name SN")
print rset
mih.shutdown()

# Get the rql_download basedir
print get_cw_basedir(instance_name, "sftp_server_basedir")


