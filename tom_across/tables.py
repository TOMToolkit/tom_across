import django_tables2 as tables
from tom_common.htmx_table import HTMXTable
from django.urls import reverse
from django.utils.html import format_html
import logging

from tom_across.utils import get_across_instrument_ids, get_across_observatory_telescope_name_map

from across.tools.archive_resolver import HEASARCArchiveResolver, MASTArchiveResolver

logger = logging.getLogger(__name__)
class ObservationTable(HTMXTable):
    telescope = tables.Column()
    instrument = tables.Column()
    exptime = tables.Column()
    date = tables.DateTimeColumn(format="Y-m-d H:i")
    type = tables.Column()
    filter_name = tables.Column()
    wavelength_range = tables.Column()
    status = tables.Column()
    external_observation_id = tables.Column()

    selection = None

    class Meta(HTMXTable.Meta):
        model = None
        empty_text = "No observations found"
        attrs = {
            **HTMXTable.Meta.attrs,
            "hx-target": "#observation-table-wrapper",
            "hx-swap": "outerHTML",
        }
    
    partial_template_name = 'tom_across/partials/observation_table_partial.html'

    def get_table_action_url(self):
        target_id = self.request.resolver_match.kwargs.get("target_id")
        return reverse("across:observation-table", kwargs={"target_id": target_id})

    def render_exptime(self, value):
        try:
            return f"{float(value):.1f}"
        except (ValueError, TypeError):
            return value

    def render_wavelength_range(self, value):
            try:
                rendered_min = f"{float(value[0]):.0f}" if float(value[0]) > 1 else f"{float(value[0]):.2e}"
                rendered_max = f"{float(value[1]):.0f}" if float(value[1]) > 1 else f"{float(value[1]):.2e}"
                return f"{rendered_min} - {rendered_max}"
            except (ValueError, TypeError):
                return value
            
    def render_external_observation_id(self, value):
        """
        Render the external observation ID as a hyperlink to the corresponding archive page.

        Args:
            value (tuple): A tuple containing the instrument ID and the external observation ID.
        
        Returns:
            str: The external observation ID, as an href link to the corresponding archive page if resolvable,
            or just the ID if not.
        """
        if not value:
            return ""
        try:
            inst_id_dict = get_across_instrument_ids()
            inst_tele_name = inst_id_dict[value[0]][1]

            obs_tele_name_dict = get_across_observatory_telescope_name_map()
            name_to_try = None
            for obs_name, tele_names in obs_tele_name_dict.items():
                if inst_tele_name in tele_names:
                    name_to_try = obs_name
                    break

            if not name_to_try:
                return value[1]

            if name_to_try in ["HST", "JWST"]:
                resolver = MASTArchiveResolver(
                    external_observation_id=value[1].split(":")[0],
                    mission=name_to_try
                )

            elif name_to_try in [
                "Chandra", "IXPE", "NICER", "NuSTAR", "XMM-Newton", "Swift", "XRISM"
            ]:
                name_table_dict = {
                    "Chandra": "chanmastr",
                    "IXPE": "ixmaster",
                    "NICER": "nicermastr",
                    "NuSTAR": "numaster",
                    "Swift": "swiftmastr",
                    "XMM-Newton": "xmmmaster",
                    "XRISM": "xrismmastr",
                }
                resolver = HEASARCArchiveResolver(
                    external_observation_id=value[1],
                    heasarc_table=name_table_dict[name_to_try]
                )
            else:
                return value[1]

            resolver.construct_archive_url()
            if resolver.archive_url:
                return format_html(
                    f'<a href="{resolver.archive_url}" target="_blank">{value[1]}</a>'
                )
            else:
                logger.warning(f"Could not resolve archive URL for observation ID: {value}")
                return value[1]
        except Exception as e:
            logger.error(f"Error resolving archive URL for observation ID {value}: {e}")
            return value[1]
