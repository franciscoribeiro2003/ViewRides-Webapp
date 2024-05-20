from django.db import connections
from django.urls import reverse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import get_user_model
from django.http import FileResponse, HttpResponse, JsonResponse
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.views.decorators.http import require_POST

from datetime import datetime
from datetime import timezone
import gpxpy
import requests
from stravalib import Client
from stravalib.exc import ObjectNotFound
from telnetlib import LOGOUT
import os

from ViewRidesWebapp import settings
from .models import GPXData, PointOfInterest
from .forms import GPXUploadForm, PointOfInterestForm, RegistrationForm


# INDEX #################################
def index(request):
    gpx_data_entries = []
    if request.user.is_authenticated:
        # Filter GPX data entries by the logged-in user
        gpx_data_entries = GPXData.objects.filter(user=request.user)
    print(len(gpx_data_entries))
    context = {'gpx_data_entries': gpx_data_entries}
    return render(request, 'index.html', context)

# UPLOAD #################################
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

# DISPLAY #################################
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

# REGISTER #################################
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


# STRAVA #################################
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
    
    for _ in range(5):  # Retry up to 5 times
        try:
            streams = client.get_activity_streams(activity['id'], types=types, resolution='high')
            break  # If the request is successful, break the loop
        except (ObjectNotFound, ConnectionError) as e:
            print(f"Error fetching stream data for activity {activity['id']}: {e}")
            time.sleep(5)  # Wait for 5 seconds before retrying
    else:
        return None  # If all retries fail, return None

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

# Points of Interest #################################



def map_view(request):
    return render(request, 'add_point.html')

def poi_list(request):
    pois = PointOfInterest.objects.using('postgis').all().values('id', 'name', 'latitude', 'longitude')
    return JsonResponse(list(pois), safe=False)

@require_POST
def add_poi(request):
    form = PointOfInterestForm(request.POST)
    if form.is_valid():
        print('addPOI valid');
        poi = form.save(commit=False)
        
        # Specify the database alias to use
        with connections['postgis'].cursor() as cursor:
            cursor.execute("SET search_path TO public")
            poi.save(using='postgis')
        
        # Return details of the newly added point in the response
        poi_data = {
            'name': poi.name,
            'latitude': poi.latitude,
            'longitude': poi.longitude,
            'layer': poi.layer
        }
        print (poi_data)
        return JsonResponse({'success': True, 'poi': poi_data})
    else:
        print('addPOI invalid');
        errors = form.errors.as_json()
        return JsonResponse({'success': False, 'errors': errors})
    


def get_layers_list(request):
    # Authentication credentials
    username = settings.GEOSERVER_USERNAME
    password = settings.GEOSERVER_PASSWORD
    
    # Get the search term from the query parameters
    search_term = request.GET.get('term', '')

    # Fetch all layer names from GeoServer REST API
    url = "{}/layers.json?list=available&detail=layerGroup&filter=enabled".format(settings.GEOSERVER_BASE_URL)
    response = requests.get(url, auth=(username, password))
    data = response.json()

    # Filter layer names based on the search term
    all_layers = [layer['name'] for layer in data['layers']['layer']]
    filtered_layers = [layer for layer in all_layers if search_term.lower() in layer.lower()]

    if search_term:
        return JsonResponse({'layers': filtered_layers[:5]})

    return JsonResponse({'layers': filtered_layers})


#subscribe to be recording an gpx file in real time, like access location and clock and then record, subscribe to like a socket or something
def recordeGPX(request):
    recordedGPX = []
    #recording the gpx file
    timezone.now()
    # current location
    currentLocation = []
    try:
        request.POST['location']
    except:
        print("no location")
    else:
        currentLocation = request.POST['location']
        print(currentLocation)
    # current time
    currentTime = []
    try:
        request.POST['time']
    except:
        print("no time")
    else:
        currentTime = request.POST['time']
        print(currentTime)

    recordedGPX.append(currentLocation)
    recordedGPX.append(currentTime)
    return JsonResponse({'recordedGPX': recordedGPX})


