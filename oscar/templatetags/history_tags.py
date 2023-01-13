from urllib import parse

from django import template
from django.urls import Resolver404, resolve
from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_class, get_model

Site = get_model('sites', 'Site')
RenterHistoryManager = get_class('renter.history', 'RenterHistoryManager')

register = template.Library()


@register.inclusion_tag('oscar/renter/history/recently_viewed_sdus.html',
                        takes_context=True)
def recently_viewed_sdus(context, current_sdu=None):
    """
    Inclusion tag listing the most recently viewed sdus
    """
    request = context['request']
    sdus = RenterHistoryManager.get(request)
    if current_sdu:
        sdus = [p for p in sdus if p != current_sdu]
    return {'sdus': sdus,
            'request': request}


@register.simple_tag(takes_context=True)
def get_back_button(context):   # noqa (too complex (11))
    """
    Show back button, custom title available for different urls, for
    example 'Back to search results', no back button if user came from other
    site
    """
    request = context.get('request', None)
    if not request:
        raise Exception('Cannot get request from context')

    referrer = request.META.get('HTTP_REFERER', None)
    if not referrer:
        return None

    try:
        url = parse.urlparse(referrer)
    except (ValueError, TypeError):
        return None

    if request.get_host() != url.netloc:
        try:
            Site.objects.get(domain=url.netloc)
        except Site.DoesNotExist:
            # Came from somewhere else, don't show back button:
            return None

    try:
        match = resolve(url.path)
    except Resolver404:
        return None

    # This dict can be extended to link back to other browsing pages
    titles = {
        'search:search': _('Back to search results'),
    }
    title = titles.get(match.view_name, None)

    if title is None:
        return None

    return {'url': referrer, 'title': str(title), 'match': match}
