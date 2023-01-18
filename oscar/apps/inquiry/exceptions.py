class InvalidStatus(Exception):
    pass


class InvalidInquiryStatus(InvalidStatus):
    pass


class InvalidLineStatus(InvalidStatus):
    pass


class InvalidShippingEvent(Exception):
    pass


class InvalidPaymentEvent(Exception):
    pass


class UnableToPlaceInquiry(Exception):
    pass
