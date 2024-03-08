# polls/forms.py
from django import forms
from .models import GPXData

class GPXUploadForm(forms.ModelForm):
    class Meta:
        model = GPXData
        fields = ['gpx_file']