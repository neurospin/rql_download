#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# cwbrowser current version
_version_major = 0
_version_minor = 0
_version_micro = 1


# Expected by setup.py: string of form "X.Y.Z"
__version__ = "{0}.{1}.{2}".format(
    _version_major, _version_minor, _version_micro)

# Expected by setup.py: the status of the project
CLASSIFIERS = ["Development Status :: 1 - Planning",
               "Environment :: Console",
               "Operating System :: OS Independent",
               "Programming Language :: Python",
               "Topic :: Scientific/Engineering",
               "Topic :: Utilities"]

# Project descriptions
description = "CWBROWSER"
long_description = """
=========
CWBROWSER 
=========

Summary
-------
Methods to access information in a CubicWeb database.
"""

# Main setup parameters
NAME = "cwbrowser"
ORGANISATION = "CEA"
MAINTAINER = "Antoine Grigis"
MAINTAINER_EMAIL = "antoine.grigis@cea.fr"
DESCRIPTION = description
LONG_DESCRIPTION = long_description
URL = ""
DOWNLOAD_URL = ""
LICENSE = "CeCILL-B"
CLASSIFIERS = CLASSIFIERS
AUTHOR = "CWBROWSER developers"
AUTHOR_EMAIL = "antoine.grigis@cea.fr"
PLATFORMS = "OS Independent"
VERSION = __version__
PROVIDES = ["cwbrowser"]
REQUIRES = [
    "paramiko",
]
EXTRA_REQUIRES = {}
