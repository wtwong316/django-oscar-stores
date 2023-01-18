from decimal import Decimal as D

import factory
from django.conf import settings

from oscar.core.loading import get_class, get_model
from oscar.core.utils import slugify
from oscar.test import factories
from oscar.test.factories.utils import tax_add, tax_subtract

InquiryCreator = get_class('inquiry.utils', 'InquiryCreator')

__all__ = [
    'BillingAddressFactory', 'ShippingAddressFactory', 'InquiryDiscountFactory',
    'InquiryFactory', 'InquiryLineFactory', 'ShippingEventTypeFactory',
    'ShippingEventFactory',
]


class BillingAddressFactory(factory.django.DjangoModelFactory):
    country = factory.SubFactory('oscar.test.factories.CountryFactory')

    first_name = 'John'
    last_name = 'Doe'
    line1 = 'Streetname'
    line2 = '1a'
    line4 = 'City'
    postcode = '1000AA'

    class Meta:
        model = get_model('inquiry', 'BillingAddress')


class ShippingAddressFactory(factory.django.DjangoModelFactory):
    country = factory.SubFactory('oscar.test.factories.CountryFactory')

    first_name = 'John'
    last_name = 'Doe'
    line1 = 'Streetname'
    line2 = '1a'
    line4 = 'City'
    postcode = '1000 AA'
    phone_number = '+12125555555'

    class Meta:
        model = get_model('inquiry', 'ShippingAddress')


class InquiryDiscountFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = get_model('inquiry', 'InquiryDiscount')


class InquiryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_model('inquiry', 'Inquiry')

    if hasattr(settings, 'OSCAR_INITIAL_ORDER_STATUS'):
        status = settings.OSCAR_INITIAL_ORDER_STATUS

    site_id = getattr(settings, "SITE_ID", None)
    number = factory.LazyAttribute(lambda o: '%d' % (100000 + o.basket.pk))
    basket = factory.SubFactory(
        'oscar.test.factories.BasketFactory')

    shipping_code = 'delivery'
    shipping_incl_tax = D('4.95')
    shipping_excl_tax = factory.LazyAttribute(
        lambda o: tax_subtract(o.shipping_incl_tax))

    total_incl_tax = factory.LazyAttribute(lambda o: o.basket.total_incl_tax)
    total_excl_tax = factory.LazyAttribute(lambda o: o.basket.total_excl_tax)

    guest_email = factory.LazyAttribute(
        lambda o: (
            '%s.%s@example.com' % (
                o.billing_address.first_name[0],
                o.billing_address.last_name
            )).lower())

    shipping_address = factory.SubFactory(ShippingAddressFactory)
    billing_address = factory.SubFactory(BillingAddressFactory)

    @factory.post_generation
    def create_line_models(obj, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            if not obj.basket.all_lines().exists():
                sdu = factories.SduFactory(stockrecords=None)
                factories.StockRecordFactory(sdu=sdu, price_currency=settings.OSCAR_DEFAULT_CURRENCY)
                obj.basket.add_sdu(sdu)
            for line in obj.basket.all_lines():
                InquiryCreator().create_line_models(obj, line)


class InquiryLineFactory(factory.django.DjangoModelFactory):
    inquiry = factory.SubFactory(InquiryFactory)
    sdu = factory.SubFactory(
        'oscar.test.factories.SduFactory')
    partner_sku = factory.LazyAttribute(lambda l: l.sdu.upc)
    stockrecord = factory.LazyAttribute(
        lambda l: l.sdu.stockrecords.first())
    quantity = 1

    line_price_incl_tax = factory.LazyAttribute(lambda obj: tax_add(obj.stockrecord.price) * obj.quantity)
    line_price_excl_tax = factory.LazyAttribute(lambda obj: obj.stockrecord.price * obj.quantity)

    line_price_before_discounts_incl_tax = (
        factory.SelfAttribute('.line_price_incl_tax'))
    line_price_before_discounts_excl_tax = (
        factory.SelfAttribute('.line_price_excl_tax'))

    unit_price_incl_tax = factory.LazyAttribute(lambda obj: tax_add(obj.stockrecord.price))
    unit_price_excl_tax = factory.LazyAttribute(lambda obj: obj.stockrecord.price)

    class Meta:
        model = get_model('inquiry', 'Line')


class ShippingEventTypeFactory(factory.django.DjangoModelFactory):
    name = 'Test event'
    code = factory.LazyAttribute(lambda o: slugify(o.name).replace('-', '_'))

    class Meta:
        model = get_model('inquiry', 'ShippingEventType')
        django_get_or_create = ('code', )


class ShippingEventFactory(factory.django.DjangoModelFactory):

    inquiry = factory.SubFactory(InquiryFactory)
    event_type = factory.SubFactory(ShippingEventTypeFactory)

    class Meta:
        model = get_model('inquiry', 'ShippingEvent')
