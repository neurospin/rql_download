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

# Cubicweb import
from cubicweb.web.action import Action
from cubicweb.predicates import is_instance
from cubicweb import ValidationError

# Define global adaptor variables
RQL_DOWNLOAD_EXPORT_ENTITIES = ["Subject"]
RQL_DOWNLOAD_FSET_ENTITIES = ["Scan", "ProcessingRun"]


class BaseIDownloadAdapter(Action):
    """ Base adapter class.

    .. note::

        * A 'rql' method has to be implemented in child classes.
        * We assume the database intergrity (ie. all file pathes inserted in
          the db exist on the file system) and thus do not check in the hooks
          to speed speed the search creation.        
    """
    __regid__ = "rqldownload-adapters"
    __abstract__ = True
    __rset_type__ = "jsonexport"

    def rql(self):
        """ Method that return the completed RQL.
        """
        raise NotImplementedError


class IFSetAdapter(Action):
    """ Action to download entity objects related through a FileSet entity.

    Add items in the global list 'RQL_DOWNLOAD_FSET_ENTITIES' to activate
    such an action. The rset will be exported in json format.

    .. warning::

        * The adapted RQL must return the file pathes in the first item
          of the rset.
    """
    __regid__ = "rqldownload-adapters"
    __select__ = Action.__select__ & is_instance(*RQL_DOWNLOAD_FSET_ENTITIES)
    __rset_type__ = "jsonexport"

    def rql(self, rql, parameter_name):
        """ Method that patch the rql.

        .. note::

            * The patched rql returned first elements are then the file pathes.
            * Reserved keys are 'PATH', 'FENTRIES', 'FILES'.
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


class IEntityAdapter(BaseIDownloadAdapter):
    """ Action to download entity attributes.

    Add items in the global list 'RQL_DOWNLOAD_EXPORT_ENTITIES' to activate
    such an action. The rset will be exported in csv format.
    """
    __select__ = BaseIDownloadAdapter.__select__ & is_instance(
        *RQL_DOWNLOAD_EXPORT_ENTITIES)
    __rset_type__ = "ecsvexport"

    def rql(self, rql, parameter_name):
        """ Method that simply return the input rql.
        """
        return rql
