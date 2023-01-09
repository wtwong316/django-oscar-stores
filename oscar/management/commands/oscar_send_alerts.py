import logging

from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_class

logger = logging.getLogger(__name__)

AlertsDispatcher = get_class('customer.alerts.utils', 'AlertsDispatcher')


class Command(BaseCommand):
    """
    Check stock records of sdus for availability and send out alerts
    to customers that have registered for an alert.
    """
    help = _("Check for sdus that are back in "
             "stock and send out alerts")

    def handle(self, **options):
        """
        Check all sdus with active sdu alerts for
        availability and send out email alerts when a sdu is
        available to buy.
        """
        AlertsDispatcher().send_alerts()
