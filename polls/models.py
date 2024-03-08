from django.db import models

class GPXData(models.Model):
    id = models.AutoField(primary_key=True)
    gpx_file = models.FileField(upload_to='gpx_files/')

    def __str__(self):
        return self.gpx_file.name
    