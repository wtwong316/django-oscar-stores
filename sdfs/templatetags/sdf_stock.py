from django import template
from django.contrib.gis.db.models.functions import Distance
from oscar.core.loading import get_model

SdfStock = get_model('sdfs', 'SdfStock')

register = template.Library()


@register.simple_tag
def sdf_stock_for_sdu(sdu, location=None, limit=20):
    query_set = SdfStock.objects.filter(sdu=sdu)
    if location:
        query_set = query_set.annotate(
            distance=Distance('sdf__location', location)
        ).order_by('distance')
    else:
        query_set = query_set.order_by('sdf__name')
    return query_set[0:limit]
