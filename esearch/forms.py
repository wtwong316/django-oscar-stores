from django import forms


class SearchSduForm(forms.Form):
    # iterable

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
    building = forms.CharField(label='大廈名稱', required=False)
    street = forms.CharField(label='街道', required=False)
    min_sdu_size = forms.IntegerField(label='最小面積（平方英尺)', required=False)
    max_rent = forms.IntegerField(label='每月最高租金', required=False)
    has_individual_kitchen = forms.BooleanField(label='有獨立廚房', initial=False, required=False)
    has_individual_bath = forms.BooleanField(label='有獨立浴室', initial=True, required=False)
    has_exterior_window = forms.BooleanField(label='有外窗', initial=True, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        # Adjust the data attribute so that the lat/lng values are empty when
        # the form is rendered again.  This prevents a bug where a search
        # alters the query field but retains the lat/lng from the previous
        # search, giving the wrong results.
        self.data = self.data.copy()
        return cleaned_data
