#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import subprocess
import sys
import json
import os.path as osp
import datetime

# RQL import
from rql.nodes import Constant

# CW import
from cubicweb import Binary, ValidationError
from cubicweb.server import hook
from cubicweb.selectors import is_instance


###############################################################################
# CW search main hooks
###############################################################################

class CWSearchAdd(hook.Hook):
    """ CubicWeb hook that is called before adding the new CWSearch entity.
    """
    __regid__ = "rqldownload.search_add_hook"
    __select__ = hook.Hook.__select__ & is_instance("CWSearch")
    events = ("before_add_entity",)

    def _find_constant_nodes(self, nodes, constant_nodes):
        """ Method that finds all leaf entity constant nodes.

        Parameters
        ----------
        nodes: rql.Nodes (mandatory)
            the rql structure.
        constant_nodes: dict of list of 2-uplet of the form (str, str)
            a dict with element types as key containing a list of constant
            nodes. Each item of the list is a 2-uplet that contains
            the entity name and the rql corresponding variable name.
        """
        # Go through all rql nodes
        for node in nodes:

            # If a leaf constant node is reached
            if isinstance(node, Constant):

                # Get the entity name and related parameter name in the rql
                if node.type not in constant_nodes:
                    constant_nodes[node.type] = []
                rql_type = node.parent
                rql_expression = rql_type.parent.children
                index = int(not(rql_expression.index(rql_type)))
                variable_name = rql_expression[index].name
                constant_nodes[node.type].append((node.value, variable_name))

            # Otherwise go deaper
            else:
                self._find_constant_nodes(node.children, constant_nodes)

    def __call__(self):
        """ Before adding the CWSearch entity, create a 'rset' and a 'result.json'
        File entities that contain all the filepath attached to the current
        rql request.
        Filepath are found by patching the rql request with the declared
        'rqldownload-adaptors' actions.
        A 'json_export' is used to export the rset.

        When an 'EntityAdaptor' is used, an 'ecsvexport' is used to export the
        entities contents.
        No file are then attached in the 'result.json' file.

        .. note::
            For the moment we expect only one entity node (type = 'etype'), we
            consider the first declared action, and we assume the database
            intergrity (ie. all file pathes inserted in the db exist on the
            file system) and thus do not check to speed up the hook.
        """
        # Get the rql/export type from the CWSearch form
        rql = self.entity.cw_edited.get("request")
        export_vid = "jsonexport"  # self.entity.cw_edited.get("rset_type")

        # Execute the rql
        # ToDo: try to get the current request cw_rset
        rset = self._cw.execute(rql)

        # Find constant nodes
        constant_nodes = {}
        self._find_constant_nodes(rset._rqlst.children, constant_nodes)

        # Select the appropriate action
        # We expect only one entity node: type = 'etype'
        actions = []
        if len(constant_nodes.get("etype", [])) == 1:

            # Get the entity type and associated rql parameter name: current
            # context
            etype, parameter_name = constant_nodes["etype"][0]

            # Get all the rqldownload declared adaptors
            possible_actions = self._cw.vreg["actions"]["rqldownload-adaptors"]

            # Keep only actions that respect the current context
            for action in possible_actions:
                for selector in action.__select__.selectors:
                    if (isinstance(selector, is_instance) and
                       etype in selector.expected_etypes):
                        actions.append((action, parameter_name))

        # Check that at least one action has been found for this request
        if actions == []:
            raise ValidationError(
                "CWSearch", {
                    "actions": _('cannot find an action for this request '
                                 '{0}'.format(rql))})

        # Create an empty result structure
        result = {"rql": rql, "files": [], "nonexistent-files": []}

        # Here we want to execute rql request with user permissions: user who
        # is creating this entity
        with self._cw.security_enabled(read=True, write=True):

            # Create the global rql from the first declared action
            # For the moment do not consider the others
            action, parameter_name = actions[0]

            # If the action is of EntityAdaptor type, export the entity content
            if action.__name__ == "EntityAdaptor":
                export_vid = "ecsvexport"

            global_rql = action(self._cw).rql(rql, parameter_name)
            rset = self._cw.execute(global_rql)
            result["rql"] = global_rql

            # Because self._cw is not a cubicwebRequest add an empty form
            # parameter
            self._cw.__dict__["form"] = {}
            try:
                view = self._cw.vreg["views"].select(
                    export_vid, self._cw, rset=rset)
                rset_view = Binary()
                view.w = rset_view.write
                view.call()
            except:
                raise ValidationError(
                    "CWSearch", {
                        "rset_type": _('cannot apply this view "{0}" on this '
                                       'rset, choose another view '
                                       'id'.format(export_vid))})

            # Save the rset in a File entity
            f_eid = self._cw.create_entity(
                "File", data=rset_view,
                data_format=view.content_type or u"text",
                data_name=u"rset").eid

            # Entity modification related event: specify that the rset has been
            # modified
            self.entity.cw_edited["rset"] = f_eid

            # Get all the files attached to the current request
            # Note: we assume the database intergrity (ie. all file pathes
            # inserted in the db exist on the file system) and thus do not
            # check to speed up this process.
            files_set = set()
            non_existent_files_set = set()
            if action.__name__ != "EntityAdaptor":
                files_set = tuple([row[0] for row in rset.rows])

            # Update the result structure
            result["files"] = list(files_set)
            result["nonexistent-files"] = list(non_existent_files_set)

            # Save the result in a File entity
            f_eid = self._cw.create_entity(
                "File", data=Binary(json.dumps(result)),
                data_format=u"text/json", data_name=u"result.json").eid

            # Entity modification related event: specify that the result has
            # been modified
            self.entity.cw_edited["result"] = f_eid


