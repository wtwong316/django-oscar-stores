from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django_tables2 import SingleTableMixin, SingleTableView

from oscar.core.loading import get_class, get_classes, get_model
from oscar.views.generic import ObjectLookupView

(SduForm,
 SduClassSelectForm,
 SduSearchForm,
 SduClassForm,
 CategoryForm,
 StockAlertSearchForm,
 AttributeOptionGroupForm,
 OptionForm) \
    = get_classes('dashboard.catalogue.forms',
                  ('SduForm',
                   'SduClassSelectForm',
                   'SduSearchForm',
                   'SduClassForm',
                   'CategoryForm',
                   'StockAlertSearchForm',
                   'AttributeOptionGroupForm',
                   'OptionForm'))
(StockRecordFormSet,
 SduCategoryFormSet,
 SduImageFormSet,
 SduRecommendationFormSet,
 SduAttributesFormSet,
 AttributeOptionFormSet) \
    = get_classes('dashboard.catalogue.formsets',
                  ('StockRecordFormSet',
                   'SduCategoryFormSet',
                   'SduImageFormSet',
                   'SduRecommendationFormSet',
                   'SduAttributesFormSet',
                   'AttributeOptionFormSet'))
SduTable, CategoryTable, AttributeOptionGroupTable, OptionTable \
    = get_classes('dashboard.catalogue.tables',
                  ('SduTable', 'CategoryTable',
                   'AttributeOptionGroupTable', 'OptionTable'))
(PopUpWindowCreateMixin,
 PopUpWindowUpdateMixin,
 PopUpWindowDeleteMixin) \
    = get_classes('dashboard.views',
                  ('PopUpWindowCreateMixin',
                   'PopUpWindowUpdateMixin',
                   'PopUpWindowDeleteMixin'))
PartnerSduFilterMixin = get_class('dashboard.catalogue.mixins', 'PartnerSduFilterMixin')
Sdu = get_model('catalogue', 'Sdu')
Category = get_model('catalogue', 'Category')
SduImage = get_model('catalogue', 'SduImage')
SduCategory = get_model('catalogue', 'SduCategory')
SduClass = get_model('catalogue', 'SduClass')
StockRecord = get_model('partner', 'StockRecord')
StockAlert = get_model('partner', 'StockAlert')
Partner = get_model('partner', 'Partner')
AttributeOptionGroup = get_model('catalogue', 'AttributeOptionGroup')
Option = get_model('catalogue', 'Option')


class SduListView(PartnerSduFilterMixin, SingleTableView):

    """
    Dashboard view of the sdu list.
    Supports the permission-based dashboard.
    """

    template_name = 'oscar/dashboard/catalogue/sdu_list.html'
    form_class = SduSearchForm
    sdu_class_form_class = SduClassSelectForm
    table_class = SduTable
    context_table_name = 'sdus'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = self.form
        ctx['sdu_class_form'] = self.sdu_class_form_class()
        return ctx

    def get_description(self, form):
        if form.is_valid() and any(form.cleaned_data.values()):
            return _('Sdu search results')
        return _('Sdus')

    def get_table(self, **kwargs):
        if 'recently_edited' in self.request.GET:
            kwargs.update(dict(orderable=False))

        table = super().get_table(**kwargs)
        table.caption = self.get_description(self.form)
        return table

    def get_table_pagination(self, table):
        return dict(per_page=settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE)

    def get_queryset(self):
        """
        Build the queryset for this list
        """
        queryset = Sdu.objects.browsable_dashboard().base_queryset()
        queryset = self.filter_queryset(queryset)
        queryset = self.apply_search(queryset)
        return queryset

    def apply_search(self, queryset):
        """
        Search through the filtered queryset.

        We must make sure that we don't return search results that the user is not allowed
        to see (see filter_queryset).
        """
        self.form = self.form_class(self.request.GET)

        if not self.form.is_valid():
            return queryset

        data = self.form.cleaned_data

        upc = data.get('upc')
        if upc:
            # Filter the queryset by upc
            # For usability reasons, we first look at exact matches and only return
            # them if there are any. Otherwise we return all results
            # that contain the UPC.

            # Look up all matches (child sdus, sdus not allowed to access) ...
            matches_upc = Sdu.objects.filter(Q(upc__iexact=upc) | Q(children__upc__iexact=upc))

            # ... and use that to pick all standalone or parent sdus that the user is
            # allowed to access.
            qs_match = queryset.filter(
                Q(id__in=matches_upc.values('id')) | Q(id__in=matches_upc.values('parent_id')))

            if qs_match.exists():
                # If there's a direct UPC match, return just that.
                queryset = qs_match
            else:
                # No direct UPC match. Let's try the same with an icontains search.
                matches_upc = Sdu.objects.filter(Q(upc__icontains=upc) | Q(children__upc__icontains=upc))
                queryset = queryset.filter(
                    Q(id__in=matches_upc.values('id')) | Q(id__in=matches_upc.values('parent_id')))

        title = data.get('title')
        if title:
            queryset = queryset.filter(Q(title__icontains=title) | Q(children__title__icontains=title))

        return queryset.distinct()


