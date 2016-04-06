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
import os
import datetime

# RQL import
from rql.nodes import Constant, Function

# CW import
from cubicweb import NotAnEntity
from cubicweb import Binary, ValidationError
from cubicweb.server import hook
from cubicweb.predicates import is_instance

_ = unicode


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

            # Skip function node
            if isinstance(node, Function):
                continue

            # If a leaf constant node is reached
            elif isinstance(node, Constant):

                # Get the entity name and related parameter name in the rql
                if node.type not in constant_nodes:
                    constant_nodes[node.type] = {}
                rql_type = node.parent
                rql_expression = rql_type.parent.children
                index = int(not(rql_expression.index(rql_type)))
                variable_name = rql_expression[index].name
                if node.value not in constant_nodes[node.type]:
                    constant_nodes[node.type][node.value] = []
                constant_nodes[node.type][node.value].append(variable_name)

            # Otherwise go deaper
            else:
                self._find_constant_nodes(node.children, constant_nodes)

    def __call__(self):
        """ Before adding the CWSearch entity, create a 'rset' and a
        'result.json' File entities that contain all the filepath attached
        to the current rql request.
        Filepath are found by patching the rql request with the declared
        'rqldownload-adaptors' actions.
        The '__rset_type__' adaptor attribute is used to export the rset.

        When an 'ecsvexport' is used, no file are then attached in
        the 'result.json' file.

        .. warning::

            For the moment we assume the database intergrity (ie. all file
            paths inserted in the db exist on the file system) and thus do not
            check to speed up the hook.
        """
        # Get the rql/export type from the CWSearch form
        rql = self.entity.cw_edited.get("path")

        # Execute the rql
        # ToDo: try to get the current request cw_rset
        rset = self._cw.execute(rql)

        # Get all the entities
        entities = {}
        if rset.rowcount > 0:
            for rowindex in range(len(rset[0])):
                try:
                    entity = rset.get_entity(0, rowindex)
                    entity_type = entity.__class__.__name__
                    entities[rowindex] = entity_type
                except NotAnEntity:
                    pass
                except:
                    raise
        if len(entities) == 0:
            raise ValidationError(
                "CWSearch", {
                    "entities": _('cannot find any entity for the request '
                                  '{0}'.format(rql))})

        # Find the constant nodes
        constant_nodes = {}
	
        self._find_constant_nodes(rset.syntax_tree().children, constant_nodes)

        # Check we can associated rset entities with their rql labels
        actions = []
        rql_etypes = constant_nodes.get("etype", {})
        for etype in entities.values():
            if etype not in rql_etypes or len(rql_etypes[etype]) != 1:
                raise ValidationError(
                    "CWSearch", {
                        "rql": _('cannot find entity description in the'
                                 'request {0}. Expect something like "Any X'
                                 'Where X is '
                                 '{1}, ..."'.format(rql, etype))})

        # Get all the rqldownload declared adapters
        possible_actions = self._cw.vreg["actions"]["rqldownload-adapters"]

        # Keep only actions that respect the current context
        actions = {}
        export_vids = set()
        for index, etype in entities.items():
            entity_label = rql_etypes[etype][0]
            for action in possible_actions:
                for selector in action.__select__.selectors:
                    if (isinstance(selector, is_instance) and
                       etype in selector.expected_etypes):
                        actions.setdefault(etype, []).append(
                            (action, entity_label))
                        export_vids.add(unicode(action.__rset_type__))

        # Check that at least one action has been found for this request
        if actions == []:
            raise ValidationError(
                "CWSearch", {
                    "actions": _('cannot find an action for this request '
                                 '{0}'.format(rql))})

        # Check that the export types are homogeneous
        if len(export_vids) != 1:
            raise ValidationError(
                "CWSearch", {
                    "actions": _('cannot deal with different action export '
                                 'types: {0}'.format(export_vids))})
        export_vid = export_vids.pop()

        # Create an empty result structure
        result = {"rql": rql, "files": [], "nonexistent-files": [],
                  "upper_file_index": 0}

        # Here we want to execute rql request with user permissions: user who
        # is creating this entity
        with self._cw.security_enabled(read=True, write=True):

            # Set the adaptor rset type
            self.entity.cw_edited["rset_type"] = export_vid

            # Create the global rql from the declared actions
            global_rql = rql
            cnt = 1
            upper_file_index = 0
            for etype, action_item in actions.items():
                for action, entity_label in action_item:
                    global_rql, nb_files = action(self._cw).rql(
                        global_rql, entity_label, cnt)
                    upper_file_index += nb_files
                    cnt += 1
            result["upper_file_index"] = upper_file_index

            # Execute the global rql
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
                data_format=unicode(view.content_type) or u"text",
                data_name=u"rset").eid

            # Entity modification related event: specify that the rset has been
            # modified
            self.entity.cw_edited["rset"] = f_eid

            # Get all the files attached to the current request
            # Note: we assume the database intergrity (ie. all file paths
            # inserted in the db exist on the file system) and thus do not
            # check to speed up this process.
            files_set = set()
            non_existent_files_set = set()
            if export_vid != "ecsvexport":
                for rset_row in rset.rows:
                    for rset_index in range(upper_file_index):
                        files_set.add(rset_row[rset_index])

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
    """ On startup, register a task to add an expiration date to each CWSearch.
    """
    __regid__ = "rsetftp.search_add_expiration_hook"
    __select__ = hook.Hook.__select__ & is_instance("CWSearch")
    events = ("before_add_entity", )

    def __call__(self):
        """ Method to execute the 'CWSearchExpirationDateHook' hook.
        """
        if "expiration_date" not in self.entity.cw_edited:
            delay = self._cw.vreg.config["default_expiration_delay"]
            self.entity.cw_edited["expiration_date"] = (
                datetime.date.today() + datetime.timedelta(delay))


