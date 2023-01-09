from django.dispatch import receiver

from oscar.apps.catalogue.signals import sdu_viewed
from oscar.core.loading import get_class

CustomerHistoryManager = get_class('customer.history', 'CustomerHistoryManager')


@receiver(sdu_viewed)
def receive_sdu_view(sender, sdu, user, request, response, **kwargs):
    """
    Receiver to handle viewing single sdu pages

    Requires the request and response objects due to dependence on cookies
    """
    return CustomerHistoryManager.update(sdu, request, response)
