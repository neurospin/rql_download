#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import grp
from optparse import OptionParser
import os

# LDAP import
import ldap


# Parse the command line
parser = OptionParser()
parser.add_option("-g", "--gname", dest="group_name",
                  help="the group name from which we want to retrieve the "
                       "users (system or ldap).")
parser.add_option("-l", "--ldap",
                  action="store_true", dest="use_ldap", default=False,
                  help="search on ldap.")
parser.add_option("-b", "--basedir", dest="basedir",
                  help="the basedir where the user home will be built.")
parser.add_option("-n", "--dbname", dest="db_name",
                  help="the cw database instance name.")
parser.add_option("-a", "--ldapaddr", dest="uri",
                  help="the ldap address.")
parser.add_option("-c", "--ldapuser", dest="user",
                  help="the ldap user login.")
parser.add_option("-p", "--ldappwd", dest="password",
                  help="the ldap user password.")
parser.add_option("-u", "--user", dest="user",
                  help="a specific user.")
(options, args) = parser.parse_args()


# List the system and ldap users
# > system
if not options.use_ldap:
    sys_group = grp.getgrnam(options.group_name)
    members = sys_group.gr_mem
else:
    members = []
if options.user:
    members.append(options.user)

# Create the home of each member
for m in members:
    fuse_home = os.path.join(options.basedir, "home", m, "rql_download",
                             options.db_name)
    if not os.path.isdir(fuse_home):
        os.makedirs(fuse_home, 0755)
