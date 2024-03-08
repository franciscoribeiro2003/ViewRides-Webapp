from django.shortcuts import render
from django.http import HttpResponse
import os
from django.conf import settings

from polls.models import GPXData
from .forms import GPXUploadForm

def index (request):
    return render(request, 'index.html')

def rota (request):
    file_path = os.path.join(settings.BASE_DIR, 'polls/static/gpx/rota.gpx')
    with open(file_path, 'r') as f:
        file = f.read()
    return HttpResponse(file, content_type='text/xml')

def upload_gpx(request):
    if request.method == 'POST':
        form = GPXUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponse('File uploaded successfully')
    else:
        form = GPXUploadForm()
    return render(request, 'upload_gpx.html', {'form': form})

# display all the data from the database
def display_gpx(request):
    data = GPXData.objects.all()
    return render(request, 'display_gpx.html', {'data': data})