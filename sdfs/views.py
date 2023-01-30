from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.utils.translation import gettext_lazy as _
from django.views import generic
from oscar.core.loading import get_class, get_model

SdfSearchForm = get_class('sdfs.forms', 'SdfSearchForm')
Sdf = get_model('sdfs', 'sdf')
SdfSdu = get_model('sdfs', 'SdfSdu')

class MapsContextMixin:

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['maps_api_key'] = settings.GOOGLE_MAPS_API_KEY
        return ctx


class SdfListView(MapsContextMixin, generic.ListView):
    model = Sdf
    template_name = 'sdfs/index.html'
    context_object_name = 'sdf_list'
    form_class = SdfSearchForm
    title_template = "%(sdf_type)s %(filter)s"

    def get(self, request, *args, **kwargs):
        if self.is_form_submitted(request):
            self.form = self.form_class(data=request.GET)
        else:
            self.form = self.form_class()
        return super().get(request, *args, **kwargs)

    def is_form_submitted(self, request):
        return 'query' in request.GET

    def get_max_distance(self):
        """ Return max search distance when searching for sdfs """
        return getattr(settings, 'STORES_MAX_SEARCH_DISTANCE', None)

    def get_queryset(self):
        queryset = self.model.objects.filter(is_active=True)
        if not self.form.is_valid():
            return queryset

        data = self.form.cleaned_data

        group = data.get('group', None)
        if group:
            queryset = queryset.filter(group=group)

        latlng = self.form.point

        if latlng:
            queryset = queryset.annotate(distance=Distance('location', latlng))

            # Constrain by distance if set up
            max_distance = self.get_max_distance()
            if max_distance:
                queryset = queryset.filter(distance__lte=max_distance)

            # Order by distance
            queryset = queryset.order_by('distance')

        return queryset

    def get_title(self):
        title_kwargs = {
            'sdf_type': _('Sdfs'),
            'filter': '',
        }
        if self.form.is_valid():
            data = self.form.cleaned_data

            group = data.get('group', None)
            if group:
                title_kwargs['sdf_type'] = _('%(group)s sdfs') % {
                    'group': group.name,
                }

            latlng = self.form.point
            if latlng:
                if data['query']:
                    title_kwargs['filter'] = _('nearest to %(query)s') % {
                        'query': data['query']}
                else:
                    title_kwargs['filter'] = _('nearest to me')

        return _(self.title_template) % title_kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx['form'] = self.form
        #ctx['all_sdfs'] = self.model.objects.select_related('group', 'address').all()
        if hasattr(self.form, 'point') and self.form.point:
            coords = self.form.point.coords
            ctx['latitude'] = coords[1]
            ctx['longitude'] = coords[0]

        ctx['queryset_description'] = self.get_title()

        return ctx


class SdfDetailView(MapsContextMixin, generic.DetailView):
    model = Sdf
    template_name = 'sdfs/detail.html'
    context_object_name = 'sdf'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pk = self.object.id
        all_sdus = SdfSdu.objects.select_related().filter(sdfId_id=pk)
        ctx['all_sdus'] = all_sdus
        return ctx

