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
from yams.buildobjs import EntityType
from yams.buildobjs import SubjectRelation
from yams.buildobjs import String
from yams.buildobjs import Date
from yams.buildobjs import Bytes
from yams.buildobjs import RichString


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
        a json file with all the server resources associated with the
        current search - {"rql": rql, "files": [], "nonexistent-files": []}
    rset: SubjectRelation (mandatory)
        the result set associated with the current search.
    rset_type: String (optional, default 'jsonexport')
        the type of the rset.
    """
    __permissions__ = {
        "read": ("managers", ERQLExpression("X owned_by U"),),
        "add": ("managers", "users"),
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


class File(EntityType):
    """ A downloadable file which may contains binary data.
    """
    __permissions__ = {
        "read": ("managers", ERQLExpression("X owned_by U"),),
        "add": ("managers", "users"),
        "delete": ("managers", "owners"),
        "update": ("managers", "owners"),
    }
    title = String(fulltextindexed=True, maxsize=256)
    data = Bytes(
        required=True, fulltextindexed=True, description=_("file to upload"))
    data_format = String(
        required=True, maxsize=128,
        description=_("MIME type of the file. Should be dynamically set at "
                      "upload time."))
    data_encoding = String(
        maxsize=32,
        description=_("encoding of the file when it applies (e.g. text). "
                      "Should be dynamically set at upload time."))
    data_name = String(
        required=True, fulltextindexed=True,
        description=_("name of the file. Should be dynamically set at upload "
                      "time."))
    data_sha1hex = String(
        maxsize=40,
        description=_("SHA1 sum of the file. May be set at upload time."))
    description = RichString(
        fulltextindexed=True, internationalizable=True,
        default_format="text/rest")
