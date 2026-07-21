from urllib.parse import urlencode
from django import template
from datetime import datetime, timedelta
from plotly import graph_objs as go
import json
from itertools import combinations
from plotly.subplots import make_subplots
from plotly import offline
from across.client import Client

import logging

logger = logging.getLogger(__name__)

register = template.Library()
