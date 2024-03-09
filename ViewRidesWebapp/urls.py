from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('map/', include('maps.urls')),
    path('admin/', admin.site.urls),
    
]