class SduCreateRedirectView(generic.RedirectView):
    permanent = False
    sdu_class_form_class = SduClassSelectForm

    def get_sdu_create_url(self, sdu_class):
        """ Allow site to provide custom URL """
        return reverse('dashboard:catalogue-sdu-create',
                       kwargs={'sdu_class_slug': sdu_class.slug})

    def get_invalid_sdu_class_url(self):
        messages.error(self.request, _("Please choose a sdu type"))
        return reverse('dashboard:catalogue-sdu-list')

    def get_redirect_url(self, **kwargs):
        form = self.sdu_class_form_class(self.request.GET)
        if form.is_valid():
            sdu_class = form.cleaned_data['sdu_class']
            return self.get_sdu_create_url(sdu_class)

        else:
            return self.get_invalid_sdu_class_url()


class SduCreateUpdateView(PartnerSduFilterMixin, generic.UpdateView):
    """
    Dashboard view that is can both create and update sdus of all kinds.
    It can be used in three different ways, each of them with a unique URL
    pattern:
    - When creating a new standalone sdu, this view is called with the
      desired sdu class
    - When editing an existing sdu, this view is called with the sdu's
      primary key. If the sdu is a child sdu, the template considerably
      reduces the available form fields.
    - When creating a new child sdu, this view is called with the parent's
      primary key.

    Supports the permission-based dashboard.
    """

    template_name = 'oscar/dashboard/catalogue/sdu_update.html'
    model = Sdu
    context_object_name = 'sdu'

    form_class = SduForm
    category_formset = SduCategoryFormSet
    image_formset = SduImageFormSet
    recommendations_formset = SduRecommendationFormSet
    stockrecord_formset = StockRecordFormSet

    creating = False
    parent = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.formsets = {'category_formset': self.category_formset,
                         'image_formset': self.image_formset,
                         'recommended_formset': self.recommendations_formset,
                         'stockrecord_formset': self.stockrecord_formset}

    def dispatch(self, request, *args, **kwargs):
        resp = super().dispatch(
            request, *args, **kwargs)
        return self.check_objects_or_redirect() or resp

    def check_objects_or_redirect(self):
        """
        Allows checking the objects fetched by get_object and redirect
        if they don't satisfy our needs.
        Is used to redirect when create a new variant and the specified
        parent sdu can't actually be turned into a parent sdu.
        """
        if self.creating and self.parent is not None:
            is_valid, reason = self.parent.can_be_parent(give_reason=True)
            if not is_valid:
                messages.error(self.request, reason)
                return redirect('dashboard:catalogue-sdu-list')

    def get_queryset(self):
        """
        Filter sdus that the user doesn't have permission to update
        """
        return self.filter_queryset(Sdu.objects.all())

    def get_object(self, queryset=None):
        """
        This parts allows generic.UpdateView to handle creating sdus as
        well. The only distinction between an UpdateView and a CreateView
        is that self.object is None. We emulate this behavior.

        This method is also responsible for setting self.sdu_class and
        self.parent.
        """
        self.creating = 'pk' not in self.kwargs
        if self.creating:
            # Specifying a parent sdu is only done when creating a child
            # sdu.
            parent_pk = self.kwargs.get('parent_pk')
            if parent_pk is None:
                self.parent = None
                # A sdu class needs to be specified when creating a
                # standalone sdu.
                sdu_class_slug = self.kwargs.get('sdu_class_slug')
                self.sdu_class = get_object_or_404(
                    SduClass, slug=sdu_class_slug)
            else:
                self.parent = get_object_or_404(Sdu, pk=parent_pk)
                self.sdu_class = self.parent.sdu_class

            return None  # success
        else:
            sdu = super().get_object(queryset)
            self.sdu_class = sdu.get_sdu_class()
            self.parent = sdu.parent
            return sdu

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['sdu_class'] = self.sdu_class
        ctx['parent'] = self.parent
        ctx['title'] = self.get_page_title()

        for ctx_name, formset_class in self.formsets.items():
            if ctx_name not in ctx:
                ctx[ctx_name] = formset_class(self.sdu_class,
                                              self.request.user,
                                              instance=self.object)
        return ctx

    def get_page_title(self):
        if self.creating:
            if self.parent is None:
                return _('Create new %(sdu_class)s sdu') % {
                    'sdu_class': self.sdu_class.name}
            else:
                return _('Create new variant of %(parent_sdu)s') % {
                    'parent_sdu': self.parent.title}
        else:
            if self.object.title or not self.parent:
                return self.object.title
            else:
                return _('Editing variant of %(parent_sdu)s') % {
                    'parent_sdu': self.parent.title}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['sdu_class'] = self.sdu_class
        kwargs['parent'] = self.parent
        return kwargs

    def process_all_forms(self, form):
        """
        Short-circuits the regular logic to have one place to have our
        logic to check all forms
        """
        # Need to create the sdu here because the inline forms need it
        # can't use commit=False because SduForm does not support it
        if self.creating and form.is_valid():
            self.object = form.save()

        formsets = {}
        for ctx_name, formset_class in self.formsets.items():
            formsets[ctx_name] = formset_class(self.sdu_class,
                                               self.request.user,
                                               self.request.POST,
                                               self.request.FILES,
                                               instance=self.object)

        is_valid = form.is_valid() and all([formset.is_valid()
                                            for formset in formsets.values()])

        cross_form_validation_result = self.clean(form, formsets)
        if is_valid and cross_form_validation_result:
            return self.forms_valid(form, formsets)
        else:
            return self.forms_invalid(form, formsets)

    # form_valid and form_invalid are called depending on the validation result
    # of just the sdu form and redisplay the form respectively return a
    # redirect to the success URL. In both cases we need to check our formsets
    # as well, so both methods do the same. process_all_forms then calls
    # forms_valid or forms_invalid respectively, which do the redisplay or
    # redirect.
    form_valid = form_invalid = process_all_forms

    def clean(self, form, formsets):
        """
        Perform any cross-form/formset validation. If there are errors, attach
        errors to a form or a form field so that they are displayed to the user
        and return False. If everything is valid, return True. This method will
        be called regardless of whether the individual forms are valid.
        """
        return True

    def forms_valid(self, form, formsets):
        """
        Save all changes and display a success url.
        When creating the first child sdu, this method also sets the new
        parent's structure accordingly.
        """
        if self.creating:
            self.handle_adding_child(self.parent)
        else:
            # a just created sdu was already saved in process_all_forms()
            self.object = form.save()

        # Save formsets
        for formset in formsets.values():
            formset.save()

        for idx, image in enumerate(self.object.images.all()):
            image.display_order = idx
            image.save()

        return HttpResponseRedirect(self.get_success_url())

    def handle_adding_child(self, parent):
        """
        When creating the first child sdu, the parent sdu needs
        to be implicitly converted from a standalone sdu to a
        parent sdu.
        """
        # SduForm eagerly sets the future parent's structure to PARENT to
        # pass validation, but it's not persisted in the database. We ensure
        # it's persisted by calling save()
        if parent is not None:
            parent.structure = Sdu.PARENT
            parent.save()

    def forms_invalid(self, form, formsets):
        # delete the temporary sdu again
        if self.creating and self.object and self.object.pk is not None:
            self.object.delete()
            self.object = None

        messages.error(self.request,
                       _("Your submitted data was not valid - please "
                         "correct the errors below"))
        ctx = self.get_context_data(form=form, **formsets)
        return self.render_to_response(ctx)

    def get_url_with_querystring(self, url):
        url_parts = [url]
        if self.request.GET.urlencode():
            url_parts += [self.request.GET.urlencode()]
        return "?".join(url_parts)

    def get_success_url(self):
        """
        Renders a success message and redirects depending on the button:
        - Standard case is pressing "Save"; redirects to the sdu list
        - When "Save and continue" is pressed, we stay on the same page
        - When "Create (another) child sdu" is pressed, it redirects
          to a new sdu creation page
        """
        msg = render_to_string(
            'oscar/dashboard/catalogue/messages/sdu_saved.html',
            {
                'sdu': self.object,
                'creating': self.creating,
                'request': self.request
            })
        messages.success(self.request, msg, extra_tags="safe noicon")

        action = self.request.POST.get('action')
        if action == 'continue':
            url = reverse(
                'dashboard:catalogue-sdu', kwargs={"pk": self.object.id})
        elif action == 'create-another-child' and self.parent:
            url = reverse(
                'dashboard:catalogue-sdu-create-child',
                kwargs={'parent_pk': self.parent.pk})
        elif action == 'create-child':
            url = reverse(
                'dashboard:catalogue-sdu-create-child',
                kwargs={'parent_pk': self.object.pk})
        else:
            url = reverse('dashboard:catalogue-sdu-list')
        return self.get_url_with_querystring(url)


