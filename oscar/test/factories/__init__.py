# coding=utf-8
import datetime
import random
from decimal import Decimal as D

from django.conf import settings
from django.utils import timezone

from oscar.core.loading import get_class, get_model
from oscar.test.factories.address import *  # noqa
from oscar.test.factories.basket import *  # noqa
from oscar.test.factories.catalogue import *  # noqa
from oscar.test.factories.contrib import *  # noqa
from oscar.test.factories.customer import *  # noqa
from oscar.test.factories.models import *  # noqa
from oscar.test.factories.offer import *  # noqa
from oscar.test.factories.order import *  # noqa
from oscar.test.factories.partner import *  # noqa
from oscar.test.factories.payment import *  # noqa
from oscar.test.factories.voucher import *  # noqa
from oscar.test.factories.wishlists import *  # noqa

Basket = get_model('basket', 'Basket')
Free = get_class('shipping.methods', 'Free')
Voucher = get_model('voucher', 'Voucher')
OrderCreator = get_class('order.utils', 'OrderCreator')
OrderTotalCalculator = get_class('checkout.calculators',
                                 'OrderTotalCalculator')
SurchargeApplicator = get_class('checkout.applicator', 'SurchargeApplicator')
Partner = get_model('partner', 'Partner')
StockRecord = get_model('partner', 'StockRecord')
PurchaseInfo = get_class('partner.strategy', 'PurchaseInfo')
Default = get_class('partner.strategy', 'Default')
StockRequired = get_class('partner.availability', 'StockRequired')
FixedPrice = get_class('partner.prices', 'FixedPrice')

Sdu = get_model('catalogue', 'Sdu')
SduClass = get_model('catalogue', 'SduClass')
SduAttribute = get_model('catalogue', 'SduAttribute')
SduAttributeValue = get_model('catalogue', 'SduAttributeValue')
SduImage = get_model('catalogue', 'SduImage')

WeightBand = get_model('shipping', 'WeightBand')
WeightBased = get_model('shipping', 'WeightBased')

Range = get_model('offer', 'Range')
Condition = get_model('offer', 'Condition')
Benefit = get_model('offer', 'Benefit')
ConditionalOffer = get_model('offer', 'ConditionalOffer')


def create_stockrecord(sdu=None, price=None, partner_sku=None,
                       num_in_stock=None, partner_name=None,
                       currency=settings.OSCAR_DEFAULT_CURRENCY,
                       partner_users=None):
    if sdu is None:
        sdu = create_sdu()
    partner, __ = Partner.objects.get_or_create(name=partner_name or '')
    if partner_users:
        for user in partner_users:
            partner.users.add(user)
    if price is None:
        price = D('9.99')
    if partner_sku is None:
        partner_sku = 'sku_%d_%d' % (sdu.id, random.randint(0, 10000))
    return sdu.stockrecords.create(
        partner=partner, partner_sku=partner_sku,
        price_currency=currency,
        price=price, num_in_stock=num_in_stock)


def create_purchase_info(record):
    return PurchaseInfo(
        price=FixedPrice(
            record.price_currency,
            record.price,
            D('0.00')  # Default to no tax
        ),
        availability=StockRequired(
            record.net_stock_level),
        stockrecord=record
    )


def create_sdu(upc=None, title="Dùｍϻϒ title",
                   sdu_class="Dùｍϻϒ item class",
                   partner_name=None, partner_sku=None, price=None,
                   num_in_stock=None, attributes=None,
                   partner_users=None, **kwargs):
    """
    Helper method for creating sdus that are used in tests.
    """
    sdu_class, __ = SduClass._default_manager.get_or_create(
        name=sdu_class)
    sdu = sdu_class.sdus.model(
        sdu_class=sdu_class,
        title=title, upc=upc, **kwargs)
    if kwargs.get('parent') and 'structure' not in kwargs:
        sdu.structure = 'child'
    if attributes:
        for code, value in attributes.items():
            # Ensure sdu attribute exists
            sdu_class.attributes.get_or_create(name=code, code=code)
            setattr(sdu.attr, code, value)
    sdu.save()

    # Shortcut for creating stockrecord
    stockrecord_fields = [
        price, partner_sku, partner_name, num_in_stock, partner_users]
    if any([field is not None for field in stockrecord_fields]):
        create_stockrecord(
            sdu, price=price, num_in_stock=num_in_stock,
            partner_users=partner_users, partner_sku=partner_sku,
            partner_name=partner_name)
    return sdu


