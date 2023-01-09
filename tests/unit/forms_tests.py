from django.test import TestCase
from oscar.core.loading import get_model

from sdfs.dashboard.forms import DashboardSdfSearchForm
from tests.factories import SdfAddressFactory, SdfFactory


class TestDashboardSdfSearchForm(TestCase):

    def test_filters(self):
        f = DashboardSdfSearchForm()
        Sdf = get_model('sdfs', 'Sdf')

        location = '{"type": "Point", "coordinates": [144.917908,-37.815751]}'

        sdf1 = SdfFactory(name='sdf1', location=location)
        sdf2 = SdfFactory(name='sdf2', location=location)

        SdfAddressFactory(
            sdf=sdf1, line1='Great Portland st., London')

        SdfAddressFactory(
            sdf=sdf2, line1='Sturt Street, Melbourne')

        f.cleaned_data = {'address': 'portland st, london'}
        qs = f.apply_filters(Sdf.objects.all())
        self.assertEqual(list(qs), [sdf1])

        f.cleaned_data = {'name': 'sdf2'}
        qs = f.apply_filters(Sdf.objects.all())
        self.assertEqual(list(qs), [sdf2])

        f.cleaned_data = {'name': 'sdf2', 'address': 'london'}
        qs = f.apply_filters(Sdf.objects.all())
        self.assertEqual(list(qs), [])
