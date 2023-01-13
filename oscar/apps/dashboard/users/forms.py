from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from oscar.core.compat import get_user_model
from oscar.core.loading import get_model

User = get_user_model()
SduAlert = get_model('renter', 'SduAlert')


class UserSearchForm(forms.Form):
    email = forms.CharField(required=False, label=_("Email"))
    name = forms.CharField(
        required=False, label=pgettext_lazy("User's name", "Name"))


class SduAlertUpdateForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        alert = kwargs['instance']
        if alert.user:
            # Remove 'unconfirmed' from list of available choices when editing
            # an alert for a real user
            choices = self.fields['status'].choices
            del choices[0]
            self.fields['status'].choices = choices

    class Meta:
        model = SduAlert
        fields = [
            'status',
        ]


class SduAlertSearchForm(forms.Form):
    STATUS_CHOICES = (
        ('', '------------'),
    ) + SduAlert.STATUS_CHOICES

    status = forms.ChoiceField(required=False, choices=STATUS_CHOICES,
                               label=_('Status'))
    name = forms.CharField(required=False, label=_('Name'))
    email = forms.EmailField(required=False, label=_('Email'))
