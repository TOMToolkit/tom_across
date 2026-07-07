from django.shortcuts import render
from django.views.generic import TemplateView
from django_tables2 import RequestConfig
from django.views.generic.list import ListView
from tom_common.htmx_table import HTMXTableViewMixin
from django_tables2 import SingleTableView
from django.urls import reverse

from across.client import Client

from tom_targets.models import Target

from tom_across.utils import observation_rows
from tom_across.tables import ObservationTable
import logging

logger = logging.getLogger(__name__)

class DemoView(TemplateView):
    """
    Generic demo view
    """
    template_name = "tom_across/demo_page.html"

class ObservationTableView(HTMXTableViewMixin, ListView):
    table_class = ObservationTable
    template_name = "tom_across/observation_table.html"
    paginate_by = 10
    model = None

    def get_queryset(self):
        client = Client()
        target = Target.objects.get(id=self.kwargs["target_id"])
        return observation_rows(client, target)

    def get_context_data(self, **kwargs):
        context = super(HTMXTableViewMixin, self).get_context_data(**kwargs)
        context['record_count'] = context['paginator'].count
        context['empty_database'] = not context['object_list']
        context["target"] = Target.objects.get(id=self.kwargs["target_id"])
        return context