from django.urls import path
from django.utils.translation import gettext_lazy as _

from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class InquiriesDashboardConfig(OscarDashboardConfig):
    label = 'inquiries_dashboard'
    name = 'oscar.apps.dashboard.inquiries'
    verbose_name = _('Inquiries dashboard')

    default_permissions = ['is_staff', ]
    permissions_map = {
        'inquiry-list': (['is_staff'], ['partner.dashboard_access']),
        'inquiry-stats': (['is_staff'], ['partner.dashboard_access']),
        'inquiry-detail': (['is_staff'], ['partner.dashboard_access']),
        'inquiry-detail-note': (['is_staff'], ['partner.dashboard_access']),
        'inquiry-line-detail': (['is_staff'], ['partner.dashboard_access']),
        'inquiry-shipping-address': (['is_staff'], ['partner.dashboard_access']),
    }

    def ready(self):
        self.inquiry_list_view = get_class('dashboard.inquiries.views', 'InquiryListView')
        self.inquiry_detail_view = get_class('dashboard.inquiries.views', 'InquiryDetailView')
        self.shipping_address_view = get_class('dashboard.inquiries.views',
                                               'ShippingAddressUpdateView')
        self.line_detail_view = get_class('dashboard.inquiries.views', 'LineDetailView')
        self.inquiry_stats_view = get_class('dashboard.inquiries.views', 'InquiryStatsView')

    def get_urls(self):
        urls = [
            path('', self.inquiry_list_view.as_view(), name='inquiry-list'),
            path('statistics/', self.inquiry_stats_view.as_view(), name='inquiry-stats'),
            path('<str:number>/', self.inquiry_detail_view.as_view(), name='inquiry-detail'),
            path('<str:number>/notes/<int:note_id>/', self.inquiry_detail_view.as_view(), name='inquiry-detail-note'),
            path('<str:number>/lines/<int:line_id>/', self.line_detail_view.as_view(), name='inquiry-line-detail'),
            path(
                '<str:number>/shipping-address/', self.shipping_address_view.as_view(), name='inquiry-shipping-address'),
        ]
        return self.post_process_urls(urls)
