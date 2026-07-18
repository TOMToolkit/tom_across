from django import forms
import logging

logger = logging.getLogger(__name__)

class ObservationFilterForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    wavelength_type = forms.ChoiceField(
        required=False,
        choices=[('angstrom', 'angstrom'), ('nm', 'nm'), ('keV', 'keV')]
    )
    wavelength_min = forms.FloatField(required=False)
    wavelength_max = forms.FloatField(required=False)
    observation_type = forms.ChoiceField(
        required=False,
        choices=[('', 'Any'), ('imaging', 'Imaging'), ('spectroscopy', 'Spectroscopy')]
    )
    def clean(self):
        cleaned_data = super().clean()

        wavelength_type = cleaned_data.get("wavelength_type")
        wavelength_min = cleaned_data.get("wavelength_min")
        wavelength_max = cleaned_data.get("wavelength_max")

        if wavelength_type:
            if wavelength_min is None:
                cleaned_data["wavelength_min"] = 1
            if wavelength_max is None:
                cleaned_data["wavelength_max"] = 1000000

        return cleaned_data


class VisibilityPlotForm(forms.Form):
    observatories = forms.MultipleChoiceField(required=True)
    begin = forms.DateTimeField(required=True)
    end = forms.DateTimeField(required=True)

    def __init__(self, *args, observatory_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['observatories'].choices = observatory_choices or []
