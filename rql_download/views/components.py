##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from packaging import version

# Cubicweb import
import cubicweb
cw_version = version.parse(cubicweb.__version__)
if cw_version >= version.parse("3.21.0"):
    from cubicweb import _

from cubicweb import NotAnEntity
from cubicweb.web import component
from cubicweb.predicates import is_instance
from cubicweb.predicates import nonempty_rset
from cubicweb.predicates import anonymous_user
from cubicweb.predicates import non_final_entity
from cubicweb.predicates import nonempty_rset
from cubicweb.web.views.facets import facets
from cubicweb.web.views.facets import FilterBox
from cubicweb.web.views.facets import FacetFilterMixIn
from cubicweb.web.views.facets import contextview_selector
from logilab.mtconverter import xml_escape
from cubicweb.web.views.bookmark import BookmarksBox

# RQL download import
from cubes.rql_download.entities import RQL_DOWNLOAD_EXPORT_ENTITIES
from cubes.rql_download.entities import RQL_DOWNLOAD_FSET_ENTITIES
from cubes.rql_download.entities import RQL_DOWNLOAD_ENTITIES

# Define global search variables
RQL_DOWNLOAD_SEARCH_ENTITIES = (
    RQL_DOWNLOAD_EXPORT_ENTITIES + RQL_DOWNLOAD_FSET_ENTITIES +
    RQL_DOWNLOAD_ENTITIES)


###############################################################################
# Save CW search box
###############################################################################

class SaveCWSearchFilterBox(FacetFilterMixIn, component.CtxComponent):
    """ Class that enables us to display a 'Save search' box when the selected
    entities fulfill the '__select__' requirements.

    * This component shows up if the current rset is adaptable.
    * This component is integrated in the CW facet component
    * The global parameters 'RQL_DOWNLOAD_ENTITIES',
      'RQL_DOWNLOAD_EXPORT_ENTITIES' and 'RQL_DOWNLOAD_FSET_ENTITIES' specify
      which entities can be downloaded
      (ie. are adaptable).
    """
    __regid__ = "facet.filterbox"
    __select__ = (nonempty_rset() | contextview_selector())
    context = "left"
    order = 0
    visible = True
    title = _("Filter")

    linkbox_template = u'<div class="cw_search_box">{0}</div>'

    def render(self, w, **kwargs):
        """ Render the facet box only if something has to be displayed.
        """
        # Get the component context
        rset, vid, divid, paginate = self._get_context()

        # Check if some facets are defined for this view
        rql, available_facets = facets(self._cw, rset, self.__regid__)
        nb_facet_widgets = len(available_facets)
        if "eid" in rql:
            nb_facet_widgets = 0

        # Check if the view information can be downloaded
        can_save_search = False
        if rset.rowcount > 0:
            for rowindex in range(len(rset[0])):
                try:
                    entity = rset.get_entity(0, rowindex)
                    entity_name = entity.__class__.__name__
                    if entity_name in RQL_DOWNLOAD_SEARCH_ENTITIES:
                        can_save_search = True
                        break
                except NotAnEntity:
                    pass
                except:
                    raise

        # Can't download if not logged
        can_save_search = (can_save_search and
                           not self._cw.session.anonymous_session)

        # Display the facet if something has to be displayed
        if can_save_search or nb_facet_widgets > 0:
            self.can_save_search = can_save_search
            self.nb_facet_widgets = nb_facet_widgets
            self.layout_render(w, **kwargs)

    def render_body(self, w, **kwargs):
        """ Method that generates the html elements to display the 'Save search'
        box.

        .. note::

            This method only consider the first registered
            'rqldownload-adapters' action to generate the resources associated
            with the current search.

            If the 'eid' attribute is in the RQL do not show the facets.
        """
        # Get the component context
        rset, vid, divid, paginate = self._get_context()

        # Check we have a valid vid
        if vid is None:
            vid = self._cw.form.get("vid")

        # Create the form url
        if self.can_save_search:
            w(self.search_link(rset))
        if self.nb_facet_widgets > 0:
            self.generate_form(w, rset, divid, vid, paginate=paginate,
                               hiddens={}, **self.cw_extra_kwargs)

    def search_link(self, rset):
        """ Method that generates the url of the CWSearch form we want to save.
        """
        # Construct the form path
        # > get rql as url parameter
        path = u'rql={0}'.format(self._cw.url_quote(rset.printable_rql()))

        # > get the vid of the view
        if self._cw.form.get("vid"):
            path += u'&vid={0}'.format(self._cw.url_quote(self._cw.form["vid"]))

        # > say its a view
        path = u'view?' + path

        # Define the form default tile
        title = self._cw._("--unique title--")

        # Create the url to the CWSearch form
        cls = self._cw.vreg["etypes"].etype_class("CWSearch")
        add_url = cls.cw_create_url(self._cw, path=path, title=title)

        base_url = cls.cw_create_url(self._cw, title=title)
        link = (u'<a class="btn btn-primary" cubicweb:target="{0}" '
                 'id="facetBkLink" href="{1}">'.format(xml_escape(base_url),
                                                       xml_escape(add_url)))

        # Create the button
        button = u'<div class="btn-toolbar">'
        button += u'<div class="btn-group-vertical btn-block">'
        button += link
        button += u'<span class="glyphicon glyphicon-save" ' \
                  u'style="width: 25px;"></span>{0}'.format(
                      self._cw._("Add to cart"))
        button += u'</a></div></div><br />'

        return self.linkbox_template.format(button)

    def _get_context(self):
        """ Method to get the in context box information.
        """
        view = self.cw_extra_kwargs.get("view")
        context = getattr(view, "filter_box_context_info", lambda: None)()
        if context:
            rset, vid, divid, paginate = context
        else:
            rset = self.cw_rset
            vid, divid = None, "pageContent"
            paginate = view and view.paginable
        return rset, vid, divid, paginate


###############################################################################
# Help for download CW search box
###############################################################################

class HelpCWSearchBox(component.CtxComponent):
    """ Class that display a help box to download a cwsearch.

    A message is displayed when a new CWSearch is created. The global class
    parameter '_message' can be tuned to display a custom help message.
    """
    __regid__ = "help-cw-search"
    __select__ = is_instance("CWSearch")
    context = "navcontentbottom"
    order = 0
    title = _("Download Search Help")
    _message = (u"This is the content of your cart. You can download each "
                u"subset using your favorite SFTP client (e.g. FileZilla)")

    def render_body(self, w):
        """ Display the help message in the web page.
        """
        w(u'<div class="help-cw-search">')
        w(self._message)
        w(u'</div>')


###############################################################################
# Registration callback
###############################################################################

def registration_callback(vreg):
    vreg.unregister(FilterBox)
    vreg.unregister(BookmarksBox)
    vreg.register(SaveCWSearchFilterBox)
    vreg.register(HelpCWSearchBox)
