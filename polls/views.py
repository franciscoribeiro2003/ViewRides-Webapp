from django.shortcuts import render, get_object_or_404
from django.http import FileResponse, HttpResponse
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
def display_gpx_data(request):
    gpx_data_entries = GPXData.objects.all()
    return render(request, 'display_gpx.html', {'gpx_data_entries': gpx_data_entries})

def serve_gpx_file(request, id):
    gpx_data = get_object_or_404(GPXData, id=id)
    gpx_file = gpx_data.gpx_file
    return FileResponse(gpx_file, as_attachment=True)

def display_gpx_data_detail(request, id):
    gpx_data = get_object_or_404(GPXData, id=id)
    return render(request, 'gpx_data_detail.html', {'gpx_data': gpx_data})