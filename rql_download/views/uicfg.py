#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

from cubicweb.web import formwidgets as fwdgs
from cubicweb.web.views import uicfg
from cubicweb.web.views.uicfg import autoform_field_kwargs as affk
from cwsearch import CWSearchPathWidget

uicfg.autoform_section.hide_fields("CWSearch", ("rset", "result",
                                                "expiration_date", "rset_type",
                                                ))


def rset_type_choices(form, field, **kw):
    res = set()
    for vid, views in form._cw.vreg["views"].iteritems():
        for v in views:
            if not v.templatable and v.binary:
                res.add(v.__regid__)
    return list(res)


affk.set_field_kwargs("CWSearch", "rset_type",
                      widget=fwdgs.Select(),
                      choices=("jsonexport", ))
                      #choices=rset_type_choices)
affk.set_field_kwargs("CWSearch", "path",
                      widget=CWSearchPathWidget)