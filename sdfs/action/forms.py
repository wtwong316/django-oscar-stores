from django import forms


class SduEstimateForm(forms.Form):

    DISTRICT_CHOICES = (
        ("1", "港島中西區"),
        ("2", "港島東區"),
        ("3", "港島南區"),
        ("4", "港島灣仔區"),
        ("5", "九龍九龍城區"),
        ("6", "九龍觀塘區"),
        ("7", "九龍深水埗區"),
        ("8", "九龍黃大仙區"),
        ("9", "九龍油尖旺區"),
        ("10", "新界離島區"),
        ("11", "新界葵青區"),
        ("12", "新界北區"),
        ("13", "新界西貢區"),
        ("14", "新界沙田區"),
        ("15", "新界大埔區"),
        ("16", "新界荃灣區"),
        ("17", "新界屯門區"),
        ("18", "新界元朗區")
    )
    district = forms.ChoiceField(label='行政分區', choices=DISTRICT_CHOICES)

    size = forms.DecimalField(required=True, label='面積（平方英尺)', initial=100)
    household_size = forms.IntegerField(required=True, label='住户人数', initial=1, min_value=1, max_value=10)
    rent = forms.IntegerField(required=True, label='每月租金', initial=5000)
    has_individual_kitchen = forms.BooleanField(required=False, label='有獨立廚房', initial=False)
    has_individual_bath = forms.BooleanField(required=False, label='有獨立浴室', initial=True)
    has_exterior_window = forms.BooleanField(required=False, label='有外窗', initial=True)
    internal_grading = forms.IntegerField(required=True, label='内部裝修评分', initial=3, min_value=1, max_value=5)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data
