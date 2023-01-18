import datetime
from decimal import Decimal as D
from decimal import InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q, Sum, fields
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, FormView, ListView, UpdateView

from oscar.apps.inquiry import exceptions as inquiry_exceptions
from oscar.apps.payment.exceptions import PaymentError
from oscar.core.compat import UnicodeCSVWriter
from oscar.core.loading import get_class, get_model
from oscar.core.utils import datetime_combine, format_datetime
from oscar.views import sort_queryset
from oscar.views.generic import BulkEditMixin

Partner = get_model('partner', 'Partner')
Transaction = get_model('payment', 'Transaction')
SourceType = get_model('payment', 'SourceType')
Inquiry = get_model('inquiry', 'Inquiry')
InquiryNote = get_model('inquiry', 'InquiryNote')
ShippingAddress = get_model('inquiry', 'ShippingAddress')
Line = get_model('inquiry', 'Line')
ShippingEventType = get_model('inquiry', 'ShippingEventType')
PaymentEventType = get_model('inquiry', 'PaymentEventType')
EventHandlerMixin = get_class('inquiry.mixins', 'EventHandlerMixin')
InquiryStatsForm = get_class('dashboard.inquiries.forms', 'InquiryStatsForm')
InquirySearchForm = get_class('dashboard.inquiries.forms', 'InquirySearchForm')
InquiryNoteForm = get_class('dashboard.inquiries.forms', 'InquiryNoteForm')
ShippingAddressForm = get_class(
    'dashboard.inquiries.forms', 'ShippingAddressForm')
InquiryStatusForm = get_class('dashboard.inquiries.forms', 'InquiryStatusForm')


def queryset_inquiries_for_user(user):
    """
    Returns a queryset of all inquiries that a user is allowed to access.
    A staff user may access all inquiries.
    To allow access to an inquiry for a non-staff user, at least one line's
    partner has to have the user in the partner's list.
    """
    queryset = Inquiry._default_manager.select_related(
        'billing_address', 'billing_address__country',
        'shipping_address', 'shipping_address__country',
        'user'
    ).prefetch_related('lines', 'status_changes')
    if user.is_staff:
        return queryset
    else:
        partners = Partner._default_manager.filter(users=user)
        return queryset.filter(lines__partner__in=partners).distinct()


def get_inquiry_for_user_or_404(user, number):
    try:
        return queryset_inquiries_for_user(user).get(number=number)
    except ObjectDoesNotExist:
        raise Http404()


class InquiryStatsView(FormView):
    """
    Dashboard view for inquiry statistics.
    Supports the permission-based dashboard.
    """
    template_name = 'oscar/dashboard/inquiries/statistics.html'
    form_class = InquiryStatsForm

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def form_valid(self, form):
        ctx = self.get_context_data(form=form,
                                    filters=form.get_filters())
        return self.render_to_response(ctx)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['data'] = self.request.GET
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        filters = kwargs.get('filters', {})
        ctx.update(self.get_stats(filters))
        ctx['title'] = kwargs['form'].get_filter_description()
        return ctx

    def get_stats(self, filters):
        inquiries = queryset_inquiries_for_user(self.request.user).filter(**filters)
        stats = {
            'total_inquiries': inquiries.count(),
            'total_lines': Line.objects.filter(inquiry__in=inquiries).count(),
            'total_revenue': inquiries.aggregate(
                Sum('total_incl_tax'))['total_incl_tax__sum'] or D('0.00'),
            'inquiry_status_breakdown': inquiries.order_by('status').values(
                'status').annotate(freq=Count('id'))
        }
        return stats


