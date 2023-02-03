from oscar.core.application import OscarConfig
from oscar.core.loading import get_class
from django.urls import path


class SdfsActionConfig(OscarConfig):

    name = 'sdfs.action'
    label = 'sdfs_action'
    namespace = 'sdfs-action'
    verbose_name = 'Action'

    def ready(self):
        self.sdu_estimator_view = get_class('sdfs.action.views', 'SduEstimatorView')

    def get_urls(self):
        urls = [
            path('estimate/', self.sdu_estimator_view.as_view(), name='sdu-estimator'),
        ]
        return self.post_process_urls(urls)
