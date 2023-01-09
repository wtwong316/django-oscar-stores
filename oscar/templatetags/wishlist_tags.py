from django import template

register = template.Library()


@register.simple_tag
def wishlists_containing_sdu(wishlists, sdu):
    return wishlists.filter(lines__sdu=sdu)
