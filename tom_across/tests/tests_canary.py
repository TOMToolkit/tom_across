from django.test import tag, TestCase
from across.client import Client


@tag('canary')
class TestAPPCanary(TestCase):
    """NOTE: To run these tests in your venv: python ./{{tom_app}}/tests/run_tests.py"""

    def test_canary(self):
        """
        Testing the ACROSS client can be instantiated and make a simple call.
        """
        client = Client()   # class under test
        instrument_id = 'd21c66bc-7173-454e-8f67-69df1b43590d'
        instrument = client.instrument.get(instrument_id)
        self.assertEqual(instrument.id, instrument_id)