class SduDeleteView(PartnerSduFilterMixin, generic.DeleteView):
    """
    Dashboard view to delete a sdu. Has special logic for deleting the
    last child sdu.
    Supports the permission-based dashboard.
    """
    template_name = 'oscar/dashboard/catalogue/sdu_delete.html'
    model = Sdu
    context_object_name = 'sdu'

    def get_queryset(self):
        """
        Filter sdus that the user doesn't have permission to update
        """
        return self.filter_queryset(Sdu.objects.all())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.object.is_child:
            ctx['title'] = _("Delete sdu variant?")
        else:
            ctx['title'] = _("Delete sdu?")
        return ctx

    def delete(self, request, *args, **kwargs):
        # We override the core delete method and don't call super in order to
        # apply more sophisticated logic around handling child sdus.
        # Calling super makes it difficult to test if the sdu being deleted
        # is the last child.

        self.object = self.get_object()

        # Before performing the delete, record whether this sdu is the last
        # child.
        is_last_child = False
        if self.object.is_child:
            parent = self.object.parent
            is_last_child = parent.children.count() == 1

        # This also deletes any child sdus.
        self.object.delete()

        # If the sdu being deleted is the last child, then pass control
        # to a method than can adjust the parent itself.
        if is_last_child:
            self.handle_deleting_last_child(parent)

        return HttpResponseRedirect(self.get_success_url())

    def handle_deleting_last_child(self, parent):
        # If the last child sdu is deleted, this view defaults to turning
        # the parent sdu into a standalone sdu. While this is
        # appropriate for many scenarios, it is intentionally easily
        # overridable and not automatically done in e.g. a Sdu's delete()
        # method as it is more a UX helper than hard business logic.
        parent.structure = parent.STANDALONE
        parent.save()

    def get_success_url(self):
        """
        When deleting child sdus, this view redirects to editing the
        parent sdu. When deleting any other sdu, it redirects to the
        sdu list view.
        """
        if self.object.is_child:
            msg = _("Deleted sdu variant '%s'") % self.object.get_title()
            messages.success(self.request, msg)
            return reverse(
                'dashboard:catalogue-sdu',
                kwargs={'pk': self.object.parent_id})
        else:
            msg = _("Deleted sdu '%s'") % self.object.title
            messages.success(self.request, msg)
            return reverse('dashboard:catalogue-sdu-list')