class CWSearchDelete(hook.Hook):
    """ On startup, register a task to delete old CWSearch entities.
    """
    __regid__ = "rqldownload.search_delete_hook"
    events = ("server_startup",)

    def __call__(self):
        """ Method to execute the 'CWSearchDelete' hook.
        """
        def cleaning_old_cwsearch(repo):
            """ Delete all CWSearch entities that have expired.
            """
            with repo.internal_cnx() as cnx:
                cnx.execute(
                    "DELETE CWSearch S WHERE S expiration_date < today")
                cnx.commit()

        # Set the cleaning event loop
        dt = datetime.timedelta(0.5)  # 12h
        self.repo.looping_task(
            dt.total_seconds(), cleaning_old_cwsearch, self.repo)

        # Call the clean function manually on the startup
        cleaning_old_cwsearch(self.repo)


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
            with self.repo.internal_cnx() as cnx:
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
                fuse_zombies = globals()["cw_fuse_zombies"]
                if fuse_zombies is None:
                    fuse_zombies = []
                for process in fuse_zombies:
                    if process.poll() is not None:
                        process.wait()
                        globals()["cw_fuse_zombies"].remove(process)

        # Register the cleaning looping task
        self.repo.looping_task(dt.total_seconds(), cleaning_cw_fuse_zombies)


class ServerShutdownKillFuseProcess(hook.Hook):
    """
    When the server is going down, kill the Fuse process and unmount the
    user's repository. They will be automatically restored when server starts
    again.
    """
    __regid__ = "rqldownload.shutdown_fuse_process"
    events = ("server_shutdown", )

    def __call__(self):
        """ Start a loop to clean fuse processes and unmount fuse repository.
        """
        # Get the chroot dir
        mount_base = self.repo.config.get("mountdir")
        if not os.path.isdir(mount_base):
            return

        # Deal with all users in the chroor dir
        for uid in os.listdir(mount_base):

            # Get the fuse mount point
            mount_point = os.path.join(mount_base, fuse_folder,
                                       self.repo.schema.name)

            # Kill the fuse mount if fuse mount is active
            if os.path.isdir(mount_point):
                try:
                    os.stat(os.path.join(mount_point, ".kill"))
                except:
                    pass


###############################################################################
# CW search twisted hook
###############################################################################

class LaunchTwistedFTPServer(hook.Hook):
    """ On startup launch the twisted sftp server.

    If the option 'start_sftp_server' is set to True in the configuration file
    execute the the 'twistedserver/main.py' script to start the sftp server.
    """
    __regid__ = "rqldownload.launch_twisted_server"
    events = ("server_startup",)

    def __call__(self):
        """ Start the sftp server when starting the instance if the
        'start_sftp_server' option is set to True.
        """
        if self.repo.vreg.config["start_sftp_server"]:
            cube_path = os.path.join(os.path.dirname(
                os.path.abspath(__file__)))
            ftpserver_path = os.path.join(cube_path,
                                          "twistedserver/main.py")
            basedir_opt = ""
            sftp_server_basedir = self.repo.vreg.config["basedir"]
            if sftp_server_basedir:
                basedir_opt = "--base-dir=%s" % sftp_server_basedir
            subprocess.Popen([sys.executable, ftpserver_path, basedir_opt])
