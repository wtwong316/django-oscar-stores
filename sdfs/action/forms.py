from django import forms
from sdfs.utils import DISTRICT_CHOICES


class SduEstimateForm(forms.Form):

    district = forms.ChoiceField(label='行政分區', choices=DISTRICT_CHOICES)
    size = forms.DecimalField(required=True, label='面積（平方英尺)', initial=100)
    household_size = forms.IntegerField(required=True, label='住户人数', initial=1, min_value=1, max_value=10)
    rent = forms.IntegerField(required=False, label='每月租金', initial=5000)
    has_individual_kitchen = forms.BooleanField(required=False, label='有獨立廚房', initial=False)
    has_individual_bath = forms.BooleanField(required=False, label='有獨立浴室', initial=True)
    has_exterior_window = forms.BooleanField(required=False, label='有外窗', initial=True)
    internal_grading = forms.IntegerField(required=True, label='内部裝修评分', initial=3, min_value=1, max_value=5)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data
