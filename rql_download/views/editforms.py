##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Cubicweb import
from cubicweb.web.views.editforms import CreationFormView


class CWSearchCreationFormView(CreationFormView):
    title = _("Add search")

    def form_title(self, entity):
        if entity.dc_type() == "CWSearch":
            self.w(u"")
        else:
            super(CWSearchCreationFormView, self).form_title(entity)


def registration_callback(vreg):
    vreg.register_and_replace(CWSearchCreationFormView, CreationFormView)
