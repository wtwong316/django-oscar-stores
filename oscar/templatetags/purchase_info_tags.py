from django import template

register = template.Library()


@register.simple_tag
def purchase_info_for_sdu(request, sdu):
    if sdu.is_parent:
        return request.strategy.fetch_for_parent(sdu)

    return request.strategy.fetch_for_sdu(sdu)


@register.simple_tag
def purchase_info_for_line(request, line):
    return request.strategy.fetch_for_line(line)
