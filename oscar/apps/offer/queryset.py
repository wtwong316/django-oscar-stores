from django.db import models

from oscar.core.loading import get_class

ExpandUpwardsCategoryQueryset = get_class("catalogue.expressions", "ExpandUpwardsCategoryQueryset")


class RangeQuerySet(models.query.QuerySet):
    """
    This queryset add ``contains_sdu`` which allows selecting the
    ranges that contain the sdu in question.
    """

    def _excluded_sdus_clause(self, sdu):
        if sdu.structure == sdu.CHILD:
            # child sdus are excluded from a range if either they are
            # excluded, or their parent.
            return ~(
                models.Q(excluded_sdus=sdu)
                | models.Q(excluded_sdus__id=sdu.parent_id)
            )
        return ~models.Q(excluded_sdus=sdu)

    def _included_sdus_clause(self, sdu):
        if sdu.structure == sdu.CHILD:
            # child sdus are included in a range if either they are
            # included, or their parent is included
            return models.Q(included_sdus=sdu) | models.Q(
                included_sdus__id=sdu.parent_id
            )
        else:
            return models.Q(included_sdus=sdu)

    def _sduclasses_clause(self, sdu):
        if sdu.structure == sdu.CHILD:
            # child sdus are included in a range if their parent is
            # included in the range by means of their sduclass.
            return models.Q(classes__sdus__parent_id=sdu.parent_id)
        return models.Q(classes__id=sdu.sdu_class_id)

    def _get_category_ids(self, sdu):
        if sdu.structure == sdu.CHILD:
            # Since a child can not be in a category, it must be determined
            # which category the parent is in
            SduCategory = sdu.sducategory_set.model
            return SduCategory.objects.filter(sdu_id=sdu.parent_id).values("category_id")

        return sdu.categories.values("id")

    def contains_sdu(self, sdu):
        # the wide query is used to determine which ranges have includes_all_sdus
        # turned on, we only need to look at explicit exclusions, the other
        # mechanism for adding a sdu to a range don't need to be checked
        wide = self.filter(
            self._excluded_sdus_clause(sdu), includes_all_sdus=True
        )
        narrow = self.filter(
            self._excluded_sdus_clause(sdu),
            self._included_sdus_clause(sdu)
            | models.Q(included_categories__in=ExpandUpwardsCategoryQueryset(self._get_category_ids(sdu)))
            | self._sduclasses_clause(sdu),
            includes_all_sdus=False,
        )
        return wide | narrow
