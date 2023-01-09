from django import template
from django.template.loader import select_template

register = template.Library()


@register.simple_tag(takes_context=True)
def render_sdu(context, sdu):
    """
    Render a sdu snippet as you would see in a browsing display.

    This templatetag looks for different templates depending on the UPC and
    sdu class of the passed sdu.  This allows alternative templates to
    be used for different sdu classes.
    """
    if not sdu:
        # Search index is returning sdus that don't exist in the
        # database...
        return ''

    names = ['oscar/catalogue/partials/sdu/upc-%s.html' % sdu.upc,
             'oscar/catalogue/partials/sdu/class-%s.html'
             % sdu.get_sdu_class().slug,
             'oscar/catalogue/partials/sdu.html']
    template_ = select_template(names)
    context = context.flatten()

    # Ensure the passed sdu is in the context as 'sdu'
    context['sdu'] = sdu
    return template_.render(context)
