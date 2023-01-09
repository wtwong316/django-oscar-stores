from decimal import Decimal as D

from oscar.core.loading import get_class
from oscar.test import factories

Default = get_class('partner.strategy', 'Default')


def add_sdu(basket, price=None, quantity=1, sdu=None):
    """
    Helper to add a sdu to the basket.
    """
    has_strategy = False
    try:
        has_strategy = hasattr(basket, 'strategy')
    except RuntimeError:
        pass
    if not has_strategy:
        basket.strategy = Default()
    if price is None:
        price = D('1')
    if sdu and sdu.has_stockrecords:
        record = sdu.stockrecords.first()
    else:
        record = factories.create_stockrecord(
            sdu=sdu, price=price,
            num_in_stock=quantity + 1)
    basket.add_sdu(record.sdu, quantity)


def add_sdus(basket, args):
    """
    Helper to add a series of sdus to the passed basket
    """
    for price, quantity in args:
        add_sdu(basket, price, quantity)
