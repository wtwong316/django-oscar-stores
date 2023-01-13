# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from oscar.core.loading import get_model

Sdu = get_model('catalogue', 'Sdu')


class Command(BaseCommand):
    help = """Update the denormalised reviews average on all Sdu instances.
              Should only be necessary when changing to e.g. a weight-based
              rating."""

    def handle(self, *args, **options):
        # Iterate over all Sdus (not just ones with reviews)
        sdus = Sdu.objects.all()
        for sdu in sdus:
            sdu.update_rating()
        self.stdout.write(
            'Successfully updated %s sdus\n' % sdus.count())
