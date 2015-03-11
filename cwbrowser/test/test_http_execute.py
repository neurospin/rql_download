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


class TestHTTPExecuteTwisted(unittest.TestCase):
    """ Class to test http execute method with twisted server.
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
        # Check twisted server
        rset = self.connection.execute_with_sync(self.rql3, "/tmp/sync_twisted",
                                                 timer=1)
        for item in rset:
            self.assertTrue(os.path.isfile(item[0]))

        rset = self.connection.execute_with_sync(self.rql2, "/tmp/sync_twisted",
                                                 timer=1)

class TestHTTPExecuteFuse(unittest.TestCase):
    """ Class to test http execute method with fuse virtual folders and
    sftp.
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
        login = raw_input("\nEnter the login: ")
        password = getpass.getpass("Enter the password: ")

        # Create dummy rqls
        self.rql1 = ("Any S WHERE S is Subject")
        self.rql2 = ("Any S WHERE S is Scan, S has_data A, A field '3T', "
                     "S in_assessment B, B timepoint 'V0', B concerns D, "
                     "D code_in_study 'subject2'")

        # HTTP test
        self.connection = CWInstanceConnection(http_url, login, password,
                                               port=22)

    def test_execute_with_sync(self):
        """ Method to test if we can create/download a search from the script.
        """
        # Test Fuse virtual folders + sftp
        rset = self.connection.execute_with_sync(self.rql2, "/tmp/sync_fuse",
                                                 timer=1)
        for item in rset:
            self.assertTrue(os.path.isfile(item[0]))

        rset = self.connection.execute_with_sync(self.rql1, "/tmp/sync_fuse",
                                                 timer=1)             
            


def test_twisted():
    """ Function to execute unitest associated to twisted server.
    """
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHTTPExecuteTwisted)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


def test_fuse():
    """ Function to execute unitest associated to fuse virtual folders.
    """
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHTTPExecuteFuse)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test_twisted()
    test_fuse()
