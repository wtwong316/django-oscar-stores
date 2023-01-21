from decimal import Decimal as D

from django.conf import settings
from django.contrib.sites.models import Site
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from oscar.apps.inquiry.signals import inquiry_placed
from oscar.core.loading import get_class, get_model

from . import exceptions

Inquiry = get_model('inquiry', 'Inquiry')
Line = get_model('inquiry', 'Line')
InquiryDiscount = get_model('inquiry', 'InquiryDiscount')
CommunicationEvent = get_model('inquiry', 'CommunicationEvent')
CommunicationEventType = get_model('communication', 'CommunicationEventType')
Dispatcher = get_class('communication.utils', 'Dispatcher')
Surcharge = get_model('inquiry', 'Surcharge')


class InquiryNumberGenerator(object):
    """
    Simple object for generating inquiry numbers.

    We need this as the inquiry number is often required for payment
    which takes place before the inquiry model has been created.
    """

    def inquiry_number(self, basket):
        """
        Return an inquiry number for a given basket
        """
        return 100000 + basket.id


class InquiryCreator(object):
    """
    Places the order by writing out the various models
    """

    def place_inquiry(self, basket, total,  # noqa (too complex (12))
                    shipping_method, shipping_charge, user=None,
                    shipping_address=None, billing_address=None,
                    inquiry_number=None, status=None, inquiry=None, surcharges=None, **kwargs):
        """
        Placing an inquiry involves creating all the relevant models based on the
        basket and session data.
        """
        if basket.is_empty:
            raise ValueError(_("Empty baskets cannot be submitted"))
        if not inquiry_number:
            generator = InquiryNumberGenerator()
            inquiry_number = generator.inquiry_number(basket)
        if not status and hasattr(settings, 'OSCAR_INITIAL_ORDER_STATUS'):
            status = getattr(settings, 'OSCAR_INITIAL_ORDER_STATUS')

        if Inquiry._default_manager.filter(number=inquiry_number).exists():
            raise ValueError(_("There is already an inquiry with number %s")
                             % inquiry_number)

        with transaction.atomic():

            kwargs['surcharges'] = surcharges
            # Ok - everything seems to be in inquiry, let's place the inquiry
            inquiry = self.create_inquiry_model(
                user, basket, shipping_address, shipping_method, shipping_charge,
                billing_address, total, inquiry_number, status, inquiry, **kwargs)
            for line in basket.all_lines():
                self.create_line_models(inquiry, line)
                self.update_stock_records(line)

            for voucher in basket.vouchers.select_for_update():
                if not voucher.is_active():  # basket ignores inactive vouchers
                    basket.vouchers.remove(voucher)
                else:
                    available_to_user, msg = voucher.is_available_to_user(user=user)
                    if not available_to_user:
                        raise ValueError(msg)

            # Record any discounts associated with this inquiry
            for application in basket.offer_applications:
                # Trigger any deferred benefits from offers and capture the
                # resulting message
                application['message'] \
                    = application['offer'].apply_deferred_benefit(basket, inquiry,
                                                                  application)
                # Record offer application results
                if application['result'].affects_shipping:
                    # Skip zero shipping discounts
                    shipping_discount = shipping_method.discount(basket)
                    if shipping_discount <= D('0.00'):
                        continue
                    # If a shipping offer, we need to grab the actual discount off
                    # the shipping method instance, which should be wrapped in an
                    # OfferDiscount instance.
                    application['discount'] = shipping_discount
                self.create_discount_model(inquiry, application)
                self.record_discount(application)

            for voucher in basket.vouchers.all():
                self.record_voucher_usage(inquiry, voucher, user)

        # Send signal for analytics to pick up
        inquiry_placed.send(sender=self, inquiry=inquiry, user=user)

        return inquiry

    def create_inquiry_model(self, user, basket, shipping_address,
                           shipping_method, shipping_charge, billing_address,
                           total, inquiry_number, status, inquiry=None, surcharges=None, **extra_inquiry_fields):
        """Create an inquiry model."""
        inquiry_data = {'basket': basket,
                      'number': inquiry_number,
                      'currency': total.currency,
                      'total_incl_tax': total.incl_tax,
                      'total_excl_tax': total.excl_tax,
                      'shipping_incl_tax': shipping_charge.incl_tax,
                      'shipping_excl_tax': shipping_charge.excl_tax,
                      'shipping_method': shipping_method.name,
                      'shipping_code': shipping_method.code}
        if shipping_address:
            inquiry_data['shipping_address'] = shipping_address
        if billing_address:
            inquiry_data['billing_address'] = billing_address
        if user and user.is_authenticated:
            inquiry_data['user_id'] = user.id
        if status:
            inquiry_data['status'] = status
        if extra_inquiry_fields:
            inquiry_data.update(extra_inquiry_fields)
        if 'site' not in inquiry_data:
            inquiry_data['site'] = Site._default_manager.get_current(inquiry)
        inquiry = Inquiry(**inquiry_data)
        inquiry.save()
        if surcharges is not None:
            for charge in surcharges:
                Surcharge.objects.create(
                    inquiry=inquiry,
                    name=charge.surcharge.name,
                    code=charge.surcharge.code,
                    excl_tax=charge.price.excl_tax,
                    incl_tax=charge.price.incl_tax
                )
        return inquiry

    def create_line_models(self, inquiry, basket_line, extra_line_fields=None):
        """
        Create the batch line model.

        You can set extra fields by passing a dictionary as the
        extra_line_fields value
        """
        product = basket_line.product
        stockrecord = basket_line.stockrecord
        if not stockrecord:
            raise exceptions.UnableToPlaceInquiry(
                "Basket line #%d has no stockrecord" % basket_line.id)
        partner = stockrecord.partner
        line_data = {
            'inquiry': inquiry,
            # Partner details
            'partner': partner,
            'partner_name': partner.name,
            'partner_sku': stockrecord.partner_sku,
            'stockrecord': stockrecord,
            # Product details
            'product': product,
            'title': product.get_title(),
            'upc': product.upc,
            'quantity': basket_line.quantity,
            # Price details
            'line_price_excl_tax':
            basket_line.line_price_excl_tax_incl_discounts,
            'line_price_incl_tax':
            basket_line.line_price_incl_tax_incl_discounts,
            'line_price_before_discounts_excl_tax':
            basket_line.line_price_excl_tax,
            'line_price_before_discounts_incl_tax':
            basket_line.line_price_incl_tax,
            # Reporting details
            'unit_price_incl_tax': basket_line.unit_price_incl_tax,
            'unit_price_excl_tax': basket_line.unit_price_excl_tax,
        }
        extra_line_fields = extra_line_fields or {}
        if hasattr(settings, 'OSCAR_INITIAL_LINE_STATUS'):
            if not (extra_line_fields and 'status' in extra_line_fields):
                extra_line_fields['status'] = getattr(
                    settings, 'OSCAR_INITIAL_LINE_STATUS')
        if extra_line_fields:
            line_data.update(extra_line_fields)

        inquiry_line = Line._default_manager.create(**line_data)
        self.create_line_price_models(inquiry, inquiry_line, basket_line)
        self.create_line_attributes(inquiry, inquiry_line, basket_line)
        self.create_additional_line_models(inquiry, inquiry_line, basket_line)

        return inquiry_line

    def update_stock_records(self, line):
        """
        Update any relevant stock records for this inquiry line
        """
        #if line.product.get_product_class().track_stock:
        #    line.stockrecord.allocate(line.quantity)
        pass


    def create_additional_line_models(self, inquiry, inquiry_line, basket_line):
        """
        Empty method designed to be overridden.

        Some applications require additional information about lines, this
        method provides a clean place to create additional models that
        relate to a given line.
        """
        pass

    def create_line_price_models(self, inquiry, inquiry_line, basket_line):
        """
        Creates the batch line price models
        """
        breakdown = basket_line.get_price_breakdown()
        for price_incl_tax, price_excl_tax, quantity in breakdown:
            inquiry_line.prices.create(
                inquiry=inquiry,
                quantity=quantity,
                price_incl_tax=price_incl_tax,
                price_excl_tax=price_excl_tax)

    def create_line_attributes(self, inquiry, inquiry_line, basket_line):
        """
        Creates the batch line attributes.
        """
        for attr in basket_line.attributes.all():
            inquiry_line.attributes.create(
                option=attr.option,
                type=attr.option.code,
                value=attr.value)

    def create_discount_model(self, inquiry, discount):

        """
        Create an inquiry discount model for each offer application attached to
        the basket.
        """
        inquiry_discount = InquiryDiscount(
            inquiry=inquiry,
            message=discount['message'] or '',
            offer_id=discount['offer'].id,
            frequency=discount['freq'],
            amount=discount['discount'])
        result = discount['result']
        if result.affects_shipping:
            inquiry_discount.category = InquiryDiscount.SHIPPING
        elif result.affects_post_inquiry:
            inquiry_discount.category = InquiryDiscount.DEFERRED
        voucher = discount.get('voucher', None)
        if voucher:
            inquiry_discount.voucher_id = voucher.id
            inquiry_discount.voucher_code = voucher.code
        inquiry_discount.save()

    def record_discount(self, discount):
        discount['offer'].record_usage(discount)
        if 'voucher' in discount and discount['voucher']:
            discount['voucher'].record_discount(discount)

    def record_voucher_usage(self, inquiry, voucher, user):
        """
        Updates the models that care about this voucher.
        """
        voucher.record_usage(inquiry, user)


