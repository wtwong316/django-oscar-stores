from oscar.apps.catalogue.reviews.abstract_models import (
    AbstractSduReview, AbstractVote)
from oscar.core.loading import is_model_registered

if not is_model_registered('reviews', 'SduReview'):
    class SduReview(AbstractSduReview):
        pass


if not is_model_registered('reviews', 'Vote'):
    class Vote(AbstractVote):
        pass
