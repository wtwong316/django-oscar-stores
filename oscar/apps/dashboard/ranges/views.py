from io import TextIOWrapper

from django.conf import settings
from django.contrib import messages
from django.core import exceptions
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import HttpResponse, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from django.views.generic import (
    CreateView, DeleteView, ListView, UpdateView, View)

from oscar.core.loading import get_classes, get_model
from oscar.views.generic import BulkEditMixin

Range = get_model('offer', 'Range')
RangeSdu = get_model('offer', 'RangeSdu')
RangeSduFileUpload = get_model('offer', 'RangeSduFileUpload')
Sdu = get_model('catalogue', 'Sdu')
RangeForm, RangeSduForm = get_classes('dashboard.ranges.forms',
                                          ['RangeForm', 'RangeSduForm'])


class RangeListView(ListView):
    model = Range
    context_object_name = 'ranges'
    template_name = 'oscar/dashboard/ranges/range_list.html'
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE


class RangeCreateView(CreateView):
    model = Range
    template_name = 'oscar/dashboard/ranges/range_form.html'
    form_class = RangeForm

    def get_success_url(self):
        if 'action' in self.request.POST:
            return reverse('dashboard:range-sdus',
                           kwargs={'pk': self.object.id})
        else:
            msg = render_to_string(
                'oscar/dashboard/ranges/messages/range_saved.html',
                {'range': self.object})
            messages.success(self.request, msg, extra_tags='safe noicon')
            return reverse('dashboard:range-list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = _("Create range")
        return ctx


class RangeUpdateView(UpdateView):
    model = Range
    template_name = 'oscar/dashboard/ranges/range_form.html'
    form_class = RangeForm

    def get_object(self):
        obj = super().get_object()
        if not obj.is_editable:
            raise exceptions.PermissionDenied("Not allowed")
        return obj

    def get_success_url(self):
        if 'action' in self.request.POST:
            return reverse('dashboard:range-sdus',
                           kwargs={'pk': self.object.id})
        else:
            msg = render_to_string(
                'oscar/dashboard/ranges/messages/range_saved.html',
                {'range': self.object})
            messages.success(self.request, msg, extra_tags='safe noicon')
            return reverse('dashboard:range-list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['range'] = self.object
        ctx['title'] = self.object.name
        return ctx


class RangeDeleteView(DeleteView):
    model = Range
    template_name = 'oscar/dashboard/ranges/range_delete.html'
    context_object_name = 'range'

    def get_success_url(self):
        messages.warning(self.request, _("Range deleted"))
        return reverse('dashboard:range-list')


class RangeSduListView(BulkEditMixin, ListView):
    model = Sdu
    template_name = 'oscar/dashboard/ranges/range_sdu_list.html'
    context_object_name = 'sdus'
    actions = ('remove_selected_sdus', 'add_sdus')
    form_class = RangeSduForm
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        if request.POST.get('action', None) == 'add_sdus':
            return self.add_sdus(request)
        return super().post(request, *args, **kwargs)

    def get_range(self):
        if not hasattr(self, '_range'):
            self._range = get_object_or_404(Range, id=self.kwargs['pk'])
        return self._range

    def get_queryset(self):
        sdus = self.get_range().all_sdus()
        return sdus.order_by('rangesdu__display_order')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        range = self.get_range()
        ctx['range'] = range
        if 'form' not in ctx:
            ctx['form'] = self.form_class(range)
        return ctx

    def remove_selected_sdus(self, request, sdus):
        range = self.get_range()
        for sdu in sdus:
            range.remove_sdu(sdu)
        num_sdus = len(sdus)
        messages.success(
            request,
            ngettext("Removed %d sdu from range", "Removed %d sdus from range", num_sdus) % num_sdus
        )
        return HttpResponseRedirect(self.get_success_url(request))

    def add_sdus(self, request):
        range = self.get_range()
        form = self.form_class(range, request.POST, request.FILES)
        if not form.is_valid():
            ctx = self.get_context_data(form=form,
                                        object_list=self.object_list)
            return self.render_to_response(ctx)

        self.handle_query_sdus(request, range, form)
        self.handle_file_sdus(request, range, form)
        return HttpResponseRedirect(self.get_success_url(request))

    def handle_query_sdus(self, request, range, form):
        sdus = form.get_sdus()
        if not sdus:
            return

        for sdu in sdus:
            range.add_sdu(sdu)

        num_sdus = len(sdus)
        messages.success(
            request,
            ngettext("%d sdu added to range", "%d sdus added to range", num_sdus) % num_sdus
        )
        dupe_skus = form.get_duplicate_skus()
        if dupe_skus:
            messages.warning(
                request,
                _("The sdus with SKUs or UPCs matching %s are already "
                  "in this range") % ", ".join(dupe_skus))

        missing_skus = form.get_missing_skus()
        if missing_skus:
            messages.warning(
                request,
                _("No sdu(s) were found with SKU or UPC matching %s") %
                ", ".join(missing_skus))
        self.check_imported_sdus_sku_duplicates(request, sdus)

    def handle_file_sdus(self, request, range, form):
        if 'file_upload' not in request.FILES:
            return
        f = request.FILES['file_upload']
        upload = self.create_upload_object(request, range, f)
        sdus = upload.process(TextIOWrapper(f, encoding=request.encoding))
        if not upload.was_processing_successful():
            messages.error(request, upload.error_message)
        else:
            msg = render_to_string(
                'oscar/dashboard/ranges/messages/range_sdus_saved.html',
                {'range': range,
                 'upload': upload})
            messages.success(request, msg, extra_tags='safe noicon block')
        self.check_imported_sdus_sku_duplicates(request, sdus)

    def create_upload_object(self, request, range, f):
        upload = RangeSduFileUpload.objects.create(
            range=range,
            uploaded_by=request.user,
            filepath=f.name,
            size=f.size
        )
        return upload

    def check_imported_sdus_sku_duplicates(self, request, queryset):
        dupe_sku_sdus = queryset.values('stockrecords__partner_sku')\
                                    .annotate(total=Count('stockrecords__partner_sku'))\
                                    .filter(total__gt=1).order_by('stockrecords__partner_sku')
        if dupe_sku_sdus:
            dupe_skus = [p['stockrecords__partner_sku'] for p in dupe_sku_sdus]
            messages.warning(
                request,
                _("There are more than one sdu with SKU %s") %
                ", ".join(dupe_skus)
            )


class RangeReorderView(View):
    def post(self, request, pk):
        order = dict(request.POST).get('sdu')
        self._save_page_order(order)
        return HttpResponse(status=200)

    def _save_page_order(self, order):
        """
        Save the order of the sdus within range.
        """
        range = get_object_or_404(Range, pk=self.kwargs['pk'])
        for index, item in enumerate(order):
            entry = RangeSdu.objects.get(range=range, sdu__pk=item)
            if entry.display_order != index:
                entry.display_order = index
                entry.save()
