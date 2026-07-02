from django.shortcuts import render
from django.views.generic import TemplateView
from django_tables2 import RequestConfig

from across.client import Client

from tom_targets.models import Target

from tom_across.utils import observation_rows
from tom_across.tables import ObservationTable
import logging

logger = logging.getLogger(__name__)


class AcrossDashboardView(TemplateView):
    template_name = "tom_across/dashboard.html"


def observation_table_view(request, target_id):
    client = Client()
    target = Target.objects.get(id=target_id)

    data = observation_rows(client, target)
    table = ObservationTable(data)

    table.htmx_url = request.path

    RequestConfig(request, paginate={"per_page": 10}).configure(table)

    return render(request, "tom_across/partials/observation_table_partial.html", {
        "table": table,
        "target": target,
    })