class StockAlertListView(generic.ListView):
    template_name = 'oscar/dashboard/catalogue/stockalert_list.html'
    model = StockAlert
    context_object_name = 'alerts'
    paginate_by = settings.OSCAR_STOCK_ALERTS_PER_PAGE

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = self.form
        ctx['description'] = self.description
        return ctx

    def get_queryset(self):
        if 'status' in self.request.GET:
            self.form = StockAlertSearchForm(self.request.GET)
            if self.form.is_valid():
                status = self.form.cleaned_data['status']
                self.description = _('Alerts with status "%s"') % status
                return self.model.objects.filter(status=status)
        else:
            self.description = _('All alerts')
            self.form = StockAlertSearchForm()
        return self.model.objects.all()


class CategoryListView(SingleTableView):
    template_name = 'oscar/dashboard/catalogue/category_list.html'
    table_class = CategoryTable
    context_table_name = 'categories'

    def get_queryset(self):
        return Category.get_root_nodes()

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['child_categories'] = Category.get_root_nodes()
        return ctx


class CategoryDetailListView(SingleTableMixin, generic.DetailView):
    template_name = 'oscar/dashboard/catalogue/category_list.html'
    model = Category
    context_object_name = 'category'
    table_class = CategoryTable
    context_table_name = 'categories'

    def get_table_data(self):
        return self.object.get_children()

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['child_categories'] = self.object.get_children()
        ctx['ancestors'] = self.object.get_ancestors_and_self()
        return ctx


