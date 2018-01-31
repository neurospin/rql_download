##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2018
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
CWBrowser is a Python package to request CubicWeb services.
"""

from __future__ import print_function
from .info import __version__
from .configure import info
from .cw_connection import CWInstanceConnection


print(info())
