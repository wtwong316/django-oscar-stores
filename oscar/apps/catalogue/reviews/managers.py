from django.db import models


class SduReviewQuerySet(models.QuerySet):
    use_for_related_fields = True

    def approved(self):
        return self.filter(status=self.model.APPROVED)
