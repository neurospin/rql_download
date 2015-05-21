#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Cubicweb import
from cubicweb import Binary


class Search(object):
    """ A class that emulate a CWSearch entity.
    """

    def __init__(self):
        """ Create two virtual searches.
        """
        self.instance = "test"
        self.searchs = {
            "search1": [
                "/tmp/study/subdir1/fichier1",
                "/tmp/study/subdir2/fichier2",
                "/tmp/study/subdir2/fichier3",
                "/tmp/study/subdir1/fichier4"
            ],
            "search2": [
                "/tmp/study/subdir1/fichier1",
                "/tmp/study/subdir2/fichier2",
            ],
        }

    def get_files(self, virtpath, session_index):
        return map(lambda x: (x, False),
                   self.searchs.get(virtpath.search_name))

    def get_searches(self):
        return [[
            (u"search1",),
            (u"search2",)
        ]]

    def get_file_data(self, file_eid, rset_file, session_index,
                      search_name=None):
        return Binary("nothing in %s" % file_eid)
