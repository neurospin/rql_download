#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
> ldpa exemple:
    python create_home_deamon.py -g OPEN_FU1 -l -b /chroot_fuse -n imagen2 -p mypwd
"""
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
parser.add_option("-a", "--ldapaddr", dest="uri", default="ldap://127.0.0.1",
                  help="the ldap address.")
parser.add_option("-c", "--ldapuser", dest="user", default="admin",
                  help="the ldap user login.")
parser.add_option("-r", "--ldapbase", dest="base",
                  default="dc=imagen2,dc=cea,dc=fr",
                  help="the ldap base login.")
parser.add_option("-p", "--ldappwd", dest="password",
                  help="the ldap user password.")
parser.add_option("-i", "--cwuser", dest="cw_uid",
                  help="the cw instance user id.")                  
(options, args) = parser.parse_args()


# List the system and ldap users
# > system
if not options.use_ldap:
    sys_group = grp.getgrnam(options.group_name)
    members = sys_group.gr_mem
# > ldap
else:
    ldapobject = ldap.initialize(options.uri)
    ldapobject.simple_bind_s(
        "cn=" + options.user + "," + options.base, options.password)
    group = ldapobject.search_s(
        "cn={0},ou=Groups,{1}".format(options.group_name, options.base),
        ldap.SCOPE_BASE)
    members = group[0][1]["memberUid"]

# Create the home of each member
for m in members:
    fuse_home = os.path.join(options.basedir, "home", m, "rql_download",
                             options.db_name)
    if not os.path.isdir(fuse_home):
        os.makedirs(fuse_home, 0750)

    if not options.use_ldap:
        cw_uid = int(options.cw_uid)
        os.chown(os.path.join(options.basedir, "home", m), -1, cw_uid)
        os.chown(os.path.join(options.basedir, "home", m, "rql_download"),
                 cw_uid, cw_uid)
        os.chown(fuse_home, cw_uid, cw_uid)
    else:
        cw_uid = int(ldapobject.search_s(
            options.base, ldap.SCOPE_SUBTREE,
            "(uid={0})".format(m))[0][1]["uidNumber"][0])
        os.chown(os.path.join(options.basedir, "home", m), cw_uid, -1)
        os.chown(os.path.join(options.basedir, "home", m, "rql_download"),
                 cw_uid, -1)
        os.chown(fuse_home, cw_uid, -1)
        