def create_sdu_image(sdu=None,
                         original=None,
                         caption='Dummy Caption',
                         display_order=None,
                         ):
    if not sdu:
        sdu = create_sdu()
    if not display_order:
        if not sdu.images.all():
            display_order = 0
        else:
            display_order = max(
                [i.display_order for i in sdu.images.all()]) + 1

    kwargs = {'sdu_id': sdu.id,
              'original': original,
              'display_order': display_order,
              'caption': caption, }

    return SduImage.objects.create(**kwargs)


def create_basket(empty=False):
    basket = Basket.objects.create()
    basket.strategy = Default()
    if not empty:
        sdu = create_sdu()
        create_stockrecord(sdu, num_in_stock=2)
        basket.add_sdu(sdu)
    return basket


def create_order(number=None, basket=None, user=None, shipping_address=None,
                 shipping_method=None, billing_address=None,
                 total=None, **kwargs):
    """
    Helper method for creating an order for testing
    """
    if not basket:
        basket = Basket.objects.create()
        basket.strategy = Default()
        sdu = create_sdu()
        create_stockrecord(sdu, num_in_stock=10, price=D('10.00'))
        basket.add_sdu(sdu)
    if not basket.id:
        basket.save()
    if shipping_method is None:
        shipping_method = Free()
    shipping_charge = shipping_method.calculate(basket)
    surcharges = SurchargeApplicator().get_applicable_surcharges(basket)
    if total is None:
        total = OrderTotalCalculator().calculate(basket, shipping_charge, surcharges)
    kwargs['surcharges'] = surcharges
    order = OrderCreator().place_order(
        order_number=number,
        user=user,
        basket=basket,
        shipping_address=shipping_address,
        shipping_method=shipping_method,
        shipping_charge=shipping_charge,
        billing_address=billing_address,
        total=total,
        **kwargs)
    basket.set_as_submitted()
    return order


def create_offer(name="Dùｍϻϒ offer", offer_type="Site",
                 max_basket_applications=None, range=None, condition=None,
                 benefit=None, priority=0, status=None, start=None, end=None):
    """
    Helper method for creating an offer
    """
    if range is None:
        range, __ = Range.objects.get_or_create(
            name="All sdus räñgë", includes_all_sdus=True)
    if condition is None:
        condition, __ = Condition.objects.get_or_create(
            range=range, type=Condition.COUNT, value=1)
    if benefit is None:
        benefit, __ = Benefit.objects.get_or_create(
            range=range, type=Benefit.PERCENTAGE, value=20)
    if status is None:
        status = ConditionalOffer.OPEN

    # Create start and end date so offer is active
    now = timezone.now()
    if start is None:
        start = now - datetime.timedelta(days=1)
    if end is None:
        end = now + datetime.timedelta(days=30)

    return ConditionalOffer.objects.create(
        name=name,
        start_datetime=start,
        end_datetime=end,
        status=status,
        offer_type=offer_type,
        condition=condition,
        benefit=benefit,
        max_basket_applications=max_basket_applications,
        priority=priority)


def create_voucher(**kwargs):
    """
    Helper method for creating a voucher
    """
    defaults = {
        'name': "Dùｍϻϒ voucher",
        'code': "test",
        'start_datetime': timezone.now(),
        'end_datetime': timezone.now() + datetime.timedelta(days=12)
    }
    defaults.update(kwargs)
    voucher = VoucherFactory(**defaults)
    voucher.offers.add(create_offer(offer_type='Voucher'))
    return voucher


def create_shipping_weight_based(default_weight=D(1)):
    return WeightBased.objects.create(
        default_weight=default_weight
    )


def create_shipping_weight_band(upper_limit, charge, weight_based=None):
    if not weight_based:
        weight_based = create_shipping_weight_based()
    return WeightBand.objects.create(
        method=weight_based,
        upper_limit=upper_limit,
        charge=charge
    )
