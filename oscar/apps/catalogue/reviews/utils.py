from django.conf import settings

from oscar.core.loading import get_model


def get_default_review_status():
    SduReview = get_model('reviews', 'SduReview')

    if settings.OSCAR_MODERATE_REVIEWS:
        return SduReview.FOR_MODERATION

    return SduReview.APPROVED
