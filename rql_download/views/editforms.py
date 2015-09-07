from cubicweb.web.views.editforms import CreationFormView


class CWSearchCreationFormView(CreationFormView):

    def form_title(self, entity):
        if entity.dc_type() == "CWSearch":
            self.w(u'')
        else:
            super(CWSearchCreationFormView, self).form_title(entity)

def registration_callback(vreg):
    vreg.register_and_replace(CWSearchCreationFormView, CreationFormView)