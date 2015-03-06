#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

""" Test path manipulations """

# System import
from __future__ import with_statement
import unittest
from collections import namedtuple

# Cubicweb import
from cubes.rql_download.twistedftpserver.server import VirtualPathTranslator
from cubes.rql_download.twistedftpserver.server import VirtualPath

# Rql Download import
from testlib import Search


FakeStat = namedtuple("FakeStat", ("st_mode", "st_ino", "st_dev", "st_nlink",
                                   "st_uid", "st_gid", "st_size", "st_atime",
                                   "st_mtime", "st_ctime"))


class TestTwistedSFTPServer(unittest.TestCase):
    """ Test the twisted sfp server used to expose user searches.
    """

    def setUp(self):
        """ A user search is simulated and virtual path are translated to
        real one.
        """
        self.search = Search()
        self.path_translator = VirtualPathTranslator(self.search)
        self.path_translator.BASE_REAL_DIR = "/"
        self.path_translator.INSTANCE_NAMES = [self.search.instance]
        self.path_translator.all_cw_search_names = [
            r[0] for r in self.search.get_searches()[0]]

    def assertVirtualPath(self, res, expected):
        self.assertEqual(res.search_name, expected[0])
        self.assertEqual(res.search_relpath, expected[1])

    def test_dir_content(self):
        """ Test to list and filter a search result. """
        expected = [
            ("/tmp/study/subdir1/fichier1", False),
            ("/tmp/study/subdir1/fichier4", False),
        ]
        test = VirtualPath("search1", "/tmp/study/subdir1", "/", "test")
        self.assertEqual(list(self.path_translator.dir_content(test, 0)),
                         expected)

    def test_split_virtual_path(self):
        """ Test the extraction of a search name from a virtual path.
        """
        expected = ("search1", "subdir1/fichier1")
        self.assertVirtualPath(
            self.path_translator.split_virtual_path(
                "/test/search1/subdir1/fichier1"),
            expected)
        expected = ("search1", "")
        self.assertVirtualPath(
            self.path_translator.split_virtual_path("/test/search1/"),
            expected)

    def test_filter_files(self):
        """ Test the extraction of files which are located in a specific dir.
        """
        expected = [
            ("/subdir1/fichier1", False),
            ("/subdir1/fichier4", False),
            ("/subdir1/subsubdir1", False),
        ]
        files = [
            ("/subdir1/fichier1", False),
            ("/subdir2/fichier2", False),
            ("/subdir2/fichier3", False),
            ("/subdir1/fichier4", False),
            ("/subdir1/subsubdir1/fichier1", False),
            ("/subdir1/subsubdir1/", False),
        ]
        self.assertEqual(
            list(self.path_translator.filter_files(files, "/subdir1")),
            expected)

    def test_list_root(self):
        """ Test that the root search of an instance is built properly.
        """
        expected = ["search1", "search2"]
        result = [r[0] for r in self.path_translator.list_directory(
            "/{0}".format(self.search.instance))]
        self.assertEqual(result, expected)

    def test_list_directory(self):
        """ List the content of a directory.
        """
        import os
        stat_f = lambda x: FakeStat(33188, 16398844, 65024L, 1, 1049, 1049, 0,
                                    1409046988, 1409046988, 1409046988)
        os.stat = stat_f
        os.lstat = stat_f
        expected = ["subdir1", "subdir2"]
        result = [r[0] for r in self.path_translator.list_directory(
            "/{0}/search1/tmp/study".format(self.search.instance))]
        self.assertEqual(result, expected)

    def test_get_attrs(self):
        """ Test the get attributes method.
        """
        self.assertEqual(
            self.path_translator.get_attrs("/")["permissions"],
            self.path_translator.dir_perm)
        self.assertEqual(
            self.path_translator.get_attrs(
                "/{0}".format(self.search.instance))["permissions"],
            self.path_translator.dir_perm)
        self.assertEqual(
            self.path_translator.get_attrs(
                "/{0}/search1/".format(self.search.instance))["permissions"],
            self.path_translator.dir_perm)

    def test_stat(self):
        """ Test the stat method.
        """
        self.assertRaisesRegexp(
            OSError, "No such file or directory: \"/toto\"",
            self.path_translator.stat, "/toto")
        self.assertEqual(self.path_translator.stat("/").st_mode,
                         self.path_translator.dir_perm)
        self.assertEqual(
            self.path_translator.stat(
                "/{0}".format(self.search.instance)).st_mode,
            self.path_translator.dir_perm)

    def test_open_file_entity(self):
        """ Try to access a file.
        """
        virtpath = self.path_translator.split_virtual_path(
            "/test/search1/rien_12345")
        self.assertTrue(self.path_translator.is_file_entity(virtpath))
        ftp_file = self.path_translator.open_cw_file(virtpath)
        expected_file_content = "nothing in 12345"
        self.assertEqual(expected_file_content,
                         ftp_file.readChunk(0, -1))
        self.assertEqual({
            "size": len(expected_file_content),
            "uid": 0,
            "gid": 0,
            "mtime": 0,
            "atime": 0,
            "permissions": self.path_translator.file_perm},
            ftp_file.getAttrs())
        self.assertTrue(hasattr(ftp_file, "close"))
        ftp_file.close()

    def test_base_dir(self):
        """ Test to mask a part of the exposed path.
        """
        old_base_dir = self.path_translator.BASE_REAL_DIR
        self.path_translator.BASE_REAL_DIR = "/tmp/study"
        import os
        stat_f = lambda x: FakeStat(33188, 16398844, 65024L, 1, 1049, 1049, 0,
                                    1409046988, 1409046988, 1409046988)
        os.stat = stat_f
        os.lstat = stat_f
        expected = ["subdir1", "subdir2"]
        result = [r[0] for r in self.path_translator.list_directory(
            "/{0}/search1".format(self.search.instance))]
        self.assertEqual(result, expected)
        self.path_translator.BASE_REAL_DIR = old_base_dir


def test():
    """ Function to execute unitest
    """
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTwistedSFTPServer)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    print("RETURNCODE: ", test())
