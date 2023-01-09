# -*- coding: utf-8 -*-
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView, DeleteView, FormView, ListView, UpdateView, View)

from oscar.core.loading import get_class, get_classes, get_model
from oscar.core.utils import redirect_to_referrer, safe_referrer

WishList = get_model('wishlists', 'WishList')
Line = get_model('wishlists', 'Line')
Sdu = get_model('catalogue', 'Sdu')
WishListForm = get_class('wishlists.forms', 'WishListForm')
LineFormset, WishListSharedEmailFormset = get_classes(
    'wishlists.formsets', ('LineFormset', 'WishListSharedEmailFormset'))
PageTitleMixin = get_class('customer.mixins', 'PageTitleMixin')


class WishListListView(PageTitleMixin, ListView):
    context_object_name = active_tab = "wishlists"
    template_name = 'oscar/customer/wishlists/wishlists_list.html'
    page_title = _('Wish Lists')

    def get_queryset(self):
        """
        Return a list of all the wishlists for the currently
        authenticated user.
        """
        return self.request.user.wishlists.all()


class WishListDetailView(PageTitleMixin, FormView):
    """
    This view acts as a DetailView for a wish list and allows updating the
    quantities of sdus.

    It is implemented as FormView because it's easier to adapt a FormView to
    display a sdu then adapt a DetailView to handle form validation.
    """
    template_name = 'oscar/customer/wishlists/wishlists_detail.html'
    active_tab = "wishlists"
    form_class = LineFormset

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_wishlist_or_404(kwargs['key'], request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_wishlist_or_404(self, key, user):
        wishlist = get_object_or_404(WishList, key=key)
        if wishlist.is_allowed_to_edit(user):
            return wishlist
        else:
            raise Http404

    def get_page_title(self):
        return self.object.name

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.object
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['wishlist'] = self.object
        other_wishlists = self.request.user.wishlists.exclude(
            pk=self.object.pk)
        ctx['other_wishlists'] = other_wishlists
        return ctx

    def form_valid(self, form):
        for subform in form:
            if subform.cleaned_data['quantity'] <= 0:
                subform.instance.delete()
            else:
                subform.save()
        messages.success(self.request, _('Quantities updated.'))
        return redirect('customer:wishlists-detail', key=self.object.key)


class WishListCreateUpdateViewMixin(PageTitleMixin):
    """
    The wishlist create and update view have the same approach on saving the wislist and shared email
    forms. This mixin handles that in the post view, where it will call process_wishlist_forms
    if both forms are valid. If one of the forms is not valid, the user will be redirected to the original
    view with form errors.
    """
    def process_wishlist_forms(self, wishlist_form, shared_emails_formset):
        wishlist = wishlist_form.save()

        for form in shared_emails_formset:
            # Prevents saving empty or unchanged forms in the formset.
            if not form.has_changed():
                continue

            # Don't commit to DB until we saved the wislist instance.
            wishlist_shared_email = form.save(commit=False)
            wishlist_shared_email.wishlist = wishlist
            wishlist_shared_email.save()

        if wishlist.shared_emails.exists() and wishlist.visibility != WishList.SHARED:
            if wishlist.visibility == WishList.PRIVATE:
                msg = _("The shared accounts won't be able to access your wishlist "
                        "because the visiblity is set to private.")
            elif wishlist.visibility == WishList.PUBLIC:
                msg = _("You have added shared accounts to your wishlist but the visiblity "
                        "is public, this means everyone with a link has access to it.")
            messages.warning(self.request, msg)

        return wishlist

    def post(self, request, *args, **kwargs):
        """
        This post method will handle both the create and update view post request.
        """
        try:
            self.object = self.get_object()
        except AttributeError:
            self.object = None

        form = self.get_form()
        shared_emails_formset = WishListSharedEmailFormset(request.POST, instance=self.object)

        if form.is_valid() and shared_emails_formset.is_valid():
            wishlist = self.process_wishlist_forms(form, shared_emails_formset)
            return self.form_valid(wishlist)

        context = self.get_context_data(form=form, shared_emails_formset=shared_emails_formset)
        return self.render_to_response(context)


class WishListCreateView(WishListCreateUpdateViewMixin, CreateView):
    """
    Create a new wishlist

    If a sdu ID is passed as a kwargs, then this sdu will be added to
    the wishlist.
    """
    model = WishList
    template_name = 'oscar/customer/wishlists/wishlists_form.html'
    active_tab = "wishlists"
    page_title = _('Create a new wish list')
    form_class = WishListForm
    sdu = None

    def dispatch(self, request, *args, **kwargs):
        if 'sdu_pk' in kwargs:
            try:
                self.sdu = Sdu.objects.get(pk=kwargs['sdu_pk'])
            except ObjectDoesNotExist:
                messages.error(
                    request, _("The requested sdu no longer exists"))
                return redirect('wishlists-create')
        return super().dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['sdu'] = self.sdu

        # Invalid post response passes this to the context.
        if "shared_emails_formset" not in kwargs:
            ctx["shared_emails_formset"] = WishListSharedEmailFormset()

        return ctx

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """
        The form argument is actually the wishlist instance because we already saved this in
        the post method below. This is also why we do not call form.save() here.
        """
        wishlist = form
        if self.sdu:
            wishlist.add(self.sdu)
            msg = _("Your wishlist has been created and '%(name)s "
                    "has been added") \
                % {'name': self.sdu.get_title()}
        else:
            msg = _("Your wishlist has been created")
        messages.success(self.request, msg)

        return redirect(form.get_absolute_url())


class WishListCreateWithSduView(View):
    """
    Create a wish list and immediately add a sdu to it
    """

    def post(self, request, *args, **kwargs):
        sdu = get_object_or_404(Sdu, pk=kwargs['sdu_pk'])
        wishlists = request.user.wishlists.all()
        if len(wishlists) == 0:
            wishlist = request.user.wishlists.create()
        else:
            # This shouldn't really happen but we default to using the first
            # wishlist for a user if one already exists when they make this
            # request.
            wishlist = wishlists[0]
        wishlist.add(sdu)
        messages.success(
            request, _("%(title)s has been added to your wishlist") % {
                'title': sdu.get_title()})
        return redirect_to_referrer(request, wishlist.get_absolute_url())


class WishListUpdateView(WishListCreateUpdateViewMixin, UpdateView):
    model = WishList
    template_name = 'oscar/customer/wishlists/wishlists_form.html'
    active_tab = "wishlists"
    form_class = WishListForm
    context_object_name = 'wishlist'

    def get_page_title(self):
        return self.object.name

    def get_object(self, queryset=None):
        return get_object_or_404(WishList, owner=self.request.user,
                                 key=self.kwargs['key'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Invalid post response passes this to the context.
        if "shared_emails_formset" not in kwargs:
            ctx["shared_emails_formset"] = WishListSharedEmailFormset(instance=self.object)

        return ctx

    def get_success_url(self):
        messages.success(
            self.request, _("Your '%s' wishlist has been updated")
            % self.object.name)
        return reverse('customer:wishlists-list')

    def form_valid(self, form):
        return redirect(self.get_success_url())


class WishListDeleteView(PageTitleMixin, DeleteView):
    model = WishList
    template_name = 'oscar/customer/wishlists/wishlists_delete.html'
    active_tab = "wishlists"

    def get_page_title(self):
        return _('Delete %s') % self.object.name

    def get_object(self, queryset=None):
        return get_object_or_404(WishList, owner=self.request.user,
                                 key=self.kwargs['key'])

    def get_success_url(self):
        messages.success(
            self.request, _("Your '%s' wish list has been deleted")
            % self.object.name)
        return reverse('customer:wishlists-list')


class WishListAddSdu(View):
    """
    Adds a sdu to a wish list.

    - If the user doesn't already have a wishlist then it will be created for
      them.
    - If the sdu is already in the wish list, its quantity is increased.
    """

    def dispatch(self, request, *args, **kwargs):
        self.sdu = get_object_or_404(Sdu, pk=kwargs['sdu_pk'])
        self.wishlist = self.get_or_create_wishlist(request, *args, **kwargs)
        return super().dispatch(request)

    def get_or_create_wishlist(self, request, *args, **kwargs):
        if 'key' in kwargs:
            wishlist = get_object_or_404(
                WishList, key=kwargs['key'], owner=request.user)
        else:
            wishlists = request.user.wishlists.all()[:1]
            if not wishlists:
                return request.user.wishlists.create()
            wishlist = wishlists[0]

        if not wishlist.is_allowed_to_edit(request.user):
            raise PermissionDenied
        return wishlist

    def get(self, request, *args, **kwargs):
        # This is nasty as we shouldn't be performing write operations on a GET
        # request.  It's only included as the UI of the sdu detail page
        # allows a wishlist to be selected from a dropdown.
        return self.add_sdu()

    def post(self, request, *args, **kwargs):
        return self.add_sdu()

    def add_sdu(self):
        self.wishlist.add(self.sdu)
        msg = _("'%s' was added to your wish list.") % self.sdu.get_title()
        messages.success(self.request, msg)
        return redirect_to_referrer(
            self.request, self.sdu.get_absolute_url())


class LineMixin(object):
    """
    Handles fetching both a wish list and a sdu
    Views using this mixin must be passed two keyword arguments:

    * key: The key of a wish list
    * line_pk: The primary key of the wish list line

    or

    * sdu_pk: The primary key of the sdu
    """

    def fetch_line(self, user, wishlist_key, line_pk=None, sdu_pk=None):
        if line_pk is not None:
            self.line = get_object_or_404(
                Line,
                pk=line_pk,
                wishlist__owner=user,
                wishlist__key=wishlist_key,
            )
        else:
            try:
                self.line = get_object_or_404(
                    Line,
                    sdu_id=sdu_pk,
                    wishlist__owner=user,
                    wishlist__key=wishlist_key,
                )
            except Line.MultipleObjectsReturned:
                raise Http404
        self.wishlist = self.line.wishlist
        self.sdu = self.line.sdu


class WishListRemoveSdu(LineMixin, PageTitleMixin, DeleteView):
    template_name = 'oscar/customer/wishlists/wishlists_delete_sdu.html'
    active_tab = "wishlists"

    def get_page_title(self):
        return _('Remove %s') % self.object.get_title()

    def get_object(self, queryset=None):
        self.fetch_line(
            self.request.user,
            self.kwargs['key'],
            self.kwargs.get('line_pk'),
            self.kwargs.get('sdu_pk')
        )
        return self.line

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['wishlist'] = self.wishlist
        ctx['sdu'] = self.sdu
        return ctx

    def get_success_url(self):
        msg = _("'%(title)s' was removed from your '%(name)s' wish list") % {
            'title': self.line.get_title(),
            'name': self.wishlist.name}
        messages.success(self.request, msg)

        # We post directly to this view on sdu pages; and should send the
        # user back there if that was the case
        referrer = safe_referrer(self.request, '')
        if (referrer and self.sdu
                and self.sdu.get_absolute_url() in referrer):
            return referrer
        else:
            return reverse(
                'customer:wishlists-detail', kwargs={'key': self.wishlist.key})


class WishListMoveSduToAnotherWishList(LineMixin, View):

    def dispatch(self, request, *args, **kwargs):
        self.fetch_line(request.user, kwargs['key'], line_pk=kwargs['line_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        to_wishlist = get_object_or_404(
            WishList, owner=request.user, key=kwargs['to_key'])

        if to_wishlist.lines.filter(sdu=self.line.sdu).count() > 0:
            msg = _("Wish list '%(name)s' already containing '%(title)s'") % {
                'title': self.sdu.get_title(),
                'name': to_wishlist.name}
            messages.error(self.request, msg)
        else:
            self.line.wishlist = to_wishlist
            self.line.save()

            msg = _("'%(title)s' moved to '%(name)s' wishlist") % {
                'title': self.sdu.get_title(),
                'name': to_wishlist.name}
            messages.success(self.request, msg)

        default_url = reverse(
            'customer:wishlists-detail', kwargs={'key': self.wishlist.key})
        return redirect_to_referrer(self.request, default_url)
