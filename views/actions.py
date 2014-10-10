#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import re
from cgi import parse_qs

# CW import
from cubicweb.web.action import Action
from cubicweb.predicates import (
    is_instance, multi_lines_rset)
from cubicweb import ValidationError

# Define global adaptor variables
RQL_DOWNLOAD_EXPORT_ENTITIES = ["Subject"]


###############################################################################
# Save CW search action
###############################################################################

class SaveCWSearchAction(Action):
    """ Action that generates a new CWSearch form.
    """
    __regid__ = "save-search"
    __select__ = Action.__select__ & multi_lines_rset()
    title = _("Save search")
    category = "save-search"

    def url(self, rql):
        """ Method that generates the url of CWSearch form.
        """
        path = self._cw.relative_path()
        param = ""
        if "?" in path:
            path, param = path.split("?", 1)
            # remove possible '_cwmsgid' parameter in url
            params_dict = parse_qs(param)
            if '_cwmsgid' in params_dict:
                del params_dict['_cwmsgid']
                param = self._cw.build_url_params(**params_dict)
        return self._cw.build_url(
            "add/CWSearch", request="{0}".format(rql), __redirectpath=path,
            __redirectparams=param)


###############################################################################
# Adaptors
###############################################################################

class FSetAdaptor(Action):
    """ Action to download entity objects related through an FileSet entity.
    """
    __regid__ = "rqldownload-adaptors"
    __select__ = Action.__select__ & is_instance("Scan", "ProcessingRun")

    def rql(self, rql, parameter_name):
        """ Method that patch the rql.

        note::
            The patched rql returned first elements are then the file pathes.
            Reserved keys are 'PATH', 'FENTRIES', 'FILES'.
        """
        # Check that reserved keys are not used
        split_rql = re.split(r"[ ,]", rql)
        for revered_key in ["PATH", "FENTRIES", "FILES"]:
            if revered_key in split_rql:
                raise ValidationError(
                    "CWSearch", {
                        "rql": _(
                            'cannot edit the rql "{0}", "{1}" is a reserved key, '
                            'choose another name'.format(rql, revered_key))})

        # Remove the begining of the rql in order to complete it
        formated_rql = " ".join(rql.split()[1:])

        # Complete the rql in order to access file pathes
        global_rql = ("Any PATH, {0}, {1} results_files FILES, FILES "
                      "file_entries FENTRIES, FENTRIES filepath "
                      "PATH".format(formated_rql, parameter_name))

        return global_rql


class EntityAdaptor(Action):
    """ Action to download entity attributes.
    """
    __regid__ = "rqldownload-adaptors"
    __select__ = Action.__select__ & is_instance(*RQL_DOWNLOAD_EXPORT_ENTITIES)

    def rql(self, rql, parameter_name):
        """ Method return the rql.
        """
        return rql


###############################################################################
# Registration callback
###############################################################################

def registration_callback(vreg):
    vreg.register(FSetAdaptor)
    vreg.register(EntityAdaptor)
    vreg.register(SaveCWSearchAction)
