from urllib.parse import urlencode
from django import template
import logging

logger = logging.getLogger(__name__)

register = template.Library()
