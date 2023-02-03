from django import forms


class SduEstimateForm(forms.Form):
    size = forms.DecimalField(
        required=True,
        label='Size in sqft'
    )
    household_size = forms.IntegerField(
        required=False,
        label='Household size'
    )
    rent = forms.IntegerField(
        required=False,
        label='Rent'
    )
    has_individual_kitchen = forms.BooleanField(
        required=False,
        label='Has individual kitchen'
    )
    has_individual_bath = forms.BooleanField(
        required=False,
        label='Has individual batch'
    )
    has_exterior_window = forms.BooleanField(
        required=False,
        label='Has exterior window'
    )
    internal_grading = forms.IntegerField(
        required=False,
        label='Internal grading', min_value=1, max_value=5
    )


