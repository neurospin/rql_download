#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013-2015
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

from cubicweb.web.views.formrenderers import EntityFormRenderer
from cubicweb.predicates import is_instance
from logilab.common.registry import yes


class CWSearchEntityFormRenderer(EntityFormRenderer):
    __select__ = is_instance('CWSearch') & yes()
    main_form_title = _('Add subset to cart')

    def render_buttons(self, w, form):
        for button in form.form_buttons:
            if button.cwaction == 'apply':
                form.form_buttons.remove(button)
        super(CWSearchEntityFormRenderer, self).render_buttons(w, form)


def registration_callback(vreg):
    vreg.register(CWSearchEntityFormRenderer)
