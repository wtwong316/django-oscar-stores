from django.db.models import Q


class PartnerSduFilterMixin:
    def filter_queryset(self, queryset):
        """
        Restrict the queryset to sdus the given user has access to.
        A staff user is allowed to access all Sdus.
        A non-staff user is only allowed access to a sdu if they are in at
        least one stock record's partner user list.
        """
        user = self.request.user
        if user.is_staff:
            return queryset

        return queryset.filter(
            Q(children__stockrecords__partner__users__pk=user.pk) | Q(stockrecords__partner__users__pk=user.pk)
        ).distinct()
