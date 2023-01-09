from django.urls import reverse
from oscar.test.testcases import WebTestCase

from tests.factories import SdfAddressFactory, SdfFactory


class TestDashboardSdfSearchForm(WebTestCase):
    is_staff = True
    is_anonymous = False

    def setUp(self):
        super().setUp()

        location = '{"type": "Point", "coordinates": [144.917908,-37.815751]}'
        location = 'POINT(144.917908 -37.815751)'

        self.sdf1 = SdfFactory(name='sdf1', location=location)
        self.sdf2 = SdfFactory(name='sdf2', location=location)

        SdfAddressFactory(
            sdf=self.sdf1, line1='Great Portland st., London')
        SdfAddressFactory(
            sdf=self.sdf2, line1='Sturt Street, Melbourne')

    def test_list_with_search(self):
        resp = self.get(reverse('sdfs-dashboard:sdf-list') + '?address=portland+london')
        self.assertIn('form', resp.context)
        self.assertEqual(resp.context['form'].cleaned_data, {'address': 'portland london',
                                                             'name': ''})
        self.assertEqual(list(resp.context['object_list']), [self.sdf1])
