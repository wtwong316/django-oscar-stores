from django.urls import path
from oscar.core.application import OscarDashboardConfig
from oscar.core.loading import get_class


class SdfsDashboardConfig(OscarDashboardConfig):

    name = 'sdfs.dashboard'
    label = 'sdfs_dashboard'

    namespace = 'sdfs-dashboard'

    default_permissions = ['is_staff']

    def ready(self):
        self.sdf_list_view = get_class('sdfs.dashboard.views', 'SdfListView')
        self.sdf_create_view = get_class('sdfs.dashboard.views', 'SdfCreateView')
        self.sdf_update_view = get_class('sdfs.dashboard.views', 'SdfUpdateView')
        self.sdf_delete_view = get_class('sdfs.dashboard.views', 'SdfDeleteView')

        self.sdf_group_list_view = get_class('sdfs.dashboard.views', 'SdfGroupListView')
        self.sdf_group_create_view = get_class('sdfs.dashboard.views', 'SdfGroupCreateView')
        self.sdf_group_update_view = get_class('sdfs.dashboard.views', 'SdfGroupUpdateView')
        self.sdf_group_delete_view = get_class('sdfs.dashboard.views', 'SdfGroupDeleteView')

    def get_urls(self):
        urls = [
            path('', self.sdf_list_view.as_view(), name='sdf-list'),
            path('create/', self.sdf_create_view.as_view(), name='sdf-create'),
            path('update/<int:pk>/', self.sdf_update_view.as_view(), name='sdf-update'),
            path('delete/<int:pk>/', self.sdf_delete_view.as_view(), name='sdf-delete'),
            path('groups/', self.sdf_group_list_view.as_view(), name='sdf-group-list'),
            path('groups/create/', self.sdf_group_create_view.as_view(), name='sdf-group-create'),
            path('groups/update/<int:pk>/', self.sdf_group_update_view.as_view(), name='sdf-group-update'),
            path('groups/delete/<int:pk>/', self.sdf_group_delete_view.as_view(), name='sdf-group-delete'),
        ]
        return self.post_process_urls(urls)