class InquiryListView(EventHandlerMixin, BulkEditMixin, ListView):
    """
    Dashboard view for a list of inquiries.
    Supports the permission-based dashboard.
    """
    model = Inquiry
    context_object_name = 'inquiries'
    template_name = 'oscar/dashboard/inquiries/inquiry_list.html'
    form_class = InquirySearchForm
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE
    actions = ('download_selected_inquiries', 'change_inquiry_statuses')
    CSV_COLUMNS = {
        'number': _('Inquiry number'),
        'value': _('Inquiry value'),
        'date': _('Date of purchase'),
        'num_items': _('Number of items'),
        'status': _('Inquiry status'),
        'customer': _('Customer email address'),
        'shipping_address_name': _('Deliver to name'),
        'billing_address_name': _('Bill to name'),
    }

    def dispatch(self, request, *args, **kwargs):
        # base_queryset is equal to all inquiries the user is allowed to access
        self.base_queryset = queryset_inquiries_for_user(
            request.user).order_by('-date_placed')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if 'inquiry_number' in request.GET and request.GET.get(
                'response_format', 'html') == 'html':
            # Redirect to Inquiry detail page if valid inquiry number is given
            try:
                inquiry = self.base_queryset.get(
                    number=request.GET['inquiry_number'])
            except Inquiry.DoesNotExist:
                pass
            else:
                return redirect(
                    'dashboard:inquiry-detail', number=inquiry.number)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):  # noqa (too complex (19))
        """
        Build the queryset for this list.
        """
        queryset = sort_queryset(self.base_queryset, self.request,
                                 ['number', 'total_incl_tax'])

        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return queryset

        data = self.form.cleaned_data

        if data['inquiry_number']:
            queryset = self.base_queryset.filter(
                number__istartswith=data['inquiry_number'])

        if data['name']:
            # If the value is two words, then assume they are first name and
            # last name
            parts = data['name'].split()
            allow_anon = getattr(settings, 'OSCAR_ALLOW_ANON_CHECKOUT', False)

            if len(parts) == 1:
                parts = [data['name'], data['name']]
            else:
                parts = [parts[0], parts[1:]]

            filter = Q(user__first_name__istartswith=parts[0])
            filter |= Q(user__last_name__istartswith=parts[1])
            if allow_anon:
                filter |= Q(billing_address__first_name__istartswith=parts[0])
                filter |= Q(shipping_address__first_name__istartswith=parts[0])
                filter |= Q(billing_address__last_name__istartswith=parts[1])
                filter |= Q(shipping_address__last_name__istartswith=parts[1])

            queryset = queryset.filter(filter).distinct()

        if data['sdu_title']:
            queryset = queryset.filter(
                lines__title__istartswith=data['sdu_title']).distinct()

        if data['upc']:
            queryset = queryset.filter(lines__upc=data['upc'])

        if data['partner_sku']:
            queryset = queryset.filter(lines__partner_sku=data['partner_sku'])

        if data['date_from'] and data['date_to']:
            date_to = datetime_combine(data['date_to'], datetime.time.max)
            date_from = datetime_combine(data['date_from'], datetime.time.min)
            queryset = queryset.filter(
                date_placed__gte=date_from, date_placed__lt=date_to)
        elif data['date_from']:
            date_from = datetime_combine(data['date_from'], datetime.time.min)
            queryset = queryset.filter(date_placed__gte=date_from)
        elif data['date_to']:
            date_to = datetime_combine(data['date_to'], datetime.time.max)
            queryset = queryset.filter(date_placed__lt=date_to)

        if data['voucher']:
            queryset = queryset.filter(
                discounts__voucher_code=data['voucher']).distinct()

        if data['payment_method']:
            queryset = queryset.filter(
                sources__source_type__code=data['payment_method']).distinct()

        if data['status']:
            queryset = queryset.filter(status=data['status'])

        return queryset

    def get_search_filter_descriptions(self):  # noqa (too complex (19))
        """Describe the filters used in the search.

        These are user-facing messages describing what filters
        were used to filter inquiries in the search query.

        Returns:
            list of unicode messages

        """
        descriptions = []

        # Attempt to retrieve data from the submitted form
        # If the form hasn't been submitted, then `cleaned_data`
        # won't be set, so default to None.
        data = getattr(self.form, 'cleaned_data', None)

        if data is None:
            return descriptions

        if data.get('inquiry_number'):
            descriptions.append(
                _('Inquiry number starts with "{inquiry_number}"').format(
                    inquiry_number=data['inquiry_number']
                )
            )

        if data.get('name'):
            descriptions.append(
                _('Customer name matches "{customer_name}"').format(
                    customer_name=data['name']
                )
            )

        if data.get('sdu_title'):
            descriptions.append(
                _('Sdu name matches "{sdu_name}"').format(
                    sdu_name=data['sdu_title']
                )
            )

        if data.get('upc'):
            descriptions.append(
                # Translators: "UPC" means "universal sdu code" and it is
                # used to uniquely identify a sdu in an online store.
                # "Item" in this context means an item in an inquiry placed
                # in an online store.
                _('Includes an item with UPC "{upc}"').format(
                    upc=data['upc']
                )
            )

        if data.get('partner_sku'):
            descriptions.append(
                # Translators: "SKU" means "stock keeping unit" and is used to
                # identify sdus that can be shipped from an online store.
                # A "partner" is a company that ships items to users who
                # buy things in an online store.
                _('Includes an item with partner SKU "{partner_sku}"').format(
                    partner_sku=data['partner_sku']
                )
            )

        if data.get('date_from') and data.get('date_to'):
            descriptions.append(
                # Translators: This string refers to inquiries in an online
                # store that were made within a particular date range.
                _('Placed between {start_date} and {end_date}').format(
                    start_date=data['date_from'],
                    end_date=data['date_to']
                )
            )

        elif data.get('date_from'):
            descriptions.append(
                # Translators: This string refers to inquiries in an online store
                # that were made after a particular date.
                _('Placed after {start_date}').format(
                    start_date=data['date_from'])
            )

        elif data.get('date_to'):
            end_date = data['date_to'] + datetime.timedelta(days=1)
            descriptions.append(
                # Translators: This string refers to inquiries in an online store
                # that were made before a particular date.
                _('Placed before {end_date}').format(end_date=end_date)
            )

        if data.get('voucher'):
            descriptions.append(
                # Translators: A "voucher" is a coupon that can be applied to
                # an inquiry in an online store in inquiry to receive a discount.
                # The voucher "code" is a string that users can enter to
                # receive the discount.
                _('Used voucher code "{voucher_code}"').format(
                    voucher_code=data['voucher'])
            )

        if data.get('payment_method'):
            payment_type = SourceType.objects.get(code=data['payment_method'])
            descriptions.append(
                # Translators: A payment method is a way of paying for an
                # item in an online store.  For example, a user can pay
                # with a credit card or PayPal.
                _('Paid using {payment_method}').format(
                    payment_method=payment_type.name
                )
            )

        if data.get('status'):
            descriptions.append(
                # Translators: This string refers to an inquiry in an
                # online store.  Some examples of inquiry status are
                # "purchased", "cancelled", or "refunded".
                _('Inquiry status is {inquiry_status}').format(
                    inquiry_status=data['status'])
            )

        return descriptions

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = self.form
        ctx['inquiry_statuses'] = Inquiry.all_statuses()
        ctx['search_filters'] = self.get_search_filter_descriptions()
        return ctx

    def is_csv_download(self):
        return self.request.GET.get('response_format', None) == 'csv'

    def get_paginate_by(self, queryset):
        return None if self.is_csv_download() else self.paginate_by

    def render_to_response(self, context, **response_kwargs):
        if self.is_csv_download():
            return self.download_selected_inquiries(
                self.request,
                context['object_list'])
        return super().render_to_response(
            context, **response_kwargs)

    def get_download_filename(self, request):
        return 'inquiries.csv'

    def get_row_values(self, inquiry):
        row = {'number': inquiry.number, 'customer': inquiry.email, 'num_items': inquiry.num_items,
               'date': format_datetime(inquiry.date_placed, 'DATETIME_FORMAT'), 'value': inquiry.total_incl_tax,
               'status': inquiry.status}
        if inquiry.shipping_address:
            row['shipping_address_name'] = inquiry.shipping_address.name
        if inquiry.billing_address:
            row['billing_address_name'] = inquiry.billing_address.name
        return row

    def download_selected_inquiries(self, request, inquiries):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s' \
            % self.get_download_filename(request)
        writer = UnicodeCSVWriter(open_file=response)

        writer.writerow(self.CSV_COLUMNS.values())
        for inquiry in inquiries:
            row_values = self.get_row_values(inquiry)
            writer.writerow([row_values.get(column, "") for column in self.CSV_COLUMNS])
        return response

    def change_inquiry_statuses(self, request, inquiries):
        for inquiry in inquiries:
            self.change_inquiry_status(request, inquiry)
        return redirect('dashboard:inquiry-list')

    def change_inquiry_status(self, request, inquiry):
        # This method is pretty similar to what
        # InquiryDetailView.change_inquiry_status does. Ripe for refactoring.
        new_status = request.POST['new_status'].strip()
        if not new_status:
            messages.error(request, _("The new status '%s' is not valid")
                           % new_status)
        elif new_status not in inquiry.available_statuses():
            messages.error(request, _("The new status '%s' is not valid for"
                                      " this inquiry") % new_status)
        else:
            handler = self.get_handler(user=request.user)
            old_status = inquiry.status
            try:
                handler.handle_inquiry_status_change(inquiry, new_status)
            except PaymentError as e:
                messages.error(request, _("Unable to change inquiry status due"
                                          " to payment error: %s") % e)
            else:
                msg = _("Inquiry status changed from '%(old_status)s' to"
                        " '%(new_status)s'") % {'old_status': old_status,
                                                'new_status': new_status}
                messages.info(request, msg)
                inquiry.notes.create(
                    user=request.user, message=msg, note_type=InquiryNote.SYSTEM)


