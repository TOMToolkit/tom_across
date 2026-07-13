from django import forms

class ObservationFilterForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    wavelength_min = forms.FloatField(required=False)
    wavelength_max = forms.FloatField(required=False)
    observation_type = forms.ChoiceField(
        required=False,
        choices=[('', 'Any'), ('imaging', 'Imaging'), ('timing', 'Timing'),
                ('spectroscopy', 'Spectroscopy'), ('slew', 'Slew')]
    )