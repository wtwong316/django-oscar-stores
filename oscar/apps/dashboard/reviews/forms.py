from django import forms
from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_class, get_model

SduReview = get_model('reviews', 'sdureview')
DatePickerInput = get_class('oscar.forms.widgets', 'DatePickerInput')


class DashboardSduReviewForm(forms.ModelForm):
    choices = (
        (SduReview.APPROVED, _('Approved')),
        (SduReview.REJECTED, _('Rejected')),
    )
    status = forms.ChoiceField(choices=choices, label=_("Status"))

    class Meta:
        model = SduReview
        fields = ('title', 'body', 'score', 'status')


class SduReviewSearchForm(forms.Form):
    STATUS_CHOICES = (
        ('', '------------'),
    ) + SduReview.STATUS_CHOICES
    keyword = forms.CharField(required=False, label=_("Keyword"))
    status = forms.ChoiceField(required=False, choices=STATUS_CHOICES,
                               label=_("Status"))
    date_from = forms.DateTimeField(required=False, label=_("Date from"),
                                    widget=DatePickerInput)
    date_to = forms.DateTimeField(required=False, label=_('to'),
                                  widget=DatePickerInput)
    name = forms.CharField(required=False, label=_('Renter name'))

    def get_friendly_status(self):
        raw = int(self.cleaned_data['status'])
        for key, value in self.STATUS_CHOICES:
            if key == raw:
                return value
        return ''