class InquiryDetailView(EventHandlerMixin, DetailView):
    """
    Dashboard view to display a single inquiry.

    Supports the permission-based dashboard.
    """
    model = Inquiry
    context_object_name = 'inquiry'
    template_name = 'oscar/dashboard/inquiries/inquiry_detail.html'

    # These strings are method names that are allowed to be called from a
    # submitted form.
    inquiry_actions = ('save_note', 'delete_note', 'change_inquiry_status',
                     'create_inquiry_payment_event')
    line_actions = ('change_line_statuses', 'create_shipping_event',
                    'create_payment_event')

    def get_object(self, queryset=None):
        return get_inquiry_for_user_or_404(
            self.request.user, self.kwargs['number'])

    def get_inquiry_lines(self):
        return self.object.lines.all()

    def post(self, request, *args, **kwargs):
        # For POST requests, we use a dynamic dispatch technique where a
        # parameter specifies what we're trying to do with the form submission.
        # We distinguish between inquiry-level actions and line-level actions.

        inquiry = self.object = self.get_object()

        # Look for inquiry-level action first
        if 'inquiry_action' in request.POST:
            return self.handle_inquiry_action(
                request, inquiry, request.POST['inquiry_action'])

        # Look for line-level action
        if 'line_action' in request.POST:
            return self.handle_line_action(
                request, inquiry, request.POST['line_action'])

        return self.reload_page(error=_("No valid action submitted"))

    def handle_inquiry_action(self, request, inquiry, action):
        if action not in self.inquiry_actions:
            return self.reload_page(error=_("Invalid action"))
        return getattr(self, action)(request, inquiry)

    def handle_line_action(self, request, inquiry, action):
        if action not in self.line_actions:
            return self.reload_page(error=_("Invalid action"))

        # Load requested lines
        line_ids = request.POST.getlist('selected_line')
        if len(line_ids) == 0:
            return self.reload_page(error=_(
                "You must select some lines to act on"))

        lines = self.get_inquiry_lines()
        lines = lines.filter(id__in=line_ids)
        if len(line_ids) != len(lines):
            return self.reload_page(error=_("Invalid lines requested"))

        # Build list of line quantities
        line_quantities = []
        for line in lines:
            qty = request.POST.get('selected_line_qty_%s' % line.id)
            try:
                qty = int(qty)
            except ValueError:
                qty = None
            if qty is None or qty <= 0:
                error_msg = _("The entered quantity for line #%s is not valid")
                return self.reload_page(error=error_msg % line.id)
            elif qty > line.quantity:
                error_msg = _(
                    "The entered quantity for line #%(line_id)s "
                    "should not be higher than %(quantity)s")
                kwargs = {'line_id': line.id, 'quantity': line.quantity}
                return self.reload_page(error=error_msg % kwargs)

            line_quantities.append(qty)

        return getattr(self, action)(
            request, inquiry, lines, line_quantities)

    def reload_page(self, fragment=None, error=None):
        url = reverse('dashboard:inquiry-detail',
                      kwargs={'number': self.object.number})
        if fragment:
            url += '#' + fragment
        if error:
            messages.error(self.request, error)
        return HttpResponseRedirect(url)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_tab'] = kwargs.get('active_tab', 'lines')

        # Forms
        ctx['note_form'] = self.get_inquiry_note_form()
        ctx['inquiry_status_form'] = self.get_inquiry_status_form()

        ctx['lines'] = self.get_inquiry_lines()
        ctx['line_statuses'] = Line.all_statuses()
        ctx['shipping_event_types'] = ShippingEventType.objects.all()
        ctx['payment_event_types'] = PaymentEventType.objects.all()

        ctx['payment_transactions'] = self.get_payment_transactions()

        return ctx

    # Data fetching methods for template context

    def get_payment_transactions(self):
        return Transaction.objects.filter(
            source__inquiry=self.object)

    def get_inquiry_note_form(self):
        kwargs = {
            'inquiry': self.object,
            'user': self.request.user,
            'data': None
        }
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST
        note_id = self.kwargs.get('note_id', None)
        if note_id:
            note = get_object_or_404(InquiryNote, inquiry=self.object, id=note_id)
            if note.is_editable():
                kwargs['instance'] = note
        return InquiryNoteForm(**kwargs)

    def get_inquiry_status_form(self):
        data = None
        if self.request.method == 'POST':
            data = self.request.POST
        return InquiryStatusForm(inquiry=self.object, data=data)

    # Inquiry-level actions

    def save_note(self, request, inquiry):
        form = self.get_inquiry_note_form()
        if form.is_valid():
            form.save()
            messages.success(self.request, _("Note saved"))
            return self.reload_page(fragment='notes')

        ctx = self.get_context_data(note_form=form, active_tab='notes')
        return self.render_to_response(ctx)

    def delete_note(self, request, inquiry):
        try:
            note = inquiry.notes.get(id=request.POST.get('note_id', None))
        except ObjectDoesNotExist:
            messages.error(request, _("Note cannot be deleted"))
        else:
            messages.info(request, _("Note deleted"))
            note.delete()
        return self.reload_page()

    def change_inquiry_status(self, request, inquiry):
        form = self.get_inquiry_status_form()
        if not form.is_valid():
            return self.reload_page(error=_("Invalid form submission"))

        old_status, new_status = inquiry.status, form.cleaned_data['new_status']
        handler = self.get_handler(user=request.user)

        success_msg = _(
            "Inquiry status changed from '%(old_status)s' to "
            "'%(new_status)s'") % {'old_status': old_status,
                                   'new_status': new_status}
        try:
            handler.handle_inquiry_status_change(
                inquiry, new_status, note_msg=success_msg)
        except PaymentError as e:
            messages.error(
                request, _("Unable to change inquiry status due to "
                           "payment error: %s") % e)
        except inquiry_exceptions.InvalidInquiryStatus:
            # The form should validate against this, so we should only end up
            # here during race conditions.
            messages.error(
                request, _("Unable to change inquiry status as the requested "
                           "new status is not valid"))
        else:
            messages.info(request, success_msg)
        return self.reload_page()

    def create_inquiry_payment_event(self, request, inquiry):
        """
        Create a payment event for the whole inquiry
        """
        amount_str = request.POST.get('amount', None)
        try:
            amount = D(amount_str)
        except InvalidOperation:
            messages.error(request, _("Please choose a valid amount"))
            return self.reload_page()
        return self._create_payment_event(request, inquiry, amount)

    # Line-level actions

    def change_line_statuses(self, request, inquiry, lines, quantities):
        new_status = request.POST['new_status'].strip()
        if not new_status:
            messages.error(request, _("The new status '%s' is not valid")
                           % new_status)
            return self.reload_page()
        errors = []
        for line in lines:
            if new_status not in line.available_statuses():
                errors.append(_("'%(status)s' is not a valid new status for"
                                " line %(line_id)d") % {'status': new_status,
                                                        'line_id': line.id})
        if errors:
            messages.error(request, "\n".join(errors))
            return self.reload_page()

        msgs = []
        for line in lines:
            msg = _("Status of line #%(line_id)d changed from '%(old_status)s'"
                    " to '%(new_status)s'") % {'line_id': line.id,
                                               'old_status': line.status,
                                               'new_status': new_status}
            msgs.append(msg)
            line.set_status(new_status)
        message = "\n".join(msgs)
        messages.info(request, message)
        inquiry.notes.create(user=request.user, message=message,
                           note_type=InquiryNote.SYSTEM)
        return self.reload_page()

    def create_shipping_event(self, request, inquiry, lines, quantities):
        code = request.POST['shipping_event_type']
        try:
            event_type = ShippingEventType._default_manager.get(code=code)
        except ShippingEventType.DoesNotExist:
            messages.error(request, _("The event type '%s' is not valid")
                           % code)
            return self.reload_page()

        reference = request.POST.get('reference', None)
        try:
            self.get_handler().handle_shipping_event(inquiry, event_type, lines,
                                                     quantities,
                                                     reference=reference)
        except inquiry_exceptions.InvalidShippingEvent as e:
            messages.error(request,
                           _("Unable to create shipping event: %s") % e)
        except inquiry_exceptions.InvalidStatus as e:
            messages.error(request,
                           _("Unable to create shipping event: %s") % e)
        except PaymentError as e:
            messages.error(request, _("Unable to create shipping event due to"
                                      " payment error: %s") % e)
        else:
            messages.success(request, _("Shipping event created"))
        return self.reload_page()

    def create_payment_event(self, request, inquiry, lines, quantities):
        """
        Create a payment event for a subset of inquiry lines
        """
        amount_str = request.POST.get('amount', None)

        # If no amount passed, then we add up the total of the selected lines
        if not amount_str:
            amount = sum([line.line_price_incl_tax for line in lines])
        else:
            try:
                amount = D(amount_str)
            except InvalidOperation:
                messages.error(request, _("Please choose a valid amount"))
                return self.reload_page()

        return self._create_payment_event(request, inquiry, amount, lines,
                                          quantities)

    def _create_payment_event(self, request, inquiry, amount, lines=None,
                              quantities=None):
        code = request.POST.get('payment_event_type')
        try:
            event_type = PaymentEventType._default_manager.get(code=code)
        except PaymentEventType.DoesNotExist:
            messages.error(
                request, _("The event type '%s' is not valid") % code)
            return self.reload_page()
        try:
            self.get_handler().handle_payment_event(
                inquiry, event_type, amount, lines, quantities)
        except PaymentError as e:
            messages.error(request, _("Unable to create payment event due to"
                                      " payment error: %s") % e)
        except inquiry_exceptions.InvalidPaymentEvent as e:
            messages.error(
                request, _("Unable to create payment event: %s") % e)
        else:
            messages.info(request, _("Payment event created"))
        return self.reload_page()


