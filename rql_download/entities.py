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
RQL_DOWNLOAD_FSET_ENTITIES = ["Scan", "ProcessingRun", "GenomicMeasure"]


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

    def rql(self, rql, parameter_name, identifier=1):
        """ Method that patch the rql.

        .. note::

            * reserved keys are 'PATH', 'FENTRIES', 'FILES' postfixed with the
              identifier number.
            * returned files are necessary at the beginning of the adapted rql.

        Parameters
        ----------
        rql: str (mandatory)
            the request to adapt.
        parameter_name: str (mandatory)
            the label of the entity to adapt.
        identifier: int (optional)
            postfix the reserved keys with this identifier.

        Returns
        -------
        global_rql: str
            the adapted rql.
        nb_files: int
            the number of files returned at the begining of the result set.        
        """
        # Define reserved labels
        reserved_labels = [
            "PATH{0}".format(identifier),
            "FILES{0}".format(identifier),
            "FENTRIES{0}".format(identifier)
        ]

        # Check that reserved keys are not used
        split_rql = re.split(r"[ ,]", rql)
        for resered_key in reserved_labels:
            if resered_key in split_rql:
                raise ValidationError(
                    "CWSearch", {
                        "rql": _(
                            'cannot edit the rql "{0}", "{1}" is a reserved key, '
                            'choose another name.'.format(rql, resered_key))})

        # Remove the begining of the rql in order to complete it
        formated_rql = " ".join(rql.split()[1:])

        # Complete the rql in order to access file pathes
        global_rql = (
            "Any {0}, {1}, {2} results_files {3}, {3} file_entries {4}, "
            "{4} filepath {0}".format(reserved_labels[0], formated_rql, 
                                      parameter_name, reserved_labels[1],
                                      reserved_labels[2]))

        return global_rql, 1


class IEntityAdapter(BaseIDownloadAdapter):
    """ Action to download entity attributes.

    Add items in the global list 'RQL_DOWNLOAD_EXPORT_ENTITIES' to activate
    such an action. The rset will be exported in csv format.
    """
    __select__ = BaseIDownloadAdapter.__select__ & is_instance(
        *RQL_DOWNLOAD_EXPORT_ENTITIES)
    __rset_type__ = "ecsvexport"

    def rql(self, rql, parameter_name, identifier=None):
        """ Method that simply return the input rql.
        """
        return rql, 1