class InquiryDispatcher:
    """
    Dispatcher to send concrete inquiry related emails.
    """

    # Event codes
    ORDER_PLACED_EVENT_CODE = 'ORDER_PLACED'

    def __init__(self, logger=None, mail_connection=None):
        self.dispatcher = Dispatcher(logger=logger, mail_connection=mail_connection)

    def dispatch_inquiry_messages(self, inquiry, messages, event_code, attachments=None, **kwargs):
        """
        Dispatch inquiry-related messages to the renter.
        """
        self.dispatcher.logger.info("Inquiry #%s - sending %s messages", inquiry.number, event_code)
        if inquiry.is_anonymous:
            email = kwargs.get('email_address', inquiry.guest_email)
            dispatched_messages = self.dispatcher.dispatch_anonymous_messages(email, messages, attachments)
        else:
            dispatched_messages = self.dispatcher.dispatch_user_messages(inquiry.user, messages, attachments)

        try:
            event_type = CommunicationEventType.objects.get(code=event_code)
        except CommunicationEventType.DoesNotExist:
            event_type = None

        self.create_communication_event(inquiry, event_type, dispatched_messages)

    def create_communication_event(self, inquiry, event_type, dispatched_messages):
        """
        Create inquiry communications event for audit.
        """
        if dispatched_messages and event_type is not None:
            CommunicationEvent._default_manager.create(inquiry=inquiry, event_type=event_type)

    def send_inquiry_placed_email_for_user(self, inquiry, extra_context, attachments=None):
        event_code = self.ORDER_PLACED_EVENT_CODE
        messages = self.dispatcher.get_messages(event_code, extra_context)
        self.dispatch_inquiry_messages(inquiry, messages, event_code, attachments=attachments)
