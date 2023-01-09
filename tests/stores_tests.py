from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django_webtest import WebTest
from oscar.test.factories import CountryFactory

from sdfs.models import Sdf
from tests.factories import SdfFactory


class TestSdf(TestCase):

    def test_querying_available_pickup_sdfs(self):
        sample_location = '{"type": "Point", "coordinates": [88.39,11.02]}'
        sdf1 = SdfFactory(is_pickup_sdf=True, location=sample_location)
        sdf2 = SdfFactory(is_pickup_sdf=True, location=sample_location)
        SdfFactory(is_pickup_sdf=False, location=sample_location)
        sdf4 = SdfFactory(is_pickup_sdf=True, location=sample_location)

        sdfs = list(Sdf.objects.pickup_sdfs())

        self.assertEqual(len(sdfs), 3)
        self.assertIn(sdf1, sdfs)
        self.assertIn(sdf2, sdfs)
        self.assertIn(sdf4, sdfs)


def repr_opening_hours(sdf):
    r = {}
    for period in sdf.opening_periods.all().order_by('start'):
        if period.weekday not in r:
            r[period.weekday] = ''
        else:
            r[period.weekday] += ', '
        r[period.weekday] += '%s - %s' % (period.start.strftime('%H:%M'),
                                          period.end  .strftime('%H:%M'))
    return r


class SdfsWebTest(WebTest):
    is_staff = False
    is_anonymous = True
    username = 'testuser'
    email = 'testuser@buymore.com'
    password = 'somefancypassword'

    def setUp(self):
        self.user = None
        if not self.is_anonymous:
            self.user = User.objects.create(
                username=self.username,
                email=self.email,
                password=self.password,
                is_staff=self.is_staff
            )

    def get(self, url, **kwargs):
        kwargs.setdefault('user', self.user)
        return self.app.get(url, **kwargs)

    def post(self, url, **kwargs):
        kwargs.setdefault('user', self.user)
        return self.app.post(url, **kwargs)


class TestASignedInUser(SdfsWebTest):
    is_staff = True
    is_anonymous = False

    def setUp(self):
        super().setUp()
        self.country = CountryFactory(
            name="AUSTRALIA",
            printable_name="Australia",
            iso_3166_1_a2='AU',
            iso_3166_1_a3='AUS',
            iso_3166_1_numeric=36,
        )

    def test_can_create_a_new_sdf_without_opening_periods(self):
        url = reverse('sdfs-dashboard:sdf-create')
        page = self.get(url)
        create_form = page.form

        create_form['name'] = 'Sample Sdf'
        create_form['address-0-line1'] = '123 Invisible Street'
        create_form['address-0-line4'] = 'Awesometown'
        create_form['address-0-state'] = 'Victoria'
        create_form['address-0-postcode'] = '3456'
        create_form['address-0-country'] = 'AU'
        create_form['location'] = '{"type": "Point", "coordinates": [30.203332,44.33333] }'

        create_form['description'] = 'A short description of the sdf'
        create_form['is_pickup_sdf'] = False
        create_form['is_active'] = True

        page = create_form.submit()

        self.assertRedirects(page, reverse('sdfs-dashboard:sdf-list'))

        self.assertEqual(Sdf.objects.count(), 1)

        sdf = Sdf.objects.all()[0]
        self.assertEqual(sdf.name, 'Sample Sdf')
        self.assertEqual(sdf.location.x, 30.203332)
        self.assertEqual(sdf.location.y, 44.33333)
        self.assertEqual(
            sdf.description,
            'A short description of the sdf'
        )
        self.assertEqual(sdf.is_pickup_sdf, False)
        self.assertEqual(sdf.is_active, True)

        self.assertEqual(sdf.address.line1, '123 Invisible Street')
        self.assertEqual(sdf.address.line4, 'Awesometown')
        self.assertEqual(sdf.address.state, 'Victoria')
        self.assertEqual(sdf.address.postcode, '3456')
        self.assertEqual(sdf.address.country, self.country)

        self.assertEqual(sdf.opening_periods.count(), 0)

    def test_workinghours_form(self):
        url = reverse('sdfs-dashboard:sdf-create')
        page = self.get(url)
        form = page.form

        form['name'] = 'WorkingHoursTest'
        form['location'] = '{"type": "Point", "coordinates": [88.39,11.02]}'

        form['day-1-open'] = True

        form['day-1-0-start'] = '10'
        form['day-1-0-end'] = '11'

        form['day-1-1-start'] = '12'
        form['day-1-1-end'] = '13'

        form['day-2-open'] = True

        form['day-2-0-start'] = '12'
        form['day-2-0-end'] = '13'

        form['day-3-0-start'] = '12'
        form['day-3-0-end'] = '13'

        resp = form.submit()

        if resp.context and 'form' in resp.context:
            assert False, repr(resp.context['form'].errors)

        sdf = Sdf.objects.get(name='WorkingHoursTest')
        assert sdf.opening_periods.count() == 3

        self.assertEqual(repr_opening_hours(sdf), {
            1: '10:00 - 11:00, 12:00 - 13:00',
            2: '12:00 - 13:00',
        })
