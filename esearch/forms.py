from django import forms


class SearchSduForm(forms.Form):
    min_sdu_size = forms.IntegerField(label='Minimum size in sqft', required=False)
    #max_sdu_size = forms.IntegerField(label='Maximum size in sqft', min_value=0, required=False)
    #household_size = forms.IntegerField(label='Household size', required=False)
    #min_rent = forms.IntegerField(label='Minimum monthly rent', required=False)
    max_rent = forms.IntegerField(label='Maximum monthly rent', required=False)
    has_individual_kitchen = forms.BooleanField(label='Has individual kitchen', required=True)
    has_individual_bath = forms.BooleanField(label='Has individual bath', required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        query = cleaned_data.get('query', None)

        # Adjust the data attribute so that the lat/lng values are empty when
        # the form is rendered again.  This prevents a bug where a search
        # alters the query field but retains the lat/lng from the previous
        # search, giving the wrong results.
        self.data = self.data.copy()
        return cleaned_data
