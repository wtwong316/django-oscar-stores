from django.contrib.gis.geos.point import Point
from django.test import TestCase

from tests.factories import SdfFactory


class TestALocation(TestCase):

    def test_can_be_set_for_a_sdf(self):
        sdf = SdfFactory(
            name='Test sdf', location=Point(30.3333, 123.323))

        sdf = sdf.__class__.objects.get(id=sdf.id)
        self.assertEqual(sdf.location.x, 30.3333)
        self.assertEqual(sdf.location.y, 123.323)
