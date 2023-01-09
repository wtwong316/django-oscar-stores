from django.contrib.gis.db.models import Manager


class SdfManager(Manager):

    def pickup_sdfs(self):
        return self.get_queryset().filter(is_pickup_sdf=True, is_active=True)
