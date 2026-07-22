from urllib.parse import urlencode

from django import template
from django.conf import settings

register = template.Library()

DEFAULT_ACROSS_APP_URL = 'https://app.across.sciencecloud.nasa.gov'

@register.simple_tag
def across_app_visibility_url(target, hi_res=True):
    base = getattr(settings, 'ACROSS_APP_URL', DEFAULT_ACROSS_APP_URL)
    query = urlencode({
        'ra': f'{target.ra:f}',
        'dec': f'{target.dec:f}',
        'hi_res': str(hi_res).lower(),
    })
    return f'{base}/visibility-calculator?{query}'
