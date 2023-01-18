import logging

from django.db import IntegrityError
from django.db.models import F
from django.dispatch import receiver

from oscar.apps.basket.signals import basket_addition
from oscar.apps.catalogue.signals import sdu_viewed
from oscar.apps.inquiry.signals import inquiry_placed
from oscar.apps.search.signals import user_search
from oscar.core.loading import get_model

SduRecord = get_model('analytics', 'SduRecord')
UserSduView = get_model('analytics', 'UserSduView')
UserRecord = get_model('analytics', 'UserRecord')
UserSearch = get_model('analytics', 'UserSearch')

# Helpers

logger = logging.getLogger('oscar.analytics')


def _update_counter(model, field_name, filter_kwargs, increment=1):
    """
    Efficiently updates a counter field by a given increment. Uses Django's
    update() call to fetch and update in one query.

    TODO: This has a race condition, we should use UPSERT here

    :param model: The model class of the recording model
    :param field_name: The name of the field to update
    :param filter_kwargs: Parameters to the ORM's filter() function to get the
                          correct instance
    """
    try:
        record = model.objects.filter(**filter_kwargs)
        affected = record.update(**{field_name: F(field_name) + increment})
        if not affected:
            filter_kwargs[field_name] = increment
            model.objects.create(**filter_kwargs)
    except IntegrityError:      # pragma: no cover
        # get_or_create has a race condition (we should use upsert in supported)
        # databases. For now just ignore these errors
        logger.error(
            "IntegrityError when updating analytics counter for %s", model)


def _record_sdus_in_inquiry(inquiry):
    # surely there's a way to do this without causing a query for each line?
    for line in inquiry.lines.all():
        _update_counter(
            SduRecord, 'num_purchases',
            {'sdu': line.sdu}, line.quantity)


def _record_user_inquiry(user, inquiry):
    try:
        record = UserRecord.objects.filter(user=user)
        affected = record.update(
            num_inquiries=F('num_inquiries') + 1,
            num_inquiry_lines=F('num_inquiry_lines') + inquiry.num_lines,
            num_inquiry_items=F('num_inquiry_items') + inquiry.num_items,
            total_spent=F('total_spent') + inquiry.total_incl_tax,
            date_last_inquiry=inquiry.date_placed)
        if not affected:
            UserRecord.objects.create(
                user=user, num_inquiries=1, num_inquiry_lines=inquiry.num_lines,
                num_inquiry_items=inquiry.num_items,
                total_spent=inquiry.total_incl_tax,
                date_last_inquiry=inquiry.date_placed)
    except IntegrityError:      # pragma: no cover
        logger.error(
            "IntegrityError in analytics when recording a user inquiry.")


# Receivers

@receiver(sdu_viewed)
def receive_sdu_view(sender, sdu, user, **kwargs):
    if kwargs.get('raw', False):
        return
    _update_counter(SduRecord, 'num_views', {'sdu': sdu})
    if user and user.is_authenticated:
        _update_counter(UserRecord, 'num_sdu_views', {'user': user})
        UserSduView.objects.create(sdu=sdu, user=user)


@receiver(user_search)
def receive_sdu_search(sender, query, user, **kwargs):
    if user and user.is_authenticated and not kwargs.get('raw', False):
        UserSearch._default_manager.create(user=user, query=query)


@receiver(basket_addition)
def receive_basket_addition(sender, sdu, user, **kwargs):
    if kwargs.get('raw', False):
        return
    _update_counter(
        SduRecord, 'num_basket_additions', {'sdu': sdu})
    if user and user.is_authenticated:
        _update_counter(UserRecord, 'num_basket_additions', {'user': user})


@receiver(inquiry_placed)
def receive_inquiry_placed(sender, inquiry, user, **kwargs):
    if kwargs.get('raw', False):
        return
    _record_sdus_in_inquiry(inquiry)
    if user and user.is_authenticated:
        _record_user_inquiry(user, inquiry)
