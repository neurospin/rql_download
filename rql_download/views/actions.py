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
# Adaptors
###############################################################################

class FSetAdaptor(Action):
    """ Action to download entity objects related through a FileSet entity.
    """
    __regid__ = "rqldownload-adaptors"
    __select__ = Action.__select__ & is_instance("Scan", "ProcessingRun")
    __rset_type__ = "jsonexport"

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

    Add items in the global list 'RQL_DOWNLOAD_EXPORT_ENTITIES' to activate
    such actions.
    """
    __regid__ = "rqldownload-adaptors"
    __select__ = Action.__select__ & is_instance(*RQL_DOWNLOAD_EXPORT_ENTITIES)
    __rset_type__ = "ecsvexport"

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
