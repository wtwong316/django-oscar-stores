from django.dispatch import receiver

from oscar.apps.catalogue.signals import product_viewed
from oscar.core.loading import get_class

RenterHistoryManager = get_class('renter.history', 'RenterHistoryManager')


@receiver(product_viewed)
def receive_product_view(sender, product, user, request, response, **kwargs):
    """
    Receiver to handle viewing single product pages

    Requires the request and response objects due to dependence on cookies
    """
    return RenterHistoryManager.update(product, request, response)
