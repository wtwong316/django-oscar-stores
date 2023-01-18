from oscar.apps.address.abstract_models import (
    AbstractBillingAddress, AbstractShippingAddress)
from oscar.apps.inquiry.abstract_models import *  # noqa
from oscar.core.loading import is_model_registered

__all__ = ['PaymentEventQuantity', 'ShippingEventQuantity']


if not is_model_registered('inquiry', 'Inquiry'):
    class Inquiry(AbstractInquiry):
        pass

    __all__.append('Inquiry')


if not is_model_registered('inquiry', 'InquiryNote'):
    class InquiryNote(AbstractInquiryNote):
        pass

    __all__.append('InquiryNote')


if not is_model_registered('inquiry', 'InquiryStatusChange'):
    class InquiryStatusChange(AbstractInquiryStatusChange):
        pass

    __all__.append('InquiryStatusChange')


if not is_model_registered('inquiry', 'CommunicationEvent'):
    class CommunicationEvent(AbstractCommunicationEvent):
        pass

    __all__.append('CommunicationEvent')


if not is_model_registered('inquiry', 'ShippingAddress'):
    class ShippingAddress(AbstractShippingAddress):
        pass

    __all__.append('ShippingAddress')


if not is_model_registered('request', 'BillingAddress'):
    class BillingAddress(AbstractBillingAddress):
        pass

    __all__.append('BillingAddress')


if not is_model_registered('inquiry', 'Line'):
    class Line(AbstractLine):
        pass

    __all__.append('Line')


if not is_model_registered('inquiry', 'LinePrice'):
    class LinePrice(AbstractLinePrice):
        pass

    __all__.append('LinePrice')


if not is_model_registered('inquiry', 'LineAttribute'):
    class LineAttribute(AbstractLineAttribute):
        pass

    __all__.append('LineAttribute')


if not is_model_registered('inquiry', 'ShippingEvent'):
    class ShippingEvent(AbstractShippingEvent):
        pass

    __all__.append('ShippingEvent')


if not is_model_registered('inquiry', 'ShippingEventType'):
    class ShippingEventType(AbstractShippingEventType):
        pass

    __all__.append('ShippingEventType')


if not is_model_registered('inquiry', 'PaymentEvent'):
    class PaymentEvent(AbstractPaymentEvent):
        pass

    __all__.append('PaymentEvent')


if not is_model_registered('inquiry', 'PaymentEventType'):
    class PaymentEventType(AbstractPaymentEventType):
        pass

    __all__.append('PaymentEventType')


if not is_model_registered('inquiry', 'InquiryDiscount'):
    class InquiryDiscount(AbstractInquiryDiscount):
        pass

    __all__.append('InquiryDiscount')

if not is_model_registered('inquiry', 'Surcharge'):
    class Surcharge(AbstractSurcharge):
        pass

    __all__.append('Surcharge')
