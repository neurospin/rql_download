# -*- coding: utf-8 -*-

"""Test path manipulations """

import unittest2
import os.path as osp
from collections import namedtuple

from cubes.rsetftp.ftpserver.server import VirtualPathTranslator, VirtualPath

from testlib import Search


FakeStat = namedtuple('FakeStat', ('st_mode', 'st_ino', 'st_dev', 'st_nlink',
                                   'st_uid', 'st_gid', 'st_size', 'st_atime',
                                   'st_mtime', 'st_ctime'))


class PathTC(unittest2.TestCase):

    def setUp(self):
        s = Search()
        self.path_translator = VirtualPathTranslator(s)

    def assertVirtualPath(self, res, expected):
        self.assertEqual(res.search_name,
                         expected[0])
        self.assertEqual(res.search_relpath,
                         expected[1])

    def test_dir_content(self):
        t = self.path_translator
        expected = [
            ('/tmp/brainomics/subdir1/fichier1', False),
            ('/tmp/brainomics/subdir1/fichier4', False),
        ]
        test = VirtualPath('search1', '/tmp/brainomics/subdir1', '/')
        self.assertEqual(list(t.dir_content(test)), expected)

    def test_split_virtual_path(self):
        t = self.path_translator
        expected = ('search1', 'subdir1/fichier1')
        self.assertVirtualPath(t.split_virtual_path('/search1/subdir1/fichier1'),
                               expected)
        expected = ('search1', '')
        self.assertVirtualPath(t.split_virtual_path('/search1/'),
                               expected)
        self.assertVirtualPath(t.split_virtual_path('/search1'), expected)

    def test_filter_files(self):
        t = self.path_translator
        t.BASE_REAL_DIR = '/'
        expected = [
            ('/subdir1/fichier1', False),
            ('/subdir1/fichier4', False),
            ('/subdir1/subsubdir1', False),
        ]
        files = [
            ("/subdir1/fichier1", False),
            ("/subdir2/fichier2", False),
            ("/subdir2/fichier3", False),
            ("/subdir1/fichier4", False),
            ("/subdir1/subsubdir1/fichier1", False),
            ("/subdir1/subsubdir1/", False),
        ]
        self.assertEqual(list(t.filter_files(files, '/subdir1')), expected)

    def test_list_root(self):
        t = self.path_translator
        expected = ['search1', 'search2']
        result = [r[0] for r in t.list_directory('/')]
        self.assertEqual(result, expected)

    def test_list_directory(self):
        import os
        stat_f = lambda x: FakeStat(33188, 16398844, 65024L, 1, 1049, 1049, 0,
                                    1409046988, 1409046988, 1409046988)
        os.stat = stat_f
        os.lstat = stat_f
        t = self.path_translator
        expected = ['subdir1', 'subdir2']
        result = [r[0] for r in t.list_directory('/search1/tmp/brainomics')]
        self.assertEqual(result, expected)

    def test_get_attrs(self):
        t = self.path_translator
        self.assertEqual(t.get_attrs('/')['permissions'], t.dir_perm)
        self.assertEqual(t.get_attrs('/search1')['permissions'], t.dir_perm)
        self.assertEqual(t.get_attrs('/search1/')['permissions'], t.dir_perm)

    def test_stat(self):
        t = self.path_translator
        self.assertRaisesRegexp(OSError, 'No such file or directory: "/toto"',
                                t.stat, '/toto')
        self.assertEqual(t.stat('/').st_mode, t.dir_perm)
        self.assertEqual(t.stat('/search1').st_mode, t.dir_perm)

    def test_open_file_entity(self):
        t = self.path_translator
        virtpath = t.split_virtual_path('/search1/rien_12345')
        self.assertTrue(t.is_file_entity(virtpath))
        ftp_file = t.open_cw_file(virtpath)
        expected_file_content = 'nothing in 12345'
        self.assertEqual(expected_file_content,
                         ftp_file.readChunk(0, -1))
        self.assertEqual({
                            'size': len(expected_file_content),
                            'uid': 0,
                            'gid': 0,
                            'mtime': 0,
                            'atime': 0,
                            'permissions': t.file_perm
                         }, ftp_file.getAttrs())
        self.assertTrue(hasattr(ftp_file, 'close'))
        ftp_file.close()

    def test_base_dir(self):
        t = self.path_translator
        t.BASE_REAL_DIR = '/tmp/brainomics'
        import os
        stat_f = lambda x: FakeStat(33188, 16398844, 65024L, 1, 1049, 1049, 0,
                                    1409046988, 1409046988, 1409046988)
        os.stat = stat_f
        os.lstat = stat_f
        expected = ['subdir1', 'subdir2']
        result = [r[0] for r in t.list_directory('/search1')]
        self.assertEqual(result, expected)


if __name__ == '__main__':
    from logilab.common.testlib import unittest_main
    unittest_main()
