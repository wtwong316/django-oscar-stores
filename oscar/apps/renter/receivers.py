from django.dispatch import receiver

from oscar.apps.catalogue.signals import sdu_viewed
from oscar.core.loading import get_class

RenterHistoryManager = get_class('renter.history', 'RenterHistoryManager')


@receiver(sdu_viewed)
def receive_sdu_view(sender, sdu, user, request, response, **kwargs):
    """
    Receiver to handle viewing single sdu pages

    Requires the request and response objects due to dependence on cookies
    """
    return RenterHistoryManager.update(sdu, request, response)
