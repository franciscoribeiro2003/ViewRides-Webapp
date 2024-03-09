from telnetlib import LOGOUT
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import get_user_model
from django.http import FileResponse, HttpResponse
from .models import GPXData
from .forms import GPXUploadForm, RegistrationForm
from django.core.exceptions import PermissionDenied


def index(request):
    return render(request, 'index.html')

def upload_gpx(request):
    if not request.user.is_authenticated:
        raise PermissionDenied 
    CustomUser = get_user_model()  # Get the custom user model
    if request.method == 'POST':
        form = GPXUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Assign the logged-in user to the GPXData instance
            gpx_data = form.save(commit=False)
            if isinstance(request.user, CustomUser):  # Check if request.user is a CustomUser instance
                gpx_data.user = request.user
                gpx_data.save()
                return HttpResponse('File uploaded successfully')
            else:
                return HttpResponse('Invalid user type')  # Handle the case where request.user is not a CustomUser
    else:
        form = GPXUploadForm()
    return render(request, 'upload_gpx.html', {'form': form})

def display_gpx_data(request):
    if request.user.is_authenticated:
        # Filter GPX data entries by the logged-in user
        gpx_data_entries = GPXData.objects.filter(user=request.user)
        return render(request, 'display_gpx.html', {'gpx_data_entries': gpx_data_entries})
    else:
        raise PermissionDenied

def serve_gpx_file(request, id):
    gpx_data = get_object_or_404(GPXData, id=id)
    # Check if the requested GPX data belongs to the logged-in user
    if request.user == gpx_data.user:
        gpx_file = gpx_data.gpx_file
        return FileResponse(gpx_file, as_attachment=True)
    else:
        return HttpResponse('Unauthorized', status=403)

def display_gpx_data_detail(request, id):
    # Get the GPX data associated with the logged-in user
    gpx_data = get_object_or_404(GPXData, id=id, user=request.user)
    return render(request, 'gpx_data_detail.html', {'gpx_data': gpx_data})

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def logout_view(request):
    LOGOUT(request)
    return redirect('index')