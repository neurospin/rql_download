#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Cubicweb import
from cubicweb.schema import ERQLExpression, RQLUniqueConstraint
from yams.buildobjs import EntityType, SubjectRelation, String, Date


class CWSearch(EntityType):
    """ An entity used to save a search which may contains resources on the 
    server file system.

    Attributes
    ----------
    title: String (mandatory)
        a short description of the file.
    path: String (mandatory)
        the rql request that will be saved.
    expiration_data: Date (mandatory)
        the expiration date of the current search.
    result: SubjectRelation (mandatory)
        a json file with all the server resources associated with the current search - {"rql": rql, "files": [], "nonexistent-files": []}
    rset: SubjectRelation (mandatory)
        the result set associated with the current search.
    rset_type: String (optional, default 'jsonexport')
        the type of the rset.
    """
    __permissions__ = {
        "read":   ("managers", ERQLExpression("X owned_by U"),),
        "add":    ("managers", "users"),
        "delete": ("managers", "owners"),
        "update": ("managers", "owners"),
    }
    title = String(maxsize=256, required=True,
                  constraints=[
                      RQLUniqueConstraint(
                          "X title N, S title N, X owned_by U, X is CWSearch",
                          mainvars="X",
                          msg=_("this name is already used"))
                  ],
                   description=_("Please set a unique subset name."))
    path = String(required=True,
                  description=_("the rql request we will save (do not edit "
                                "this field)."))
    expiration_date = Date(required=True, indexed=True)
    # json which contains resultset and filepath
    result = SubjectRelation("File", cardinality="1*", inlined=True,
                             composite="subject")
    rset = SubjectRelation("File", cardinality="1*", inlined=True,
                           composite="subject")
    # view regid to show rset
    rset_type = String(required=True, default="jsonexport", maxsize=50)
