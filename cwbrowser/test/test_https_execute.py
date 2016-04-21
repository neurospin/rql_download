#! /usr/bin/env python
##########################################################################
# CWBROWSER - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import os
import getpass
import logging
import unittest

# Cwbrowser import
from cwbrowser.cw_connection import CWInstanceConnection


class TestHTTPSExecute(unittest.TestCase):
    """ Class to test https execute method.
    """
    def setUp(self):
        """ Define some rql and create a connection.
        """
        # Set logging level
        logging.basicConfig(level=logging.DEBUG)

        # Ask for url & login information
        https_url = raw_input(
            "\nEnter the http url [default: https://imagen2.cea.fr/database/]: ")
        if not https_url:
            https_url = "https://imagen2.cea.fr/database/"
        login = raw_input("\nEnter the login: ")
        password = getpass.getpass("Enter the password: ")

        # Create dummy rqls
        self.rql = ("Any C, G Where X is Subject, X code_in_study C, "
                     "X handedness 'ambidextrous', X gender G")

        # HTTP test
        self.connection = CWInstanceConnection(https_url, login, password,
                                               realm="Imagen")

    def test_execute(self):
        """ Method to test if we can interogate the server from the script.
        """
        rset = self.connection.execute(self.rql, export_type="json")
        self.assertTrue(len(rset) > 0)


def test():
    """ Function to execute unitest.
    """
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHTTPSExecute)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
