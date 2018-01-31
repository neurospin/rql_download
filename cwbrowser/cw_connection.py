##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2018
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
A module to connect a CubicWeb service and send requests.
"""

# System import
from __future__ import print_function
import os
import sys
import json
import time
import stat
import glob
import csv
try:
    # for Python 2.x
    from StringIO import StringIO
except ImportError:
    # for Python 3.x
    from io import StringIO

# Third party import
import requests
import numpy
import paramiko


def load_csv(text, delimiter=";"):
    """ Load a csv.

    Parameters
    ----------
    text: string (mandatory)
        the csv text.

    Returns
    -------
    csv_lines: list
        a list containing all the csv lines.
    """
    csv_stream = StringIO(text)
    reader = csv.reader(csv_stream, delimiter=delimiter)
    csv_lines = [line for line in reader]

    return csv_lines


class CWInstanceConnection(object):
    """ Tool to dump the data stored in a cw instance.

    .. code-block:: python

        # Import Connection module
        from cwbrowser.cw_connection import CWInstanceConnection

        # Create dummy rqls
        rql1 = ("Any C, G Where X is Subject, X code_in_study C, "
                "X handedness 'ambidextrous', X gender G")
        rql2 = ("Any S WHERE S is Scan, S has_data A, A field '3T', "
                "S in_assessment B, B timepoint 'V1', S format 'GIS', "
                "S in_assessment C, C concerns D, D code_in_study 'ab100207'")

        # HTTP test
        url = @HTTPURL; login = @LOGIN; password = @PWD
        connection = CWInstanceConnection(url, login, password, port=9191)
        connection.execute(rql1, export_type="json")
        connection.execute_with_sync(rql2, "/tmp/fuse", timer=1)

        # HTTPS test
        url = @HTTPSURL; login = @LOGIN; password = @PWD
        connection = CWInstanceConnection(url, login, password,
                                          server_root="/home/$login")
        connection.execute(rql)

    Attributes
    ----------
    url : str
        the url to the cw instance.
    login : str
        the cw login.
    opener:  OpenerDirector
        object that contains the connexion to the cw instance.
    """
    # Global variable that specify the supported export cw formats
    _EXPORT_TYPES = ["json", "csv", "cw"]
    importers = {
        "json": json.loads,
        "csv": load_csv,
        "cw": json.loads,
        "cwsearch": json.loads
    }

    def __init__(self, url, login, password, port=22, server_root=os.path.sep,
                 verify=True, verbosity=0):
        """ Initilize the HTTPConnection class.

        Parameters
        ----------
        url: str (mandatory)
            the url to the cw instance.
        login: str (mandatory)
            the cw login.
        password: str (mandatory)
            the cw user password.
        port: int (optional default 22)
            the sftp port.
        server_root: str (optional default '/')
            the server root directory where the user mount points (chroot) are
            mapped.
        verify: bool (optional, default True)
            if unset, disable the security certificate check.
        verbosity: int (optional default 0)
            the verbosity level.
        """
        # Class parameters
        if not url.startswith("https"):
            raise ValueError(
                "Authentication was requested on a non secured URL ({0})."
                "Request has been blocked for security reasons.".format(url))
        self.url = url
        self.login = login
        self.password = password
        self.host = self.url.split("/")[2].split(":")[0]
        self.port = port
        self.server_root = server_root
        self.verify = verify
        self.verbosity = verbosity

    ###########################################################################
    # Public Members
    ###########################################################################

    def execute(self, rql, export_type="json", nb_tries=2):
        """ Method that loads the rset from a rql request.

        Parameters
        ----------
        rql: str (mandatory)
            the rql rquest that will be executed on the cw instance.
        export_type: str (optional default 'json')
            the result set export format: one defined in '_EXPORT_TYPES'.
        nb_tries: int (optional default 2)
            number of times a request will be repeated if it fails.

        Returns
        -------
        rset: list of list of str
            a list that contains the requested entity parameters.
        """
        # Debug message
        if self.verbosity > 2:
            print("Executing rql: '%s'", rql)
            print("Exporting in: '%s'", export_type)

        # Check export type
        if export_type not in self._EXPORT_TYPES:
            raise Exception("Unknown export type '{0}', expect one in "
                            "'{1}'.".format(export_type, self._EXPORT_TYPES))

        # Create a dictionary with the request meta information
        data = {
            "__login": self.login,
            "__password": self.password,
            "rql": rql,
            "vid": export_type + "export",
            "_binary": 1
        }
        if export_type == "cw":
            del data["_binary"]
        
        try_count = 0
        while True:
            try:  # Get the result set, it will always try at least once
                try_count += 1
                response = requests.post(
                    self.url, data=data,verify=self.verify,
                    auth=(self.login, self.password))
                if not response.ok:
                    raise ValueError(response.reason)
                rset = self.importers[export_type](response.content)
                break
            except Exception as e:
                if try_count >= nb_tries:
                    # keep original message of e and add infos
                    e.message += ("\nFailed to get data after {} tries.\n"
                                  "Request: {}").format(nb_tries, data["rql"])
                    raise e
                time.sleep(1)  # wait 1 second before retrying

        # Debug message
        if self.verbosity > 2:
            print("RQL result: '%s'", rset)

        return rset

    def execute_with_sync(self, rql, sync_dir, timer=3, nb_tries=3):
        """ Method that loads the rset from a rql request through sftp protocol
        using the CWSearch mechanism.

        Parameters
        ----------
        rql: str (mandatory)
            the rql rquest that will be executed on the cw instance.
        sync_dir: str (mandatory)
            the destination folder where the rql data are synchronized.
        timer: int (optional default 3)
            the time in seconds we are waiting for the fuse or twisted
            server update.
        nb_tries: int (optional default 3)
            if the update has not been detected after 'nb_of_try' trials
            raise an exception.

        Returns
        -------
        rset: list of list or list of dict
            a list that contains the requested cubicweb database parameters
            when a json rset is generated, a list of dictionaries if a csv
            rset is generated.
        """
        # Create the CWSearch
        self._create_cwsearch(rql)

        # Wait for the update: use double quote in rql
        try_nb = 1
        cwsearch_title = None
        rql = rql.replace("'", '"')
        while try_nb <= nb_tries:

            # Timer
            if self.verbosity > 2:
                print("Sleeping: '%i sec'", timer)
            time.sleep(timer)

            # Get all the user CWSearch in the database
            rset = self.execute(
                "Any S, T, P Where S is CWSearch, S title T, S path P")

            # Check if the cubicweb update has been done.
            # If true, get the associated CWSearch title
            for item in rset:
                if item[2].replace("'", '"') == rql:
                    cwsearch_title = item[1]
                    break
            if cwsearch_title is not None:
                break

            # Increment
            try_nb += 1

        # If the search is not created
        if try_nb == (nb_tries + 1):
            raise IOError("The search has not been created properly.")

        # Get instance parameters
        cw_params = self.execute(rql="", export_type="cw")
        if self.verbosity > 2:
            print("Autodetected sync parameters: '%s'", str(cw_params))

        # Copy the data with the sftp fuse mount point
        self._get_server_dataset(sync_dir, cwsearch_title, cw_params)

        # Load the rset
        local_dir = os.path.join(sync_dir, cwsearch_title)
        rset_file = glob.glob(os.path.join(local_dir, "request_result.*"))
        if self.verbosity > 2:
            print("Autodetected json rset file at location '{0}'".format(
                rset_file))
        if len(rset_file) != 1:
            raise IOError("'{0}' rset file not supported, expect a single "
                          "rset file.".format(rset_json_file))
        rset_file = rset_file[0]
        filext = os.path.splitext(rset_file)[1]
        # > deal with json file
        if filext == ".json":
            with open(rset_file) as json_data:
                rset = json.load(json_data)

            # Tune the rset files in order to point in the local filesystem
            if not local_dir.endswith(os.path.sep):
                local_dir += os.path.sep
            if not cw_params["basedir"].endswith(os.path.sep):
                cw_params["basedir"] += os.path.sep
            for rset_items in rset:
                for item_index in range(len(rset_items)):
                    item = rset_items[item_index]
                    if (isinstance(item, basestring) and
                       item.startswith(cw_params["basedir"])):
                        rset_items[item_index] = item.replace(
                            cw_params["basedir"], local_dir, 1)

        # > deal with csv file
        elif filext == ".csv":
            with open(rset_file) as csv_data:
                data = csv.DictReader(csv_data, delimiter=";", quotechar="|")
                rset = [item for item in data]

        # > raise an error when the file extension is not supported
        else:
            raise IOError("Unknown '{0}' rset extension.".format(rset_file))

        # Debug message
        if self.verbosity > 2:
            print("RQL result: '%s'", rset)

        return rset

    def get_genotype_measure(self, gene_name, genomic_measure, nb_tries=3):
        """ Method that loads the genomic measures stored in PLINK format.

        Parameters
        ----------
        gene_name: str (mandatory)
            a gene name used to limit the number of measures that will be
            loaded.
        genomic_measure: str (mandatory)
            the genomic measure name associated to PLINK files.
        nb_tries: int (optional default 3)
            if the update has not been detected after 'nb_of_try' trials
            raise an exception.

        Returns
        -------
        rset: dict
            dictionary with 'labels' and 'records' (that contains
            the requested cubicweb database parameters).
        """
        # Debug message
        if self.verbosity > 2:
            print("Genotype extraction: '{0}', '{1}'".format(
                genomic_measure, gene_name))

        # Create a dictionary with the request meta information
        data = {
            "__login": self.login,
            "__password": self.password,
            "vid": "metagen-search-json",
            "measure": genomic_measure,
            "gene": gene_name,
            "export": "data"
        }
        
        try_count = 0
        while True:
            try:  # Get the result set, it will always try at least once
                try_count += 1
                response = requests.post(
                    self.url, data=data, verify=self.verify,
                    auth=(self.login, self.password))
                if not response.ok:
                    raise ValueError(response.reason)
                rset = self.importers["json"](response.content)
                break
            except Exception as e:
                if try_count >= nb_tries:
                    # keep original message of e and add infos
                    e.message += ("\nFailed to get data after {} tries.\n"
                                  "Request: {}").format(nb_tries, data["rql"])
                    raise e
                time.sleep(1)  # wait 1 second before retrying

        # Debug message
        if self.verbosity > 2:
            print("Genotype result: '%s'", rset)

        return rset

    ###########################################################################
    # Private Members
    ###########################################################################

    def _get_server_dataset(self, sync_dir, cwsearch_title, cw_params):
        """ Download the CWSearch result trough a sftp connection.

        .. note::

            If a folder 'sync_dir' + 'cwsearch_title' is detected on the local
            machine, no download is run. We assume that the CWSearch has already
            been downloaded properly.

        Parameters
        ----------
        sync_dir: str (mandatory)
            the destination folder where the rql data are synchronized.
        cwsearch_title: str (mandatory)
            the title of the CWSearch that will be downloaded.
        cw_params: dict (mandatory)
            a dictionary containing cw/fuse parameters.
        """
        # Build the mount point
        mount_point = os.path.join(
            self.server_root, cw_params["instance_name"])

        # Get the virtual folder to sync
        virtual_dir_to_sync = os.path.join(mount_point, cwsearch_title)
        if self.verbosity > 2:
            print("Autodetected sync directory: '%s'", virtual_dir_to_sync)

        # Get the local folder
        local_dir = os.path.join(sync_dir, cwsearch_title)
        if os.path.isdir(local_dir):
            print("The CWSearch '{0}' has been found at location "
                  "'{1}'. Do not download the data again.".format(
                    cwsearch_title, local_dir))

        # Rsync via paramiko and sftp
        else:
            transport = paramiko.Transport((self.host, self.port))
            transport.connect(username=self.login, password=self.password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            if self.verbosity > 2:
                print("Downloading: '%s' to '%s'", virtual_dir_to_sync,
                             local_dir)
            self._sftp_get_recursive(virtual_dir_to_sync, local_dir, sftp)
            if self.verbosity > 2:
                print("Downloading done")

            sftp.close()
            transport.close()

    def _sftp_get_recursive(self, path, dest, sftp):
        """ Recursive download of the data through a sftp connection.

        Parameters
        ----------
        path: str (mandatory)
            the sftp path to download.
        dest: str (mandatory)
            the destination folder on the local machine.
        sftp: paramiko sftp connection (mandatory)
        """
        # Go through the current sftp folder content
        dir_items = sftp.listdir(path)
        os.makedirs(dest)
        for item in dir_items:

            # Construct the item absolute path
            item_path = os.path.join(path, item)
            dest_path = os.path.join(dest, item)

            # If a directory is found
            if self._sftp_isdir(item_path, sftp):
                self._sftp_get_recursive(item_path, dest_path, sftp)

            # Otherwise transfer the data
            else:
                sftp.get(item_path, dest_path)

    def _sftp_isdir(self, path, sftp):
        """ Check if a distant path is a directory through a sftp connection.

        Parameters
        ----------
        path: str (mandatory)
            the sftp path to download.
        sftp: paramiko sftp connection (mandatory)
        """
        try:
            return stat.S_ISDIR(sftp.stat(path).st_mode)
        #Path does not exist, so by definition not a directory
        except IOError:
            return False

    def _create_cwsearch(self, rql, export_type="cwsearch"):
        """ Method that creates a CWSearch entity from a rql.

        .. note::

            The CWSearch title has to be unique, build automatically title
            of the form 'auto_generated_title_x' where x is incremented
            each time an element is inserted in the data base.

        Parameters
        ----------
        rql: str (mandatory)
            the rql rquest that will be executed on the cw instance.
        """
        # Debug message
        if self.verbosity > 2:
            print("Executing rql: '%s'", rql)
            print("Exporting in: '%s'", export_type)

        # Create a dictionary with the request meta information
        data = {
            "__login": self.login,
            "__password": self.password,
            "path": rql,
            "vid": export_type + "export"
        }

        # Get the result set
        response = requests.post(self.url, data=data, verify=self.verify,
                                 auth=(self.login, self.password))
        if not response.ok:
            raise ValueError(response.reason)
        status = self.importers[export_type](response.content)
        if status["exitcode"] != 0:
            raise ValueError("Can't create 'CWSearch' from RQL '{0}': "
                             "{1}.".format(rql, status["stderr"]))
