from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarConfig


class InquiryConfig(OscarConfig):
    label = 'inquiry'
    name = 'oscar.apps.inquiry'
    verbose_name = _('Inquiry')
