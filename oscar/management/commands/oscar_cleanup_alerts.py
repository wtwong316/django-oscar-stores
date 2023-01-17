import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils.timezone import now

from oscar.core.loading import get_model

SduAlert = get_model('renter', 'SduAlert')

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Command to remove all stale unconfirmed alerts
    """
    help = "Check unconfirmed alerts and clean them up"

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            dest='days',
            default=0,
            help='cleanup alerts older then DAYS from now.')
        parser.add_argument(
            '--hours',
            dest='hours',
            default=0,
            help='cleanup alerts older then HOURS from now.')

    def handle(self, *args, **options):
        """
        Generate a threshold date from the input options or 24 hours
        if no options specified. All alerts that have the
        status ``UNCONFIRMED`` and have been created before the
        threshold date will be removed assuming that the emails
        are wrong or the renter changed their mind.
        """
        delta = timedelta(days=int(options['days']),
                          hours=int(options['hours']))
        if not delta:
            delta = timedelta(hours=24)

        threshold_date = now() - delta

        logger.info('Deleting unconfirmed alerts older than %s',
                    threshold_date.strftime("%Y-%m-%d %H:%M"))

        qs = SduAlert.objects.filter(
            status=SduAlert.UNCONFIRMED,
            date_created__lt=threshold_date
        )
        logger.info("Found %d stale alerts to delete", qs.count())
        qs.delete()
