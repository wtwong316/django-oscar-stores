from django import forms
from django.contrib.gis.geos import GEOSGeometry
from django.utils.translation import gettext as _
from oscar.core.loading import get_class, get_model

from sdfs.utils import get_geodetic_srid

geocode = get_class('sdfs.services', 'geocode')
SdfGroup = get_model('sdfs', 'SdfGroup')


class SdfSearchForm(forms.Form):
    latitude = forms.CharField(widget=forms.HiddenInput, required=False)
    longitude = forms.CharField(widget=forms.HiddenInput, required=False)
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': _("輸入地址..."),
                'class': 'search-query',
            }))
    group = forms.ModelChoiceField(
        required=False,
        queryset=SdfGroup.objects.none(),
        widget=forms.Select(attrs={'data-behaviours': 'filter-group'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group'].queryset = SdfGroup.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        self.point = self.geocoordinates(cleaned_data)

        query = cleaned_data.get('query', None)
        if query and not self.point:
            raise forms.ValidationError(_(
                "No location could be found for your search"))

        # Adjust the data attribute so that the lat/lng values are empty when
        # the form is rendered again.  This prevents a bug where a search
        # alters the query field but retains the lat/lng from the previous
        # search, giving the wrong results.
        self.data = self.data.copy()
        self.data['latitude'] = ''
        self.data['longitude'] = ''

        return cleaned_data

    def geocoordinates(self, data):
        latitude = data.get('latitude', None)
        longitude = data.get('longitude', None)
        if latitude and longitude:
            return GEOSGeometry('POINT(%s %s)' % (longitude, latitude), get_geodetic_srid())

        query = data.get('query', None)
        if query is not None:
            try:
                return geocode.GeoCodeService().geocode(query)
            except geocode.ServiceError:
                return None