class CategoryListMixin(object):

    def get_success_url(self):
        parent = self.object.get_parent(update=True)
        if parent is None:
            return reverse("dashboard:catalogue-category-list")
        else:
            return reverse("dashboard:catalogue-category-detail-list",
                           args=(parent.pk,))


class CategoryCreateView(CategoryListMixin, generic.CreateView):
    template_name = 'oscar/dashboard/catalogue/category_form.html'
    model = Category
    form_class = CategoryForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = _("Add a new category")
        return ctx

    def get_success_url(self):
        messages.info(self.request, _("Category created successfully"))
        return super().get_success_url()

    def get_initial(self):
        # set child category if set in the URL kwargs
        initial = super().get_initial()
        if 'parent' in self.kwargs:
            initial['_ref_node_id'] = self.kwargs['parent']
        return initial


class CategoryUpdateView(CategoryListMixin, generic.UpdateView):
    template_name = 'oscar/dashboard/catalogue/category_form.html'
    model = Category
    form_class = CategoryForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = _("Update category '%s'") % self.object.name
        return ctx

    def get_success_url(self):
        messages.info(self.request, _("Category updated successfully"))
        action = self.request.POST.get('action')
        if action == 'continue':
            return reverse('dashboard:catalogue-category-update', kwargs={"pk": self.object.id})
        return super().get_success_url()


class CategoryDeleteView(CategoryListMixin, generic.DeleteView):
    template_name = 'oscar/dashboard/catalogue/category_delete.html'
    model = Category

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['parent'] = self.object.get_parent()
        return ctx

    def get_success_url(self):
        messages.info(self.request, _("Category deleted successfully"))
        return super().get_success_url()


class SduLookupView(ObjectLookupView):
    model = Sdu

    def get_queryset(self):
        return self.model.objects.browsable().all()

    def lookup_filter(self, qs, term):
        return qs.filter(Q(title__icontains=term)
                         | Q(parent__title__icontains=term))


class SduClassCreateUpdateView(generic.UpdateView):

    template_name = 'oscar/dashboard/catalogue/sdu_class_form.html'
    model = SduClass
    form_class = SduClassForm
    sdu_attributes_formset = SduAttributesFormSet

    def process_all_forms(self, form):
        """
        This validates both the SduClass form and the
        SduClassAttributes formset at once
        making it possible to display all their errors at once.
        """
        if self.creating and form.is_valid():
            # the object will be needed by the sdu_attributes_formset
            self.object = form.save(commit=False)

        attributes_formset = self.sdu_attributes_formset(
            self.request.POST, self.request.FILES, instance=self.object)

        is_valid = form.is_valid() and attributes_formset.is_valid()

        if is_valid:
            return self.forms_valid(form, attributes_formset)
        else:
            return self.forms_invalid(form, attributes_formset)

    def forms_valid(self, form, attributes_formset):
        form.save()
        attributes_formset.save()

        return HttpResponseRedirect(self.get_success_url())

    def forms_invalid(self, form, attributes_formset):
        messages.error(self.request,
                       _("Your submitted data was not valid - please "
                         "correct the errors below"
                         ))
        ctx = self.get_context_data(form=form,
                                    attributes_formset=attributes_formset)
        return self.render_to_response(ctx)

    # form_valid and form_invalid are called depending on the validation result
    # of just the sdu class form, and return a redirect to the success URL
    # or redisplay the form, respectively. In both cases we need to check our
    # formsets as well, so both methods do the same. process_all_forms then
    # calls forms_valid or forms_invalid respectively, which do the redisplay
    # or redirect.
    form_valid = form_invalid = process_all_forms

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(
            *args, **kwargs)

        if "attributes_formset" not in ctx:
            ctx["attributes_formset"] = self.sdu_attributes_formset(
                instance=self.object)

        ctx["title"] = self.get_title()

        return ctx


