from cubicweb.web.views.formrenderers import EntityFormRenderer
from cubicweb.predicates import is_instance
from logilab.common.registry import yes


class CWSearchEntityFormRenderer(EntityFormRenderer):
    __select__ = is_instance('CWSearch') & yes()
    main_form_title = _('Adding subset to your personnal repository')

    def render_buttons(self, w, form):
        for button in form.form_buttons:
            if button.cwaction == 'apply':
                form.form_buttons.remove(button)
        w("""<table width="100%%">
              <tbody>
               <tr><td align="center">
               %s
               %s
               </td></tr>
              </tbody>
             </table>""" % tuple(button.render(form)
                                 for button in form.form_buttons))

def registration_callback(vreg):
    vreg.register(CWSearchEntityFormRenderer)