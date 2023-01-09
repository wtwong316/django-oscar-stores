import re

from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_model

Sdu = get_model('catalogue', 'Sdu')
Range = get_model('offer', 'Range')

UPC_SET_REGEX = re.compile(r'[^,\s]+')


class RangeForm(forms.ModelForm):

    class Meta:
        model = Range
        fields = [
            'name', 'description', 'is_public',
            'includes_all_sdus', 'included_categories'
        ]


class RangeSduForm(forms.Form):
    query = forms.CharField(
        max_length=1024, label=_("Sdu SKUs or UPCs"),
        widget=forms.Textarea, required=False,
        help_text=_("You can paste in a selection of SKUs or UPCs"))
    file_upload = forms.FileField(
        label=_("File of SKUs or UPCs"), required=False, max_length=255,
        help_text=_('Either comma-separated, or one identifier per line'))

    def __init__(self, range, *args, **kwargs):
        self.range = range
        super().__init__(*args, **kwargs)

    def clean(self):
        clean_data = super().clean()
        if not clean_data.get('query') and not clean_data.get('file_upload'):
            raise forms.ValidationError(
                _("You must submit either a list of SKU/UPCs or a file"))
        return clean_data

    def clean_query(self):
        raw = self.cleaned_data['query']
        if not raw:
            return raw

        # Check that the search matches some sdus
        ids = set(UPC_SET_REGEX.findall(raw))
        sdus = self.range.all_sdus()
        existing_skus = set(sdus.values_list(
            'stockrecords__partner_sku', flat=True))
        existing_upcs = set(sdus.values_list('upc', flat=True))
        existing_ids = existing_skus.union(existing_upcs)
        new_ids = ids - existing_ids

        if len(new_ids) == 0:
            raise forms.ValidationError(
                _("The sdus with SKUs or UPCs matching %s are already in"
                  " this range") % (', '.join(ids)))

        self.sdus = Sdu._default_manager.filter(
            Q(stockrecords__partner_sku__in=new_ids)
            | Q(upc__in=new_ids))
        if len(self.sdus) == 0:
            raise forms.ValidationError(
                _("No sdus exist with a SKU or UPC matching %s")
                % ", ".join(ids))

        found_skus = set(self.sdus.values_list(
            'stockrecords__partner_sku', flat=True))
        found_upcs = set(self.sdus.values_list('upc', flat=True))
        found_ids = found_skus.union(found_upcs)
        self.missing_skus = new_ids - found_ids
        self.duplicate_skus = existing_ids.intersection(ids)

        return raw

    def get_sdus(self):
        return self.sdus if hasattr(self, 'sdus') else []

    def get_missing_skus(self):
        return self.missing_skus

    def get_duplicate_skus(self):
        return self.duplicate_skus
