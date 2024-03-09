from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("upload_gpx", views.upload_gpx, name="upload_gpx"),
    path('gpx_data/', views.display_gpx_data, name='display_gpx_data'),
    path('gpx_data/<int:id>/file/', views.serve_gpx_file, name='serve_gpx_file'),
    path('gpx_data/<int:id>/', views.display_gpx_data_detail, name='display_gpx_data_detail'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
]