class LineDetailView(DetailView):
    """
    Dashboard view to show a single line of an inquiry.
    Supports the permission-based dashboard.
    """
    model = Line
    context_object_name = 'line'
    template_name = 'oscar/dashboard/inquiries/line_detail.html'

    def get_object(self, queryset=None):
        inquiry = get_inquiry_for_user_or_404(self.request.user,
                                          self.kwargs['number'])
        try:
            return inquiry.lines.get(pk=self.kwargs['line_id'])
        except self.model.DoesNotExist:
            raise Http404()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['inquiry'] = self.object.inquiry
        return ctx


def get_changes_between_models(model1, model2, excludes=None):
    """
    Return a dict of differences between two model instances
    """
    if excludes is None:
        excludes = []
    changes = {}
    for field in model1._meta.fields:
        if (isinstance(field, (fields.AutoField,
                               fields.related.RelatedField))
                or field.name in excludes):
            continue

        if field.value_from_object(model1) != field.value_from_object(model2):
            changes[field.verbose_name] = (field.value_from_object(model1),
                                           field.value_from_object(model2))
    return changes


def get_change_summary(model1, model2):
    """
    Generate a summary of the changes between two address models
    """
    changes = get_changes_between_models(model1, model2, ['search_text'])
    change_descriptions = []
    for field, delta in changes.items():
        change_descriptions.append(_("%(field)s changed from '%(old_value)s'"
                                     " to '%(new_value)s'")
                                   % {'field': field,
                                      'old_value': delta[0],
                                      'new_value': delta[1]})
    return "\n".join(change_descriptions)


class ShippingAddressUpdateView(UpdateView):
    """
    Dashboard view to update an inquiry's shipping address.
    Supports the permission-based dashboard.
    """
    model = ShippingAddress
    context_object_name = 'address'
    template_name = 'oscar/dashboard/inquiries/shippingaddress_form.html'
    form_class = ShippingAddressForm

    def get_object(self, queryset=None):
        inquiry = get_inquiry_for_user_or_404(self.request.user,
                                          self.kwargs['number'])
        return get_object_or_404(self.model, inquiry=inquiry)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['inquiry'] = self.object.inquiry
        return ctx

    def form_valid(self, form):
        old_address = ShippingAddress.objects.get(id=self.object.id)
        response = super().form_valid(form)
        changes = get_change_summary(old_address, self.object)
        if changes:
            msg = _("Delivery address updated:\n%s") % changes
            self.object.inquiry.notes.create(user=self.request.user, message=msg,
                                           note_type=InquiryNote.SYSTEM)
        return response

    def get_success_url(self):
        messages.info(self.request, _("Delivery address updated"))
        return reverse('dashboard:inquiry-detail',
                       kwargs={'number': self.object.inquiry.number, })
