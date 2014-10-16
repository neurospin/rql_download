#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# CW import
from cubicweb.web.views import uicfg
from cubicweb.web.formwidgets import FieldWidget
from cubicweb import tags


###############################################################################
# CWSearch Widgets
###############################################################################

class CWSearchPathWidget(FieldWidget):
    """ Custom widget to edit the query string from the 'path' attribute.

    It deals with url quoting nicely so that the user edit the unquoted value.
    """
    def _render(self, form, field, renderer):
        """ Create the 'path' form field.
        """
        # Get the path form value
        values, attrs = self.values_and_attributes(form, field)
        attrs.setdefault("onkeyup", "autogrow(this)")

        # Check the inputs
        if not values:
            value = u""
        elif len(values) == 1:
            value = values[0]
        else:
            raise ValueError("A textarea is not supposed to be multivalued")

        # Extract the rql
        if value:
            try:
                path, rql = value.split("?", 1)
            except ValueError:
                rql = ""
        else:
            rql = ""

        # Get unquoted rql value
        rql = [v for k, v in form._cw.url_parse_qsl(rql)][0]
        rql = rql.replace("DISTINCT ","")

        # Compute render properties
        lines = rql.splitlines()
        linecount = len(lines)
        for line in lines:
            linecount += len(line) / 80
        attrs.setdefault("cols", 80)
        attrs.setdefault("rows", min(15, linecount + 2))

        # Create the request render widget
        return tags.textarea(rql, name=field.input_name(form, self.suffix),
                             **attrs)


# Associate the CWSearch form widget
_affk = uicfg.autoform_field_kwargs
_affk.tag_attribute(("CWSearch", "path"), {"widget": CWSearchPathWidget})
