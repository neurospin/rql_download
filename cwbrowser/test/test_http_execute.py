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


class TestHTTPEXECUTE(unittest.TestCase):
    """ Class to test http/https execute method.
    """
    def setUp(self):
        """ Define some rql and create a connection.
        """
        # Set logging level
        logging.basicConfig(level=logging.DEBUG)

        # Ask for url & login information
        http_url = raw_input(
            "\nEnter the http url [default: http://localhost:8080/]: ")
        if not http_url:
            http_url = "http://localhost:8080/"
        login = raw_input("\nEnter the login [default: admin]: ")
        if not login:
            login = "admin"
        password = getpass.getpass("Enter the password [default: a]: ")
        if not password:
            password = "a"

        # Create dummy rqls
        self.rql1 = ("Any C, G Where X is Subject, X code_in_study C, "
                     "X handedness 'ambidextrous', X gender G")
        self.rql2 = ("Any S WHERE S is Subject")
        self.rql3 = ("Any S WHERE S is Scan, S has_data A, A field '3T', "
                     "S in_assessment B, B timepoint 'V0', B concerns D, "
                     "D code_in_study 'subject1'")

        # HTTP test
        self.connection = CWInstanceConnection(http_url, login, password,
                                               port=9191)


    def test_execute(self):
        """ Method to test if we can interogate the server from the script.
        """
        rset = self.connection.execute(self.rql1, export_type="json")
        self.assertTrue(len(rset) > 0)

    def test_execute_with_sync(self):
        """ Method to test if we can create/download a search from the script.
        """
        rset = self.connection.execute_with_sync(self.rql3, "/tmp/sync",
                                                 timer=1)
        for item in rset:
            self.assertTrue(os.path.isfile(item[0]))

        rset = self.connection.execute_with_sync(self.rql2, "/tmp/sync",
                                                 timer=1)        


def test():
    """ Function to execute unitest.
    """
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHTTPEXECUTE)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
