# -*- coding: utf-8 -*-

from cubicweb import Binary


class Search(object):

    def __init__(self):
        self.searchs = {
            'search1': [
                "/tmp/brainomics/subdir1/fichier1",
                "/tmp/brainomics/subdir2/fichier2",
                "/tmp/brainomics/subdir2/fichier3",
                "/tmp/brainomics/subdir1/fichier4"
            ],
            'search2': [
                "/tmp/brainomics/subdir1/fichier1",
                "/tmp/brainomics/subdir2/fichier2",
                "/tmp/brainomics/subdir2/fichier3",
                "/tmp/brainomics/subdir1/fichier4"
            ],
        }

    def get_files(self, virtpath):
        return map(lambda x: (x, False), self.searchs.get(virtpath.search_name))

    def get_searches(self):
        return [
            (u'search1',),
            (u'search2',)
        ]

    def get_file_data(self, file_eid, rset_file, search_name=None):
        return Binary('nothing in %s' % file_eid)