class SduClassCreateView(SduClassCreateUpdateView):

    creating = True

    def get_object(self):
        return None

    def get_title(self):
        return _("Add a new sdu type")

    def get_success_url(self):
        messages.info(self.request, _("Sdu type created successfully"))
        return reverse("dashboard:catalogue-class-list")


class SduClassUpdateView(SduClassCreateUpdateView):

    creating = False

    def get_title(self):
        return _("Update sdu type '%s'") % self.object.name

    def get_success_url(self):
        messages.info(self.request, _("Sdu type updated successfully"))
        return reverse("dashboard:catalogue-class-list")

    def get_object(self):
        sdu_class = get_object_or_404(SduClass, pk=self.kwargs['pk'])
        return sdu_class


class SduClassListView(generic.ListView):
    template_name = 'oscar/dashboard/catalogue/sdu_class_list.html'
    context_object_name = 'classes'
    model = SduClass

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['title'] = _("Sdu Types")
        return ctx


class SduClassDeleteView(generic.DeleteView):
    template_name = 'oscar/dashboard/catalogue/sdu_class_delete.html'
    model = SduClass
    form_class = SduClassForm

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['title'] = _("Delete sdu type '%s'") % self.object.name
        sdu_count = self.object.sdus.count()

        if sdu_count > 0:
            ctx['disallow'] = True
            ctx['title'] = _("Unable to delete '%s'") % self.object.name
            messages.error(self.request,
                           _("%i sdus are still assigned to this type") %
                           sdu_count)
        return ctx

    def get_success_url(self):
        messages.info(self.request, _("Sdu type deleted successfully"))
        return reverse("dashboard:catalogue-class-list")


class AttributeOptionGroupCreateUpdateView(generic.UpdateView):

    template_name = 'oscar/dashboard/catalogue/attribute_option_group_form.html'
    model = AttributeOptionGroup
    form_class = AttributeOptionGroupForm
    attribute_option_formset = AttributeOptionFormSet

    def process_all_forms(self, form):
        """
        This validates both the AttributeOptionGroup form and the
        AttributeOptions formset at once making it possible to display all their
        errors at once.
        """
        if self.creating and form.is_valid():
            # the object will be needed by the attribute_option_formset
            self.object = form.save(commit=False)

        attribute_option_formset = self.attribute_option_formset(
            self.request.POST, self.request.FILES, instance=self.object)

        is_valid = form.is_valid() and attribute_option_formset.is_valid()

        if is_valid:
            return self.forms_valid(form, attribute_option_formset)
        else:
            return self.forms_invalid(form, attribute_option_formset)

    def forms_valid(self, form, attribute_option_formset):
        form.save()
        attribute_option_formset.save()
        if self.is_popup:
            return self.popup_response(form.instance)
        else:
            return HttpResponseRedirect(self.get_success_url())

    def forms_invalid(self, form, attribute_option_formset):
        messages.error(self.request,
                       _("Your submitted data was not valid - please "
                         "correct the errors below"
                         ))
        ctx = self.get_context_data(form=form,
                                    attribute_option_formset=attribute_option_formset)
        return self.render_to_response(ctx)

    # form_valid and form_invalid are called depending on the validation result
    # of just the attribute option group form, and return a redirect to the
    # success URL or redisplay the form, respectively. In both cases we need to
    # check our formsets as well, so both methods do the same.
    # process_all_forms then calls forms_valid or forms_invalid respectively,
    # which do the redisplay or redirect.
    form_valid = form_invalid = process_all_forms

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault("attribute_option_formset", self.attribute_option_formset(instance=self.object))
        ctx["title"] = self.get_title()
        return ctx

    def get_url_with_querystring(self, url):
        url_parts = [url]
        if self.request.GET.urlencode():
            url_parts += [self.request.GET.urlencode()]
        return "?".join(url_parts)


class AttributeOptionGroupCreateView(PopUpWindowCreateMixin, AttributeOptionGroupCreateUpdateView):

    creating = True

    def get_object(self):
        return None

    def get_title(self):
        return _("Add a new Attribute Option Group")

    def get_success_url(self):
        self.add_success_message(_("Attribute Option Group created successfully"))
        url = reverse("dashboard:catalogue-attribute-option-group-list")
        return self.get_url_with_querystring(url)


