from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    # path to rota.gpx returning that file
    path("rota", views.rota, name="rota"),
    path("upload_gpx", views.upload_gpx, name="upload_gpx"),
    path ("display_gpx", views.display_gpx, name="display_gpx")

]