from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    # path to rota.gpx returning that file
    path("rota", views.rota, name="rota"),
    path("upload_gpx", views.upload_gpx, name="upload_gpx"),
    path('gpx_data/', views.display_gpx_data, name='display_gpx_data'),
    path('gpx_data/<int:id>/file/', views.serve_gpx_file, name='serve_gpx_file'),
    path('gpx_data/<int:id>/', views.display_gpx_data_detail, name='display_gpx_data_detail'),
]