class CWSearchExpirationDateHook(hook.Hook):
    __regid__ = 'rsetftp.search_add_expiration_hook'
    __select__ = hook.Hook.__select__ & is_instance('CWSearch')
    events = ('before_add_entity', )

    def __call__(self):
        if 'expiration_date' not in self.entity.cw_edited:
            delay = self._cw.vreg.config['default_expiration_delay']
            self.entity.cw_edited['expiration_date'] = (
                datetime.date.today() + datetime.timedelta(delay))


###############################################################################
# CW search fuse hooks
###############################################################################

class CWSearchFuseMount(hook.Hook):
    """ Class that start/update a process specific to a user that mount
    his CWSearch entities.
    """
    __regid__ = "rqldownload.fuse_mount_hook"
    __select__ = hook.Hook.__select__ & is_instance("CWSearch")
    events = ("after_add_entity", )

    def __call__(self):
        """ Method that start/update the user specific process.
        """
        # Check if fuse virtual directory have to be mounted
        use_fuse = self._cw.vreg.config["start_user_fuse"]
        if use_fuse:

            # Update/Create action
            PostCommitFuseOperation(
                self._cw, _cw=self._cw, entity=self.entity)


class PostCommitFuseOperation(hook.Operation):
    """ Start/update a fuse process after a CWSearch entity is commited.
    """
    def postcommit_event(self):
        """ Define the FuseOperation postcommit operation.
        """
        # Get cw parameters
        repo = self._cw.repo
        instance_name = repo.schema.name
        login = self.entity.owned_by[0].login

        # Create a new fuse process: try first to update the fuse mount point
        # if already created otherwise create a new mount point.
        cmd = [sys.executable, "-m", "cubes.rql_download.fuse.fuse_mount",
               instance_name, login]
        process = subprocess.Popen(cmd)
        # Create zombie process, keep trace in memory to deal with them later.
        if "cw_fuse_zombies" not in globals():
            globals()["cw_fuse_zombies"] = [process]
        else:
            globals()["cw_fuse_zombies"].append(process)


class ServerStartupFuseMount(hook.Hook):
    """ On startup, generate all the fuse mount point associated with CWSearch
    owners."""
    __regid__ = "rqldownload.startup_fuse_mount_hook"
    events = ("server_startup",)

    def __call__(self):
        """ Method that start the user specific processes.
        """
        # Check if fuse virtual directory have to be mounted
        use_fuse = self.repo.vreg.config["start_user_fuse"]
        if use_fuse:

            # Execute a rql to get all the CWSearch owner logins
            with self.repo.internal_session() as cnx:
                rql = "Any L Where S is CWSearch, S owned_by U, U login L"
                rset = cnx.execute(rql)
                logins = set([x[0] for x in rset])

            # Start a fuse deamon for each user
            instance_name = self.repo.schema.name
            for user in logins:
                cmd = [sys.executable, "-m",
                       "cubes.rql_download.fuse.fuse_mount",
                       instance_name, user]
                subprocess.Popen(cmd)


class ServerStartupFuseZombiesLoop(hook.Hook):
    """ On startup, register a task to clean zombie (defunc) processes stored
    in the 'cw_fuse_zombies' global parameter.
    """
    __regid__ = "rqldownload.startup_fuse_zombies_loop"
    events = ("server_startup", )

    def __call__(self):
        """ Start a loop to clean zombie processes.
        """
        # Specify the refresh time in days: every minute here
        dt = datetime.timedelta(1. / 1440.)

        # Define the cleaning function
        def cleaning_cw_fuse_zombies():
            if "cw_fuse_zombies" in globals():
                for process in globals()["cw_fuse_zombies"]:
                    if process.poll() is not None:
                        process.wait()
                        globals()["cw_fuse_zombies"].remove(process)

        # Register the cleaning looping task
        self.repo.looping_task(dt.total_seconds(), cleaning_cw_fuse_zombies)


###############################################################################
# CW search twisted hook
###############################################################################

class ServerStartupHook(hook.Hook):
    """on startup, register a task to delete old CWSearch entity"""
    __regid__ = 'rsetftp.search_delete_hook'
    events = ('server_startup',)

    def __call__(self):
        dt = datetime.timedelta(0.5)  # 12h

        def cleaning_old_cwsearch(repo):
            with repo.internal_session() as cnx:
                cnx.execute(
                    'DELETE CWSearch S WHERE S expiration_date < today')
                cnx.commit()
        cleaning_old_cwsearch(self.repo)
        self.repo.looping_task(
            dt.total_seconds(), cleaning_old_cwsearch, self.repo)


class LaunchFTPServer(hook.Hook):
    """on startup launch ftp server"""
    __regid__ = 'rsetftp.launch_server'
    events = ('server_startup',)

    def __call__(self):
        if self.repo.vreg.config['start_sftp_server']:
            cube_path = osp.dirname(osp.abspath(__file__))
            ftpserver_path = osp.join(cube_path, 'ftpserver/main.py')
            basedir_opt = ''
            sftp_server_basedir = self.repo.vreg.config['basedir']
            if sftp_server_basedir:
                basedir_opt = '--base-dir=%s' % sftp_server_basedir
            subprocess.Popen([sys.executable, ftpserver_path, basedir_opt])
