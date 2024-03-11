from django.urls import reverse
from datetime import datetime
from telnetlib import LOGOUT
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import get_user_model
from django.http import FileResponse, HttpResponse
import gpxpy
import requests
from stravalib import Client

from ViewRidesWebapp import settings
from .models import GPXData
from .forms import GPXUploadForm, RegistrationForm
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
import polyline
from datetime import timezone
from stravalib.exc import ObjectNotFound


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



def import_strava_rides(request):
    strava_auth_url = "https://www.strava.com/oauth/authorize?" + \
                      f"client_id=122950&" + \
                      "response_type=code&" + \
                      f"redirect_uri={request.build_absolute_uri(reverse('strava_callback'))}&" + \
                      "approval_prompt=auto&" + \
                      "scope=read,activity:read_all"

    return redirect(strava_auth_url)

def strava_callback(request):
    if 'code' in request.GET:
        code = request.GET['code']
        
        # Exchange authorization code for access token
        token_response = requests.post(
            'https://www.strava.com/oauth/token',
            data={
                'client_id': '122950',  
                'client_secret': 'dcb1096b5f4aa7747121a8865d0ca5bf615cea2d',  
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': request.build_absolute_uri(reverse('strava_callback'))  # Ensure the redirect URI matches
            }
        )
        #print ("--------"+'\n'+token_response.json())
        if token_response.status_code == 200:
            print(token_response.json())
            access_token = token_response.json().get('access_token')

            page = 1
            per_page = 200
            strava_activities = []
            
            while True:
                strava_activities_response = requests.get(
                    'https://www.strava.com/api/v3/athlete/activities',
                    headers={'Authorization': f'Bearer {access_token}'},
                    params={'page': page, 'per_page': per_page}
                )
            
                if strava_activities_response.status_code == 200:
                    new_activities = strava_activities_response.json()
                    if not new_activities:  # If no more activities, break the loop
                        break

                    strava_activities.extend(new_activities)
                    page += 1
                else:
                    return HttpResponse("Failed to fetch activities from Strava")
                
            for activity in strava_activities:
                # Convert activity to GPX and save to database
                gpx1 = generate_gpx(activity, access_token)
                
                if gpx1 is None:
                    continue
                
                gpx_file = ContentFile(gpx1.encode('utf-8'))

                # Create a unique filename for the GPX file
                gpx_filename = f"{activity['id']}_{activity.get('name', '')}_{request.user.username}.gpx"

                # Save the GPX data to the database
                gpx_data = GPXData(user=request.user)
                gpx_data.gpx_file.save(gpx_filename, gpx_file)
                gpx_data.save()

                    
                    
            return HttpResponse("Activities imported successfully!")
        else:
            return HttpResponse("Failed to fetch activities from Strava")
    else:
        return HttpResponse("Failed to obtain access token from Strava")
    

def generate_gpx(activity, access_token):
    client = Client(access_token=access_token)
    types = ['time', 'latlng', 'altitude']
    try:
        streams = client.get_activity_streams(activity['id'], types=types, resolution='high')
    except ObjectNotFound:
        print(f"Stream data not found for activity {activity['id']}")
        return None
    
    if 'latlng' not in streams:
        print(f"No latlng data for activity {activity['id']}")
        return None
    
    # Generate GPX content from activity
    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack()

    # Set metadata
    gpx.name = activity.get('name', '')  # Set the name of the activity
    gpx.description = activity.get('description', '')  # Set the description of the activity
    gpx.author_name = activity['athlete'].get('name', '')  # Set the name of the author
    gpx.time = datetime.strptime(activity['start_date'], '%Y-%m-%dT%H:%M:%SZ')  # Set the time of the activity

    # Add track segment
    start_date_local = datetime.strptime(activity['start_date_local'], '%Y-%m-%dT%H:%M:%SZ')
    gpx_segment = gpxpy.gpx.GPXTrackSegment()

    # Add all points to the track segment
    for time, latlng, altitude in zip(streams['time'].data, streams['latlng'].data, streams['altitude'].data):
        track_point = gpxpy.gpx.GPXTrackPoint(
            latitude=latlng[0],
            longitude=latlng[1],
            elevation=altitude,
            time=datetime.fromtimestamp(time + int(start_date_local.timestamp()), tz=timezone.utc),
        )
        gpx_segment.points.append(track_point)

    gpx_track.segments.append(gpx_segment)
    gpx.tracks.append(gpx_track)

    return gpx.to_xml()