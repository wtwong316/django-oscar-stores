from decimal import Decimal as D

from django.core.exceptions import ObjectDoesNotExist


class Scale(object):
    """
    For calculating the weight of a sdu or basket
    """
    def __init__(self, attribute_code='weight', default_weight=None):
        self.attribute = attribute_code
        self.default_weight = default_weight

    def weigh_sdu(self, sdu):
        weight = None
        try:
            weight = sdu.get_attribute_values().get(
                attribute__code=self.attribute).value
        except ObjectDoesNotExist:
            pass

        if weight is None:
            if self.default_weight is None:
                raise ValueError(
                    "No attribute %s found for sdu %s" % (
                        self.attribute, sdu))
            weight = self.default_weight

        return D(weight) if weight is not None else D('0.0')

    def weigh_basket(self, basket):
        weight = D('0.0')
        for line in basket.lines.all():
            weight += self.weigh_sdu(line.sdu) * line.quantity
        return weight
