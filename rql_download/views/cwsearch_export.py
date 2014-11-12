#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# CW import
from cubicweb.view import View


###############################################################################
# CW Search export
###############################################################################

class CWSearchRsetView(View):
    """ Create a new CWSearch entity.
    """
    __regid__ = "cwsearchexport"
    title = _("cwsearch-export-view")

    def call(self):
        """ Create the entity if necessary.

        Check if the request has already been registered and create a unique
        title.
        """
        # Get the CWSearch entity parameters from the url 'path'
        params_dict = self._cw.form
        if "path" not in params_dict or "title" not in params_dict:
            raise ValueError("A CWSearch entity is composed of a 'path' "
                             "and a 'title' attributes.")

        # Get all the user CWSearch in the database
        rset = self._cw.session.execute(
            "Any S, T, P Where S is CWSearch, S title T, S path P")
        
        # Unpack the rset: use double quote in rql
        titles = []
        rqls = []
        eids = []
        for eid, title, rql in rset:
            titles.append(title)
            rqls.append(rql.replace("'", '"'))
            eids.append(eid)

        # Check if the rql has already been processed
        # If not, create a new CWSearch
        rql = unicode(params_dict["path"].replace("'", '"'))
        if rql not in rqls:
            
            # Create a unique name of the form 'auto_generated_title_x' where
            # x is incremented
            auto_gen_increments = [x.split("_")[-1] for x in titles
                                   if x.startswith("auto_generated_title_")]
            prefix = 1
            while True:
                if str(prefix) in auto_gen_increments:
                    prefix += 1
                else:
                    break
            unique_title = u"auto_generated_title_{0}".format(prefix)

            # Create the new CWSearch
            self._cw.session.create_entity("CWSearch",
                                           title=unique_title,
                                           path=rql)
            self._cw.session.commit()

