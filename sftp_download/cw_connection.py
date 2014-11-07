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
import sys
import urllib2
import urllib
import json
import csv
import traceback
import logging

# Define logger
logger = logging.getLogger(__name__)


def load_csv(csv_stream, delimiter=";"):
    """ Load a csv file.

    Parameters
    ----------
    csv_stream: open file (mandatory)
        the file stream we want to load.

    Returns
    -------
    csv_lines: list
        a list containing all the csv lines.
    """
    reader = csv.reader(csv_stream, delimiter=delimiter)
    csv_lines = [line for line in reader]

    return csv_lines


class CWInstanceConnection(object):
    """ Tool to dump the data stored in a cw instance.

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
    _EXPORT_TYPES = ["json", "csv"]
    importers = {
        "json": json.load,
        "csv": load_csv
    }

    def __init__(self, url, login, password, realm=None):
        """ Initilize the HTTPConnection class.

        Parameters
        ----------
        url: str (mandatory)
            the url to the cw instance.
        login: str (mandatory)
            the cw login.
        password: str (mandatory)
            the cw user password.
        realm: str (optional default None)
            authentification domain (see firefox -> Outils -> Developpement web
            -> Reseau -> Get)
        """
        # Class parameters
        self.url = url
        self.login = login
        self.realm = realm
        self._connect(password)

        print self.opener

    ###########################################################################
    # Public Members
    ###########################################################################

    def execute(self, rql, export_type="json"):
        """ Method that loads the rset from a rql request.

        Parameters
        ----------
        rql: str (mandatory)
            the rql rquest that will be executed on the cw instance.
        export_type: str (optional default 'json')
            the result set export format: one defined in '_EXPORT_TYPES'.

        Returns
        -------
        rset: list of list of str
            a list that contains the requested entity parameters.        
        """
        # Debug message
        logger.debug("Executing rql: '%s'", rql)
        logger.debug("Exporting in: '%s'", export_type)

        # Check export type
        if export_type not in self._EXPORT_TYPES:
            raise Exception("Unknown export type '{0}', expect one in "
                            "'{1}'.".format(export_type, self._EXPORT_TYPES))

        # Create a dictionary with the request meta information
        data = {
            "rql": rql,
            "vid": export_type + "export",
        }

        # Get the result set
        rset = self.importers[export_type](
            self.opener.open(self.url, urllib.urlencode(data)))

        # Debug message
        logger.debug("RQL result: '%s'", rset)

        return rset    

    ###########################################################################
    # Private Members
    ###########################################################################

    def _create_cwsearch(rql):
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
        # Create a dictionary with the request meta information
        data = {
            "path": rql,
            "title": auto_generated_title,
            "vid": export_type + "export"
        }

    def _connect(self, password):
        """ Method to create an object that handle opening of HTTP URLs.

        .. notes::

            If the Python installation has SSL support
            (i.e., if the ssl module can be imported),
            HTTPSHandler will also be added?

        Parameters
        ----------
        password: str (mandatory)
            the cw user password.       
        """
        # Create the handlers and the associated opener
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        if self.realm is not None:
            auth_handler = urllib2.HTTPBasicAuthHandler()
            auth_handler.add_password(realm=self.realm,
                                      uri=url,
                                      user=self.login,
                                      passwd=password)
            self.opener.add_handler(auth_handler)

        # Connect to the cw instance
        data = {
            "__login": self.login,
            "__password": password,
        }
        self.opener.open(self.url, urllib.urlencode(data))


if __name__ == "__main__":

    # Set logging level
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    # Create dummy rql
    rql = ("Any C, G Where X is Subject, X code_in_study C, "
           "X handedness 'ambidextrous', X gender G")

    # HTTP test
    url = "http://mart.intra.cea.fr/imagen"; login = "admin"; password = "alpine"
    connection = CWInstanceConnection(url, login, password)
    connection.execute(rql, export_type="csv")

    # HTTPS test
    #url = "https://imagen2.cea.fr/database/"; login = "grigis"; password = "password"
    #connection = CWInstanceConnection(url, login, password, realm="Imagen")
    #connection.execute(rql)
