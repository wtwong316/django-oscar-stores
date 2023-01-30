from django.contrib import messages
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.views import generic
from extra_views import CreateWithInlinesView, InlineFormSetFactory, UpdateWithInlinesView
from oscar.core.loading import get_class, get_classes, get_model
from django import forms

MapsContextMixin = get_class('sdfs.views', 'MapsContextMixin')
(DashboardSdfSearchForm,
 #OpeningHoursInline,
 #OpeningPeriodForm,
 SdfAddressForm,
 SdfForm) = get_classes('sdfs.dashboard.forms', ('DashboardSdfSearchForm',
                                                     #'OpeningHoursInline',
                                                     #'OpeningPeriodForm',
                                                     'SdfAddressForm',
                                                     'SdfForm'))
Sdf = get_model('sdfs', 'Sdf')
SdfSdu = get_model('sdfs', 'SdfSdu')
SdfGroup = get_model('sdfs', 'SdfGroup')
#OpeningPeriod = get_model('sdfs', 'OpeningPeriod')
SdfAddress = get_model('sdfs', 'SdfAddress')


class SdfListView(generic.ListView):
    model = Sdf
    template_name = "sdfs/dashboard/sdf_list.html"
    context_object_name = "sdf_list"
    paginate_by = 20
    filterform_class = DashboardSdfSearchForm

    def get_title(self):
        data = getattr(self.filterform, 'cleaned_data', {})

        name = data.get('name', None)
        address = data.get('address', None)

        if name and not address:
            return gettext('Sdfs matching "%s"') % (name)
        elif name and address:
            return gettext('Sdfs matching "%s" near "%s"') % (name, address)
        elif address:
            return gettext('Sdfs near "%s"') % (address)
        else:
            return gettext('Sdfs')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['filterform'] = self.filterform
        data['queryset_description'] = self.get_title()
        return data

    def get_queryset(self):
        qs = self.model.objects.all()
        self.filterform = self.filterform_class(self.request.GET)
        if self.filterform.is_valid():
            qs = self.filterform.apply_filters(qs)
        return qs


class SdfAddressInline(InlineFormSetFactory):

    model = SdfAddress
    form_class = SdfAddressForm
    factory_kwargs = {
        'extra': 1,
        'max_num': 1,
        'can_delete': False,
    }


#class OpeningPeriodInline(InlineFormSetFactory):
#    extra = 7
#    max_num = 7
#    model = OpeningPeriod
#    form_class = OpeningPeriodForm


class SdfEditMixin(MapsContextMixin):
    #inlines = [OpeningHoursInline, SdfAddressInline]
    inlines = [SdfAddressInline]


class SdfCreateView(SdfEditMixin, CreateWithInlinesView):
    model = Sdf
    template_name = "sdfs/dashboard/sdf_update.html"
    form_class = SdfForm
    success_url = reverse_lazy('sdfs-dashboard:sdf-list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = _("Create new SDF")
        return ctx

    def forms_invalid(self, form, inlines):
        messages.error(
            self.request,
            "Your submitted data was not valid - please correct the below errors")
        return super().forms_invalid(form, inlines)

    def forms_valid(self, form, inlines):
        response = super().forms_valid(form, inlines)

        msg = render_to_string('sdfs/dashboard/messages/sdf_saved.html',
                               {'sdf': self.object})
        messages.success(self.request, msg, extra_tags='safe')
        return response


class SdfUpdateView(SdfEditMixin, UpdateWithInlinesView):
    model = Sdf
    template_name = "sdfs/dashboard/sdf_update.html"
    form_class = SdfForm
    success_url = reverse_lazy('sdfs-dashboard:sdf-list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = self.object.name
        return ctx

    def forms_invalid(self, form, inlines):
        messages.error(
            self.request,
            "Your submitted data was not valid - please correct the below errors")
        return super().forms_invalid(form, inlines)

    def forms_valid(self, form, inlines):
        msg = render_to_string('sdfs/dashboard/messages/sdf_saved.html',
                               {'sdf': self.object})
        messages.success(self.request, msg, extra_tags='safe')
        return super().forms_valid(form, inlines)


class SdfDeleteView(generic.DeleteView):
    model = Sdf
    template_name = "sdfs/dashboard/sdf_delete.html"
    success_url = reverse_lazy('sdfs-dashboard:sdf-list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        """
        for time in self.object.opening_periods.all():
            time.delete()
        """
        return super().delete(request, *args, **kwargs)


class SdfSduListView(generic.ListView):
    model = SdfSdu
    context_object_name = 'sdu_list'
    template_name = "sdfs/dashboard/sdf_sdu_list.html"


class SdfSduCreateView(generic.CreateView):
    model = SdfSdu
    #fields = ['name', 'slug', 'size', 'household_size', 'rent', 'has_contract', 'has_individual_kitchen',
    fields = ['name', 'size', 'household_size', 'rent', 'has_contract', 'has_individual_kitchen',
              'has_individual_bath', 'has_exterior_window', 'internal_grading']
    template_name = "sdfs/dashboard/sdf_sdu_update.html"
    success_url = reverse_lazy('sdfs-dashboard:sdf-sdu-list')
    widgets = {"sdfId": forms.HiddenInput()}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = _("Create new SDU")
        if 'pk' in self.kwargs:
            ctx['pk'] = self.kwargs['pk']
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        form.instance.sdfId_id = self.kwargs['pk']
        messages.success(self.request, _("Sdu created"))
        return super(SdfSduCreateView, self).form_valid(form)

    def get_form(self):
        form = super().get_form()
        return form


class SdfSduUpdateView(generic.CreateView):
    model = SdfSdu
    template_name = "sdfs/dashboard/sdf_sdu_update.html"
    form_class = SdfForm
    success_url = reverse_lazy('sdfs-dashboard:sdf-sdu-list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = self.object.name
        return ctx

    def forms_invalid(self, form, inlines):
        messages.error(
            self.request,
            "Your submitted data was not valid - please correct the below errors")
        return super().forms_invalid(form, inlines)

    def forms_valid(self, form, inlines):
        msg = render_to_string('sdfs/dashboard/messages/sdu_saved.html',
                               {'sdu': self.object})
        messages.success(self.request, msg, extra_tags='safe')
        return super().forms_valid(form, inlines)


class SdfSduDeleteView(generic.DeleteView):
    model = SdfSdu
    template_name = "sdfs/dashboard/sdf_sdu_delete.html"
    success_url = reverse_lazy('sdfs-dashboard:sdf-sdu-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Sdf sdu deleted"))
        return response


class SdfGroupListView(generic.ListView):
    model = SdfGroup
    context_object_name = 'group_list'
    template_name = "sdfs/dashboard/sdf_group_list.html"


class SdfGroupCreateView(generic.CreateView):
    model = SdfGroup
    fields = ['name', 'slug']
    template_name = "sdfs/dashboard/sdf_group_update.html"
    success_url = reverse_lazy('sdfs-dashboard:sdf-group-list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = _("Create new SDF group")
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Sdf group created"))
        return response


class SdfGroupUpdateView(generic.UpdateView):
    model = SdfGroup
    fields = ['name', 'slug']
    template_name = "sdfs/dashboard/sdf_group_update.html"
    success_url = reverse_lazy('sdfs-dashboard:sdf-group-list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = self.object.name
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Sdf group updated"))
        return response


class SdfGroupDeleteView(generic.DeleteView):
    model = SdfGroup
    template_name = "sdfs/dashboard/sdf_group_delete.html"
    success_url = reverse_lazy('sdfs-dashboard:sdf-group-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Sdf group deleted"))
        return response
