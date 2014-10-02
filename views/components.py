#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

from cubicweb.predicates import nonempty_rset, anonymous_user
from cubicweb.web import component
from cubicweb.predicates import (
    is_instance, nonempty_rset, anonymous_user)


###############################################################################
# Save CW search box
###############################################################################

class SaveCWSearchBox(component.CtxComponent):
    """ Class that enables us to display a 'Save search' box when the selected
    entities fulfill the '__selected__' requirements.
    """
    __regid__ = "ctx-save-search-box"
    __select__ = (component.CtxComponent.__select__ & nonempty_rset() &
                  ~anonymous_user() & is_instance("Scan", "ProcessingRun"))
    context = "left"
    order = 0
    title = _("Tools")

    def render_body(self, w, **kwargs):
        """ Method that generates the html elements to display the 'Save search'
        box.

        ..note::
            This method only consider the first registered 'ns-save-search'
            action to generate the new CWSearch form.
        """
        # Get the first registered action that will give use the html page used
        # to fill the CWSearch
        possible_actions = self._cw.vreg["actions"].possible_actions(
            self._cw, self.cw_rset)
        link = possible_actions.get("save-search")

        # If a 'save-search' is declared
        if link:

            # Use the first action only
            link  = link[0]

            # Create the 'Save search' box
            url = link.url(self.cw_rset.printable_rql())
            w(u'<div class="btn-toolbar">')
            w(u'<div class="btn-group-vertical btn-block">')
            w(u'<a class="btn btn-primary"id="save-search-link" '
                'href="{0}">'.format(url))
            w(u'<span class="glyphicon glyphicon-save"> {0}</span>'.format(
                self._cw._(link.title)))
            w(u'</a></div></div>')

            # Add on load the rql facet change
            #self._cw.add_onload("$(cw).bind('facets-content-loaded', "
            #                    "cw.cubes.neurospinweb.changeSaveCWSearchUrl);")

