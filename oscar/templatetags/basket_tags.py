from django import template
from django.contrib.sessions.serializers import JSONSerializer

from oscar.core.loading import get_class, get_model

AddToBasketForm = get_class('basket.forms', 'AddToBasketForm')
SimpleAddToBasketForm = get_class('basket.forms', 'SimpleAddToBasketForm')
Sdu = get_model('catalogue', 'sdu')

register = template.Library()

QNT_SINGLE, QNT_MULTIPLE = 'single', 'multiple'


@register.simple_tag
def basket_form(request, sdu, quantity_type='single'):
    if not isinstance(sdu, Sdu):
        return ''

    initial = {}
    if not sdu.is_parent:
        initial['sdu_id'] = sdu.id

    form_class = AddToBasketForm
    if quantity_type == QNT_SINGLE:
        form_class = SimpleAddToBasketForm

    basket_post_data = request.session.pop("add_to_basket_form_post_data_%s" % sdu.pk, None)

    if basket_post_data is not None:
        basket_post_data = JSONSerializer().loads(basket_post_data.encode("latin-1"))

    form = form_class(request.basket, data=basket_post_data, sdu=sdu, initial=initial)

    return form
