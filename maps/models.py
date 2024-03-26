from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager
from django.contrib.auth.models import User

from ViewRidesWebapp import settings

class CustomUser(AbstractUser):
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        related_name='custom_user_set',  # Specify custom related_name
        related_query_name='custom_user',
    )
    # Define custom manager
    objects = UserManager()

    def __str__(self):
        return self.username

# Update the GPXData model with custom related_query_name attributes
class GPXData(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='gpx_data_set', related_query_name='gpx_data')  # Specify related_name and related_query_name
    gpx_file = models.FileField(upload_to='gpx_files/')

    def __str__(self):
        return f'{self.gpx_file.name}--{self.user.username}'

class PointOfInterest(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        managed = True