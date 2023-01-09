from django.conf import settings
from django.core.checks import Warning, register
from django.urls import path
from django.utils.translation import gettext_lazy as _
from oscar.core.application import OscarConfig
from oscar.core.loading import get_class


class SdfsConfig(OscarConfig):

    name = 'sdfs'
    verbose_name = _('Sdfs')

    namespace = 'sdfs'

    def ready(self):
        self.list_view = get_class('sdfs.views', 'SdfListView')
        self.detail_view = get_class('sdfs.views', 'SdfDetailView')

    def get_urls(self):
        urls = [
            path('', self.list_view.as_view(), name='index'),
            path('<slug:dummyslug>/<int:pk>/', self.detail_view.as_view(), name='detail'),
        ]
        return self.post_process_urls(urls)


@register()
def settings_check(app_configs, **kwargs):
    errors = []
    if not getattr(settings, 'GOOGLE_MAPS_API_KEY', False):
        errors.append(
            Warning(
                'Missing GOOGLE_MAPS_API_KEY setting',
                hint='The sdfs app should have a Google Maps API key to use Google Maps APIs',
                id='sdfs.E001',
            )
        )
    return errors
