from unittest.mock import patch

from django.template.loader import render_to_string
from django.test import TestCase

from tom_targets.models import Target

from tom_across.utils import observation_rows


class TestNonSiderealTargets(TestCase):
    """
    TOM ACROSS only supports sidereal targets; check non-sidereal targets are handled gracefully.
    """
    def setUp(self):
        self.non_sidereal = Target.objects.create(name='test non-sidereal', type=Target.NON_SIDEREAL, epoch=57000)

    @patch('tom_across.utils.client')
    def test_observation_rows_skips_across_query(self, mock_client):
        """
        A non-sidereal target has no RA/Dec to cone search on, so ACROSS should not be queried at all.
        """
        self.assertEqual(observation_rows(self.non_sidereal), [])
        mock_client.observation.get_many.assert_not_called()

    def test_target_template_shows_message(self):
        """
        The target page should explain why there is nothing to show instead of loading empty panels.
        """
        html = render_to_string('tom_across/target_across.html', {'target': self.non_sidereal})
        self.assertIn('TOM ACROSS is only configured for Sidereal targets', html)
        self.assertNotIn('View in ACROSS', html)
