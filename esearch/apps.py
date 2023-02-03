from oscar.core.application import OscarConfig
from django.urls import path
from oscar.core.loading import get_model, get_class


class EsearchConfig(OscarConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'esearch'
    verbose_name = 'ESearch'
    namespace = 'esearch'

    def ready(self):
        self.SearchSduDocumentView = get_class('esearch.views', 'SearchSduDocumentView')
        self.SearchSduView = get_class('esearch.views', 'SearchSduView')

    def get_urls(self):
        urls = [
            path('', self.SearchSduDocumentView.as_view({'get': 'list'}), name='search-sdu-document-view'),
            path('sdus/', self.SearchSduView.as_view(), name='search-sdu-view')
        ]
        return self.post_process_urls(urls)