class AttributeOptionGroupUpdateView(PopUpWindowUpdateMixin, AttributeOptionGroupCreateUpdateView):

    creating = False

    def get_object(self):
        attribute_option_group = get_object_or_404(AttributeOptionGroup, pk=self.kwargs['pk'])
        return attribute_option_group

    def get_title(self):
        return _("Update Attribute Option Group '%s'") % self.object.name

    def get_success_url(self):
        self.add_success_message(_("Attribute Option Group updated successfully"))
        url = reverse("dashboard:catalogue-attribute-option-group-list")
        return self.get_url_with_querystring(url)


class AttributeOptionGroupListView(SingleTableView):

    template_name = 'oscar/dashboard/catalogue/attribute_option_group_list.html'
    model = AttributeOptionGroup
    table_class = AttributeOptionGroupTable
    context_table_name = 'attribute_option_groups'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['querystring'] = self.request.GET.urlencode()
        return ctx


class AttributeOptionGroupDeleteView(PopUpWindowDeleteMixin, generic.DeleteView):

    template_name = 'oscar/dashboard/catalogue/attribute_option_group_delete.html'
    model = AttributeOptionGroup
    form_class = AttributeOptionGroupForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx['title'] = _("Delete Attribute Option Group '%s'") % self.object.name

        sdu_attribute_count = self.object.sdu_attributes.count()
        if sdu_attribute_count > 0:
            ctx['disallow'] = True
            ctx['title'] = _("Unable to delete '%s'") % self.object.name
            messages.error(self.request,
                           _("%i sdu attributes are still assigned to this attribute option group") %
                           sdu_attribute_count)

        ctx['http_get_params'] = self.request.GET

        return ctx

    def get_url_with_querystring(self, url):
        url_parts = [url]
        http_post_params = self.request.POST.copy()
        try:
            del http_post_params['csrfmiddlewaretoken']
        except KeyError:
            pass
        if http_post_params.urlencode():
            url_parts += [http_post_params.urlencode()]
        return "?".join(url_parts)

    def get_success_url(self):
        self.add_success_message(_("Attribute Option Group deleted successfully"))
        url = reverse("dashboard:catalogue-attribute-option-group-list")
        return self.get_url_with_querystring(url)


class OptionListView(SingleTableView):

    template_name = 'oscar/dashboard/catalogue/option_list.html'
    model = Option
    table_class = OptionTable
    context_table_name = 'options'


class OptionCreateUpdateView(generic.UpdateView):

    template_name = 'oscar/dashboard/catalogue/option_form.html'
    model = Option
    form_class = OptionForm

    def form_valid(self, form):
        self.object = form.save()
        if self.is_popup:
            return self.popup_response(form.instance)
        else:
            return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = self.get_title()
        return ctx

    def form_invalid(self, form):
        messages.error(
            self.request,
            _("Your submitted data was not valid - please correct the errors below")
        )
        return super().form_invalid(form)


class OptionCreateView(PopUpWindowCreateMixin, OptionCreateUpdateView):

    creating = True

    def get_object(self):
        return None

    def get_title(self):
        return _("Add a new Option")

    def get_success_url(self):
        self.add_success_message(_("Option created successfully"))
        return reverse("dashboard:catalogue-option-list")


class OptionUpdateView(PopUpWindowUpdateMixin, OptionCreateUpdateView):

    creating = False

    def get_object(self):
        attribute_option_group = get_object_or_404(Option, pk=self.kwargs['pk'])
        return attribute_option_group

    def get_title(self):
        return _("Update Option '%s'") % self.object.name

    def get_success_url(self):
        self.add_success_message(_("Option updated successfully"))
        return reverse("dashboard:catalogue-option-list")


class OptionDeleteView(PopUpWindowDeleteMixin, generic.DeleteView):

    template_name = 'oscar/dashboard/catalogue/option_delete.html'
    model = Option

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx['title'] = _("Delete Option '%s'") % self.object.name

        sdus = self.object.sdu_set.count()
        sdu_classes = self.object.sdu_class_set.count()
        if any([sdus, sdu_classes]):
            ctx['disallow'] = True
            ctx['title'] = _("Unable to delete '%s'") % self.object.name
            if sdus:
                messages.error(
                    self.request,
                    _("%i sdus are still assigned to this option") % sdus
                )
            if sdu_classes:
                messages.error(
                    self.request,
                    _("%i sdu classes are still assigned to this option") % sdu_classes
                )

        return ctx

    def get_success_url(self):
        self.add_success_message(_("Option deleted successfully"))
        return reverse("dashboard:catalogue-option-list")
