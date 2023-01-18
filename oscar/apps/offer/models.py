from oscar.apps.offer.abstract_models import (
    AbstractBenefit, AbstractCondition, AbstractConditionalOffer,
    AbstractRange, AbstractRangeSdu, AbstractRangeSduFileUpload)
from oscar.apps.offer.results import (
    SHIPPING_DISCOUNT, ZERO_DISCOUNT, BasketDiscount, PostInquiryAction,
    ShippingDiscount)
from oscar.core.loading import is_model_registered

__all__ = [
    'BasketDiscount', 'ShippingDiscount', 'PostInquiryAction',
    'SHIPPING_DISCOUNT', 'ZERO_DISCOUNT'
]


if not is_model_registered('offer', 'ConditionalOffer'):
    class ConditionalOffer(AbstractConditionalOffer):
        pass

    __all__.append('ConditionalOffer')


if not is_model_registered('offer', 'Benefit'):
    class Benefit(AbstractBenefit):
        pass

    __all__.append('Benefit')


if not is_model_registered('offer', 'Condition'):
    class Condition(AbstractCondition):
        pass

    __all__.append('Condition')


if not is_model_registered('offer', 'Range'):
    class Range(AbstractRange):
        pass

    __all__.append('Range')


if not is_model_registered('offer', 'RangeSdu'):
    class RangeSdu(AbstractRangeSdu):
        pass

    __all__.append('RangeSdu')


if not is_model_registered('offer', 'RangeSduFileUpload'):
    class RangeSduFileUpload(AbstractRangeSduFileUpload):
        pass

    __all__.append('RangeSduFileUpload')


# Import the benefits and the conditions. Required after initializing the
# parent models to allow overriding them

from oscar.apps.offer.benefits import *  # noqa isort:skip
from oscar.apps.offer.conditions import *  # noqa isort:skip

from oscar.apps.offer.benefits import __all__ as benefit_classes  # noqa isort:skip
from oscar.apps.offer.conditions import __all__ as condition_classes  # noqa isort:skip

__all__.extend(benefit_classes)
__all__.extend(condition_classes)
