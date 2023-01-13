from django import http
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views import generic

from oscar.core.loading import get_class, get_model

Sdu = get_model('catalogue', 'Sdu')
SduAlert = get_model('renter', 'SduAlert')
PageTitleMixin = get_class('renter.mixins', 'PageTitleMixin')
SduAlertForm = get_class('renter.forms', 'SduAlertForm')
AlertsDispatcher = get_class('renter.alerts.utils', 'AlertsDispatcher')


class SduAlertListView(PageTitleMixin, generic.ListView):
    model = SduAlert
    template_name = 'oscar/renter/alerts/alert_list.html'
    context_object_name = 'alerts'
    page_title = _('Sdu Alerts')
    active_tab = 'alerts'

    def get_queryset(self):
        return SduAlert.objects.select_related().filter(
            user=self.request.user,
            date_closed=None,
        )


class SduAlertCreateView(generic.CreateView):
    """
    View to create a new sdu alert based on a registered user
    or an email address provided by an anonymous user.
    """
    model = SduAlert
    form_class = SduAlertForm
    template_name = 'oscar/renter/alerts/form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['sdu'] = self.sdu
        ctx['alert_form'] = ctx.pop('form')
        return ctx

    def get(self, request, *args, **kwargs):
        sdu = get_object_or_404(Sdu, pk=self.kwargs['pk'])
        return http.HttpResponseRedirect(sdu.get_absolute_url())

    def post(self, request, *args, **kwargs):
        self.sdu = get_object_or_404(Sdu, pk=self.kwargs['pk'])
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['sdu'] = self.sdu
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object.is_anonymous:
            AlertsDispatcher().send_sdu_alert_confirmation_email_for_user(self.object)
        return response

    def get_success_url(self):
        if self.object.user:
            msg = _("An alert has been created")
        else:
            msg = _("A confirmation email has been sent to %s") \
                % self.object.email
        messages.success(self.request, msg)
        return self.object.sdu.get_absolute_url()


class SduAlertConfirmView(generic.RedirectView):
    permanent = False

    def get(self, request, *args, **kwargs):
        self.alert = get_object_or_404(SduAlert, key=kwargs['key'])
        self.update_alert()
        return super().get(request, *args, **kwargs)

    def update_alert(self):
        if self.alert.can_be_confirmed:
            self.alert.confirm()
            messages.success(self.request, _("Your stock alert is now active"))
        else:
            messages.error(self.request, _("Your stock alert cannot be"
                                           " confirmed"))

    def get_redirect_url(self, **kwargs):
        return self.alert.sdu.get_absolute_url()


class SduAlertCancelView(generic.RedirectView):
    """
    This function allows canceling alerts by supplying the key (used for
    anonymously created alerts) or the pk (used for alerts created by a
    authenticated user).

    Specifying the redirect url is possible by supplying a 'next' GET
    parameter.  It defaults to showing the associated sdu page.
    """
    permanent = False

    def get(self, request, *args, **kwargs):
        if 'key' in kwargs:
            self.alert = get_object_or_404(SduAlert, key=kwargs['key'])
        elif 'pk' in kwargs and request.user.is_authenticated:
            self.alert = get_object_or_404(SduAlert,
                                           user=self.request.user,
                                           pk=kwargs['pk'])
        else:
            raise Http404
        self.update_alert()
        return super().get(request, *args, **kwargs)

    def update_alert(self):
        if self.alert.can_be_cancelled:
            self.alert.cancel()
            messages.success(self.request, _("Your stock alert has been"
                                             " cancelled"))
        else:
            messages.error(self.request, _("Your stock alert cannot be"
                                           " cancelled"))

    def get_redirect_url(self, **kwargs):
        return self.request.GET.get('next',
                                    self.alert.sdu.get_absolute_url())
