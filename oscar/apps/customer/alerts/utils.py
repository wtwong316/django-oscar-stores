import logging

from django.db.models import Max
from django.template import loader

from oscar.core.loading import get_class, get_model

SduAlert = get_model('customer', 'SduAlert')
Sdu = get_model('catalogue', 'Sdu')
Dispatcher = get_class('communication.utils', 'Dispatcher')
Selector = get_class('partner.strategy', 'Selector')

alerts_logger = logging.getLogger('oscar.alerts')


class AlertsDispatcher:
    """
    Dispatcher to send concrete sdu alerts related emails
    and notifications.
    """

    # Event codes
    PRODUCT_ALERT_EVENT_CODE = 'PRODUCT_ALERT'
    PRODUCT_ALERT_CONFIRMATION_EVENT_CODE = 'PRODUCT_ALERT_CONFIRMATION'

    def __init__(self, logger=None, mail_connection=None):
        self.dispatcher = Dispatcher(
            logger=logger or alerts_logger,
            mail_connection=mail_connection,
        )

    def get_queryset(self):
        return Sdu.objects.browsable().filter(sdualert__status=SduAlert.ACTIVE).distinct()

    def send_alerts(self):
        """
        Check all sdus with active sdu alerts for
        availability and send out email alerts when a sdu is
        available to buy.
        """
        sdus = self.get_queryset()
        self.dispatcher.logger.info("Found %d sdus with active alerts", sdus.count())
        for sdu in sdus:
            self.send_sdu_alert_email_for_user(sdu)

    def send_sdu_alert_email_for_user(self, sdu):  # noqa: C901 too complex
        """
        Check for notifications for this sdu and send email to users
        if the sdu is back in stock. Add a little 'hurry' note if the
        amount of in-stock items is less then the number of notifications.
        """
        stockrecords = sdu.stockrecords.all()
        num_stockrecords = len(stockrecords)
        if not num_stockrecords:
            return

        self.dispatcher.logger.info("Sending alerts for '%s'", sdu)
        alerts = SduAlert.objects.filter(
            sdu_id__in=(sdu.id, sdu.parent_id),
            status=SduAlert.ACTIVE,
        )

        # Determine 'hurry mode'
        if num_stockrecords == 1:
            num_in_stock = stockrecords[0].num_in_stock
        else:
            result = stockrecords.aggregate(max_in_stock=Max('num_in_stock'))
            num_in_stock = result['max_in_stock']

        # 'hurry_mode' is false if 'num_in_stock' is None
        hurry_mode = num_in_stock is not None and alerts.count() > num_in_stock

        messages_to_send = []
        user_messages_to_send = []
        num_notifications = 0
        selector = Selector()
        for alert in alerts:
            # Check if the sdu is available to this user
            strategy = selector.strategy(user=alert.user)
            data = strategy.fetch_for_sdu(sdu)
            if not data.availability.is_available_to_buy:
                continue

            extra_context = {
                'alert': alert,
                'hurry': hurry_mode,
            }
            if alert.user:
                # Send a site notification
                num_notifications += 1
                self.notify_user_about_sdu_alert(alert.user, extra_context)

            messages = self.dispatcher.get_messages(self.PRODUCT_ALERT_EVENT_CODE, extra_context)

            if messages and messages['body']:
                if alert.user:
                    user_messages_to_send.append((alert.user, messages))
                else:
                    messages_to_send.append((alert.get_email_address(), messages))
            alert.close()

        if messages_to_send or user_messages_to_send:
            for message in messages_to_send:
                self.dispatcher.dispatch_direct_messages(*message)
            for message in user_messages_to_send:
                self.dispatcher.dispatch_user_messages(*message)

        self.dispatcher.logger.info(
            "Sent %d notifications and %d messages",
            num_notifications, len(messages_to_send) + len(user_messages_to_send)
        )

    def send_sdu_alert_confirmation_email_for_user(self, alert, extra_context=None):
        """
        Send an alert confirmation email.
        """
        if extra_context is None:
            extra_context = {'alert': alert}
        messages = self.dispatcher.get_messages(self.PRODUCT_ALERT_CONFIRMATION_EVENT_CODE, extra_context)
        self.dispatcher.dispatch_direct_messages(alert.email, messages)

    def notify_user_about_sdu_alert(self, user, context):
        subj_tpl = loader.get_template('oscar/customer/alerts/message_subject.html')
        message_tpl = loader.get_template('oscar/customer/alerts/message.html')
        self.dispatcher.notify_user(
            user,
            subj_tpl.render(context).strip(),
            body=message_tpl.render(context).strip()
        )
