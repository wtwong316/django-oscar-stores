from django.template import Context, Template
from django.test import TestCase
from oscar.test.factories import ProductFactory

from tests.factories import SdfFactory, SdfStockFactory


class SdfStockTest(TestCase):

    def setUp(self):
        self.product = ProductFactory()
        self.sdf1_location = '{"type": "Point", "coordinates": [87.39,12.02]}'
        self.sdf2_location = '{"type": "Point", "coordinates": [88.39,11.02]}'
        self.sdf1 = SdfFactory(
            is_pickup_sdf=True, location=self.sdf1_location)
        self.sdf2 = SdfFactory(
            is_pickup_sdf=True, location=self.sdf2_location)

        self.sdf_stock1 = SdfStockFactory(
            sdf=self.sdf1, product=self.product)
        self.sdf_stock1 = SdfStockFactory(
            sdf=self.sdf2, product=self.product)

    def test_sdf_stock_loads(self):
        Template(
            '{% load sdf_stock %}'
        ).render(Context())
