import logging

from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.urls import NoReverseMatch, reverse

from oscar.apps.checkout.signals import post_checkout
from oscar.core.loading import get_class, get_model

InquiryCreator = get_class('inquiry.utils', 'InquiryCreator')
InquiryDispatcher = get_class('inquiry.utils', 'InquiryDispatcher')
CheckoutSessionMixin = get_class('checkout.session', 'CheckoutSessionMixin')
BillingAddress = get_model('inquiry', 'BillingAddress')
ShippingAddress = get_model('inquiry', 'ShippingAddress')
InquiryNumberGenerator = get_class('inquiry.utils', 'InquiryNumberGenerator')
PaymentEventType = get_model('inquiry', 'PaymentEventType')
PaymentEvent = get_model('inquiry', 'PaymentEvent')
PaymentEventQuantity = get_model('inquiry', 'PaymentEventQuantity')
UserAddress = get_model('address', 'UserAddress')
Basket = get_model('basket', 'Basket')

# Standard logger for checkout events
logger = logging.getLogger('oscar.checkout')


class InquiryPlacementMixin(CheckoutSessionMixin):
    """
    Mixin which provides functionality for placing inquiries.

    Any view class which needs to place an inquiry should use this mixin.
    """
    # Any payment sources should be added to this list as part of the
    # handle_payment method.  If the inquiry is placed successfully, then
    # they will be persisted. We need to have the inquiry instance before the
    # payment sources can be saved.
    _payment_sources = None

    # Any payment events should be added to this list as part of the
    # handle_payment method.
    _payment_events = None

    view_signal = post_checkout

    # Payment handling methods
    # ------------------------

    def handle_payment(self, inquiry_number, total, **kwargs):
        """
        Handle any payment processing and record payment sources and events.

        This method is designed to be overridden within your project.  The
        default is to do nothing as payment is domain-specific.

        This method is responsible for handling payment and recording the
        payment sources (using the add_payment_source method) and payment
        events (using add_payment_event) so they can be
        linked to the inquiry when it is saved later on.
        """
        pass

    def add_payment_source(self, source):
        """
        Record a payment source for this inquiry
        """
        if self._payment_sources is None:
            self._payment_sources = []
        self._payment_sources.append(source)

    def add_payment_event(self, event_type_name, amount, reference=''):
        """
        Record a payment event for creation once the inquiry is placed
        """
        event_type, __ = PaymentEventType.objects.get_or_create(
            name=event_type_name)
        # We keep a local cache of (unsaved) payment events
        if self._payment_events is None:
            self._payment_events = []
        event = PaymentEvent(
            event_type=event_type, amount=amount,
            reference=reference)
        self._payment_events.append(event)

    # Placing inquiry methods
    # ---------------------

    def generate_inquiry_number(self, basket):
        """
        Return a new inquiry number
        """
        return InquiryNumberGenerator().inquiry_number(basket)

    def handle_inquiry_placement(self, inquiry_number, user, basket,
                               shipping_address, shipping_method,
                               shipping_charge, billing_address, inquiry_total,
                               surcharges=None, **kwargs):
        """
        Write out the inquiry models and return the appropriate HTTP response

        We deliberately pass the basket in here as the one tied to the request
        isn't necessarily the correct one to use in placing the inquiry.  This
        can happen when a basket gets frozen.
        """
        inquiry = self.place_inquiry(
            inquiry_number=inquiry_number, user=user, basket=basket,
            shipping_address=shipping_address, shipping_method=shipping_method,
            shipping_charge=shipping_charge, inquiry_total=inquiry_total,
            billing_address=billing_address, surcharges=surcharges, **kwargs)
        basket.submit()
        return self.handle_successful_inquiry(inquiry)

    def place_inquiry(self, inquiry_number, user, basket, shipping_address,
                    shipping_method, shipping_charge, inquiry_total,
                    billing_address=None, surcharges=None, **kwargs):
        """
        Writes the inquiry out to the DB including the payment models
        """
        # Create saved shipping address instance from passed in unsaved
        # instance
        shipping_address = self.create_shipping_address(user, shipping_address)

        # We pass the kwargs as they often include the billing address form
        # which will be needed to save a billing address.
        billing_address = self.create_billing_address(
            user, billing_address, shipping_address, **kwargs)

        if 'status' not in kwargs:
            status = self.get_initial_inquiry_status(basket)
        else:
            status = kwargs.pop('status')

        if 'request' not in kwargs:
            request = getattr(self, 'request', None)
        else:
            request = kwargs.pop('request')

        inquiry = InquiryCreator().place_inquiry(
            user=user,
            inquiry_number=inquiry_number,
            basket=basket,
            shipping_address=shipping_address,
            shipping_method=shipping_method,
            shipping_charge=shipping_charge,
            total=inquiry_total,
            billing_address=billing_address,
            status=status,
            request=request,
            surcharges=surcharges,
            **kwargs)
        self.save_payment_details(inquiry)
        return inquiry

    def create_shipping_address(self, user, shipping_address):
        """
        Create and return the shipping address for the current inquiry.

        Compared to self.get_shipping_address(), ShippingAddress is saved and
        makes sure that appropriate UserAddress exists.
        """
        # For an inquiry that only contains items that don't require shipping we
        # won't have a shipping address, so we have to check for it.
        if not shipping_address:
            return None
        shipping_address.save()
        if user.is_authenticated:
            self.update_address_book(user, shipping_address)
        return shipping_address

    def update_address_book(self, user, addr):
        """
        Update the user's address book based on the new shipping address
        """
        try:
            user_addr = user.addresses.get(
                hash=addr.generate_hash())
        except ObjectDoesNotExist:
            # Create a new user address
            user_addr = UserAddress(user=user)
            addr.populate_alternative_model(user_addr)
        if isinstance(addr, ShippingAddress):
            user_addr.num_inquiries_as_shipping_address += 1
        if isinstance(addr, BillingAddress):
            user_addr.num_inquiries_as_billing_address += 1
        user_addr.save()

    def create_billing_address(self, user, billing_address=None,
                               shipping_address=None, **kwargs):
        """
        Saves any relevant billing data (e.g. a billing address).
        """
        if not billing_address:
            return None
        billing_address.save()
        if user.is_authenticated:
            self.update_address_book(user, billing_address)
        return billing_address

    def save_payment_details(self, inquiry):
        """
        Saves all payment-related details. This could include a billing
        address, payment sources and any inquiry payment events.
        """
        self.save_payment_events(inquiry)
        self.save_payment_sources(inquiry)

    def save_payment_events(self, inquiry):
        """
        Saves any relevant payment events for this inquiry
        """
        if not self._payment_events:
            return
        for event in self._payment_events:
            event.inquiry = inquiry
            event.save()
            for line in inquiry.lines.all():
                PaymentEventQuantity.objects.create(
                    event=event, line=line, quantity=line.quantity)

    def save_payment_sources(self, inquiry):
        """
        Saves any payment sources used in this inquiry.

        When the payment sources are created, the inquiry model does not exist
        and so they need to have it set before saving.
        """
        if not self._payment_sources:
            return
        for source in self._payment_sources:
            source.inquiry = inquiry
            source.save()

    def get_initial_inquiry_status(self, basket):
        return None

    # Post-inquiry methods
    # ------------------

    def handle_successful_inquiry(self, inquiry):
        """
        Handle the various steps required after an inquiry has been successfully
        placed.

        Override this view if you want to perform custom actions when an
        inquiry is submitted.
        """
        # Send confirmation message (normally an email)
        self.send_inquiry_placed_email(inquiry)

        # Flush all session data
        self.checkout_session.flush()

        # Save inquiry id in session so thank-you page can load it
        self.request.session['checkout_inquiry_id'] = inquiry.id

        response = HttpResponseRedirect(self.get_success_url())
        self.send_signal(self.request, response, inquiry)
        return response

    def send_signal(self, request, response, inquiry):
        self.view_signal.send(
            sender=self, inquiry=inquiry, user=request.user,
            request=request, response=response)

    def get_success_url(self):
        return reverse('checkout:thank-you')

    def send_inquiry_placed_email(self, inquiry):
        extra_context = self.get_message_context(inquiry)
        dispatcher = InquiryDispatcher(logger=logger)
        dispatcher.send_inquiry_placed_email_for_user(inquiry, extra_context)

    def get_message_context(self, inquiry):
        ctx = {
            'user': self.request.user,
            'inquiry': inquiry,
            'lines': inquiry.lines.all(),
            'request': self.request,
        }

        # Attempt to add the inquiry status URL to the email template ctx.
        try:
            if self.request.user.is_authenticated:
                path = reverse('renter:inquiry',
                               kwargs={'inquiry_number': inquiry.number})
            else:
                path = reverse('renter:anon-inquiry',
                               kwargs={'inquiry_number': inquiry.number,
                                       'hash': inquiry.verification_hash()})
        except NoReverseMatch:
            # We don't care that much if we can't resolve the URL
            pass
        else:
            ctx['status_path'] = path

            # status_url is deprecated, see https://github.com/django-oscar/django-oscar/issues/3826
            site = Site.objects.get_current(self.request)
            ctx['status_url'] = 'http://%s%s' % (site.domain, path)
        return ctx

    # Basket helpers
    # --------------

    def get_submitted_basket(self):
        basket_id = self.checkout_session.get_submitted_basket_id()
        return Basket._default_manager.get(pk=basket_id)

    def freeze_basket(self, basket):
        """
        Freeze the basket so it can no longer be modified
        """
        # We freeze the basket to prevent it being modified once the payment
        # process has started.  If your payment fails, then the basket will
        # need to be "unfrozen".  We also store the basket ID in the session
        # so the it can be retrieved by multistage checkout processes.
        basket.freeze()

    def restore_frozen_basket(self):
        """
        Restores a frozen basket as the sole OPEN basket.  Note that this also
        merges in any new products that have been added to a basket that has
        been created while payment.
        """
        try:
            fzn_basket = self.get_submitted_basket()
        except Basket.DoesNotExist:
            # Strange place.  The previous basket stored in the session does
            # not exist.
            pass
        else:
            fzn_basket.thaw()
            if self.request.basket.id != fzn_basket.id:
                fzn_basket.merge(self.request.basket)
                # Use same strategy as current request basket
                fzn_basket.strategy = self.request.basket.strategy
                self.request.basket = fzn_basket
